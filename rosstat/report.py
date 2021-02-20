from math import gcd
from typing import List, Dict, Tuple, Optional
from collections import defaultdict as defdict
from dataclasses import dataclass, InitVar, field as f
from lxml.etree import _ElementTree
from .schema import str_int


def max_divider(num, terms):
    '''НОД для списка чисел'''
    for term_id in terms:
        num = gcd(num, int(term_id))
    return num


@dataclass
class Row:
    code: str
    s1: str
    s2: str
    s3: str
    cols: Dict[str, str] = f(default_factory=dict)
    _blank: bool = True

    @property
    def blank(self):
        '''Флаг указывающий, что строка пустая'''
        return self._blank

    def items(self, codes=None):
        '''Итерация по элементам строки'''
        codes = codes or self.cols.keys()
        for col_code in codes:
            yield col_code, self.get_col(col_code)

    def get_col(self, code):
        '''Возвращает указанную колонку'''
        return self.cols.get(code)

    def add_col(self, col_code, col_text):
        '''Добавление колонки в строку'''
        self.cols[col_code] = col_text
        self._blank = False

    def get_spec(self, idx):
        '''Возвращает специфику по её "индексу"'''
        return getattr(self, f's{idx}')


@dataclass
class Section:
    code: str
    rows: List[Row] = f(default_factory=list)
    row_codes: List[str] = f(default_factory=list)

    _ignore_specs: Tuple[set] = f(default=({None}, {'*'}, {'0'}), repr=False)
    _ignore_report_specs: Tuple[str] = f(default=('XX',), repr=False)

    def items(self, codes=None, specs=None):
        '''Итерация по элементам раздела'''
        codes = codes or sorted(set(self.row_codes), key=int)
        for row_code in codes:
            yield row_code, list(self.get_rows(row_code, specs=specs))

    def get_rows(self, code, specs=None):
        '''Возвращает строки с указанным кодом и спецификами'''
        for row_code, row in zip(self.row_codes, self.rows):
            if row_code == code and self._check_specs(row, specs):
                yield row

    def _check_specs(self, row, specs):
        '''Проверка, входит ли строка в список переданных специфик'''
        if specs is None:
            return True
        for i in range(1, 4):
            row_spec = getattr(row, f's{i}')
            if row_spec in self._ignore_report_specs:
                return True
            if specs[i] not in self._ignore_specs and row_spec not in specs[i]:
                return False
        return True

    def add_row(self, row_code, row):
        '''Добавление строки в раздел'''
        self.row_codes.append(row_code)
        self.rows.append(row)


@dataclass
class Report:
    xml: InitVar[_ElementTree]
    _blank: bool = True
    _year: str = None
    _title: Dict[str, str] = None
    _data: Dict[str, Section] = None
    _period_raw: str = None
    _period_type: Optional[str] = None
    _period_code: Optional[str] = None
    _row_counters: defdict = f(default_factory=lambda: defdict(int))

    def __repr__(self):
        return '<Report title={_title}\ndata={_data}>'.format(**self.__dict__)

    def __post_init__(self, xml):
        self._title = self._read_title(xml)
        self._data = self._read_data(xml)

        self._get_periods(xml)
        self._get_year(xml)

    @property
    def year(self):
        return self._year

    @property
    def blank(self):
        return self._blank

    @property
    def title(self):
        return self._title

    @property
    def period_type(self):
        return self._period_type

    @property
    def period_code(self):
        return self._period_code

    @property
    def row_counters(self):
        return self._row_counters

    def items(self):
        '''Итерация по разделам отчёта'''
        for sec_code, section in self._data.items():
            yield sec_code, section

    def get_section(self, section_code):
        '''Возвращает указанную секцию'''
        return self._data.get(section_code)

    def _read_title(self, xml):
        '''Чтение заголовка отчёта'''
        title = []
        for node in xml.xpath('/report/title/item'):
            item = (node.attrib['name'], node.attrib.get('value', '').strip())
            title.append(item)
        return title

    def _read_data(self, xml):
        '''Чтение тела отчёта (разделы/строки/колонки)'''
        data = {}
        for section_xml in xml.xpath('/report/sections/section'):
            section_code = str_int(section_xml.attrib['code'])
            section = Section(section_code)

            for row_xml in section_xml.xpath('./row'):
                row_code = str_int(row_xml.attrib['code'])
                row = Row(row_code, *self._read_row_specs(row_xml))

                for col in row_xml.xpath('./col'):
                    col_code = str_int(col.attrib['code'])

                    row.add_col(col_code, col.text)
                    self._blank = False
                section.add_row(row_code, row)
                self._row_counters[(row_code, row.s1, row.s2, row.s3)] += 1
            data[section_code] = section
        return data

    def _read_row_specs(self, row):
        '''Чтение спицифик строки'''
        return (row.attrib.get(f's{i}') for i in range(1, 4))

    def _get_year(self, xml):
        '''Получение года из корня отчёта'''
        self._year = xml.xpath('/report/@year')[0]

    def _get_periods(self, xml):
        '''Получение и разбиение периода из корня отчёта'''
        self._period_raw = xml.xpath('/report/@period')[0]
        if len(self._period_raw) == 4:
            self._period_type = str_int(self._period_raw[:2])
            self._period_code = str_int(self._period_raw[2:])

    def set_periods(self, catalogs, idp):
        '''Попытка привести тип и код периода к формату
           описанному в приказе Росстата
        '''
        try:
            periods_id = self._get_periods_id(catalogs)

            if int(self._period_raw) not in periods_id:
                return False

            max_code = max(periods_id)

            if max_code <= int(idp):
                self._period_type = idp
                self._period_code = self._period_raw
                return True

            max_div = max_divider(max_code, periods_id)

            if max_code <= int(idp) * max_div:
                self._period_type = idp
                self._period_code = str(int(int(self._period_raw) / max_div))
                return True
            return False
        except Exception:
            return False

    def _get_periods_id(self, catalogs):
        '''Получение идентификаторов допустимых периодов из справочника'''
        try:
            return [int(term_id) for term_id in catalogs['s_time']['ids']]
        except KeyError:
            return [int(term_id) for term_id in catalogs['s_mes']['ids']]
