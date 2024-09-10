from collections import defaultdict
from dataclasses import InitVar, dataclass, field
from math import gcd

from lxml.etree import _Element, _ElementTree
from multidict import MultiDict

from .helpers import read_specs, str_int


def max_divider(num, terms):
    """НОД для списка чисел"""
    for term_id in terms:
        num = gcd(num, int(term_id))
    return num


class CodeIterable:
    def iter(self, codes=None, specs=None):
        """Получения итератора по элементам"""
        if codes is None:
            return self._iter_all()
        elif specs is None:
            return self._iter_codes(codes)
        else:
            return self._iter_codes(codes, specs)


@dataclass
class Column:
    code: str
    value: str = None

    def __float__(self):
        return float(self.value or "nan")


@dataclass
class Row(CodeIterable):
    code: str
    specs: dict[str, str] = field(default_factory=dict)
    columns: dict[str, Column] = field(default_factory=dict)

    def add(self, column):
        """Добавление колонки в строку"""
        self.columns[column.code] = column

    # ---

    def _iter_all(self):
        """Возвращает view-объект по всем колонкам"""
        return self.columns.values()

    def _iter_codes(self, codes):
        """Возвращает итератор по колонкам c указанными кодами"""
        for code in codes:
            yield self.get_column(code)

    def get_column(self, code):
        """Возвращает колонку"""
        return self.columns.get(code, Column(code=code))

    # ---

    def match(self, specs):
        """Проверка, входит ли строка в список переданных специфик"""
        for key, spec in specs:
            if spec and self.get_spec(key) not in spec:
                return False
        return True

    def get_spec(self, key, default=None):
        """Возвращает указанную специфику строки"""
        return self.specs.get(key) or default


@dataclass
class Section(CodeIterable):
    code: str
    rows: MultiDict[str, Row] = field(default_factory=MultiDict)
    rows_counter: defaultdict = field(default_factory=lambda: defaultdict(int))

    def add(self, row):
        """Добавление строки в раздел и приращение счётчика"""
        self.rows.add(row.code, row)
        self.rows_counter[(row.code, *row.specs.values())] += 1

    # ---

    def _iter_all(self):
        """Возвращает view-объект по всем строкам"""
        return self.rows.values()

    def _iter_codes(self, codes, specs=None):
        """Возвращает итератор по строкам c указанными кодами"""
        for code in codes:
            yield from (row for row in self.get_rows(code) if row.match(specs))

    def get_rows(self, code):
        '''Возвращает список строк с указанным кодом"'''
        return self.rows.getall(code, [Row(code=code)])


@dataclass
class Report(CodeIterable):
    xml: InitVar[_Element | _ElementTree]

    year: str = None

    title: dict[str, str] = None
    sections: dict[str, Section] = None

    period: str = None
    period_type: str = field(default=None, repr=False)
    period_code: str = field(default=None, repr=False)

    def __post_init__(self, xml):
        self.title = dict(self._read_title(xml))
        self.sections = dict(self._read_data(xml))

        self._get_periods(xml)
        self._get_year(xml)

    @property
    def blank(self):
        return len(self.sections) == 0

    # ---

    def _iter_all(self):
        """Возвращает view-объект по всем разделам"""
        return self.sections.values()

    def _iter_codes(self, codes):
        """Возвращает итератор по разделам c указанными кодами"""
        for code in codes:
            yield self.get_section(code)

    def get_section(self, code):
        """Возвращает раздел с указанным кодом"""
        return self.sections.get(code)

    # ---

    def _read_title(self, xml):
        """Чтение заголовков отчёта"""
        for item in xml.iterfind("title/item"):
            yield item.get("name"), item.get("value", "").strip()

    # ---

    def _read_data(self, xml):
        """Чтение тела отчёта (разделы/строки/колонки)"""
        for sec_xml in xml.iterfind("sections/section"):
            sec_code = str_int(sec_xml.get("code"))

            section = Section(code=sec_code)

            for row_xml in sec_xml.iterfind("row"):
                row_code = str_int(row_xml.get("code"))
                row_specs = read_specs(row_xml)

                row = Row(code=row_code, specs=row_specs)

                for col_xml in row_xml.iterfind("col"):
                    col_code = col_xml.get("code")

                    column = Column(code=col_code, value=col_xml.text)

                    row.add(column)
                section.add(row)

            yield section.code, section

    # ---

    def _get_year(self, xml):
        """Получение года из корня отчёта"""
        self.year = xml.xpath("string(@year)")

    def _get_periods(self, xml):
        """Получение и разбиение периода из корня отчёта"""
        self.period = xml.xpath("string(@period)")

        if len(self.period) == 4:
            self.period_type = str_int(self.period[:2])
            self.period_code = str_int(self.period[2:])

    # ---

    def set_periods(self, catalogs, idp):
        """
        Попытка привести тип и код периода к формату описанному в спецификации
        """
        try:
            period_ids = self._get_period_ids(catalogs)

            if int(self.period) not in period_ids:
                return False

            max_code = max(period_ids)

            if max_code <= int(idp):
                self.period_type = idp
                self.period_code = self.period
                return True

            max_div = max_divider(max_code, period_ids)

            if max_code <= int(idp) * max_div:
                self.period_type = idp
                self.period_code = str(int(int(self.period) / max_div))
                return True
            return False
        except Exception:
            return False

    def _get_period_ids(self, catalogs):
        """Получение идентификаторов допустимых периодов из справочника"""
        try:
            return set(map(int, catalogs["s_time"]["ids"]))
        except KeyError:
            return set(map(int, catalogs["s_mes"]["ids"]))
