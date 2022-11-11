from math import gcd
from typing import Dict, List, Optional
from collections import defaultdict, namedtuple
from dataclasses import dataclass, InitVar, field as f
from lxml.etree import _ElementTree
from .helpers import SPEC_KEYS, MultiDict, str_int

ANY_SPEC = {'*'}

Title = namedtuple('Title', ['name', 'value'])
Column = namedtuple('Column', ['code', 'value'])


class EmptyIter:

    def iter(self, *args):
        return []


EMPTY_ITER = EmptyIter()


def max_divider(num, terms):
    '''НОД для списка чисел'''
    for term_id in terms:
        num = gcd(num, int(term_id))
    return num


class CodeIterable:

    def iter(self, codes=None):
        '''Метод получения итератора по элементам'''
        if codes is None or codes == ['*']:
            return self._iter_all()
        else:
            return self._iter_codes(codes)


@dataclass
class Row:
    code: str
    s1: str
    s2: str
    s3: str

    _cols: Dict[str, Column] = f(default_factory=dict)

    # ---

    def add_col(self, col_code, col_text):
        '''Добавление колонки в строку'''
        self._cols[col_code] = Column(col_code, col_text)

    # ---

    def iter(self, codes=None, dimension=None):
        '''Метод получения итератора по элементам'''
        if codes is None and dimension is None:
            return self._iter_all()
        if codes is None or codes == ['*']:
            return self._iter_codes(dimension)
        else:
            return self._iter_codes(codes)

    def _iter_all(self):
        '''Возвращает итератор по всем колонкам'''
        return self._cols.values()

    def _iter_codes(self, codes):
        '''Итерируемся по кодам, возвращаем колонку либо "заглушку"'''
        for code in codes:
            yield self.get_column(code) or Column(code, None)

    def get_column(self, code):
        '''Возвращает колонку'''
        return self._cols.get(code)

    # ---

    def match(self, specs):
        '''Проверка, входит ли строка в список переданных специфик'''
        for spec in specs:
            row_spec = self.get_spec(spec.key) or spec.default
            if spec == ANY_SPEC:
                return True
            elif row_spec not in spec:
                return False
        return True

    def get_spec(self, key):
        '''Возвращает указанную специфику строки или дефолтную'''
        return getattr(self, key)


@dataclass
class Section(CodeIterable):
    code: str

    _rows: MultiDict = f(default_factory=MultiDict)
    _rows_counter: defaultdict = f(default_factory=lambda: defaultdict(int))

    @property
    def rows(self):
        return self._rows

    @property
    def rows_counter(self):
        return self._rows_counter

    # ---

    def add_row(self, row):
        '''Добавление строки в раздел и приращение счётчика'''
        self._rows.add(row.code, row)
        self._rows_counter[(row.code, row.s1, row.s2, row.s3)] += 1

    # ---

    def _iter_all(self):
        '''Возвращает итератор по всем строкам'''
        return iter(self._rows.getall())

    def _iter_codes(self, codes):
        '''Итерируемся по кодам, получаем строки с указанным кодом,
           если список строк не пуст, возвращаем каждую строку,
           иначе строку "заглушку"
        '''
        for code in codes:
            for row in (self.get_rows(code) or [Row(code, None, None, None)]):
                yield row

    def get_rows(self, code):
        '''Возвращает список строк"'''
        return self._rows.get(code)


@dataclass
class Report(CodeIterable):
    xml: InitVar[_ElementTree]
    _blank: bool = True
    _year: str = None
    _title: List[Title] = None
    _data: Dict[str, Section] = None
    _period_raw: str = None
    _period_type: Optional[str] = None
    _period_code: Optional[str] = None

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

    # ---

    def _iter_all(self):
        '''Возвращает итератор по всем разделам'''
        return self._data.values()

    def _iter_codes(self, codes):
        '''Итерируемся по кодам, возвращаем разделы'''
        for code in codes:
            yield self.get_section(code)

    def get_section(self, code):
        '''Возвращает раздел с указанным кодом'''
        return self._data.get(code, EMPTY_ITER)

    # ---

    def _read_title(self, xml):
        '''Чтение заголовков отчёта'''
        title = []
        for node in xml.xpath('/report/title/item'):
            title.append(Title(node.attrib.get('name'),
                               node.attrib.get('value', '').strip()))
        return title

    # ---

    def _read_data(self, xml):
        '''Чтение тела отчёта (разделы/строки/колонки)'''
        data = {}
        for section_xml in xml.xpath('/report/sections/section'):
            section = Section(self._get_code(section_xml))

            for row_xml in section_xml.xpath('./row'):
                row = Row(self._get_code(row_xml), **self._read_specs(row_xml))

                for col_xml in row_xml.xpath('./col'):
                    row.add_col(self._get_code(col_xml), col_xml.text)

                    self._blank = False

                section.add_row(row)
            data[section.code] = section
        return data

    def _get_code(self, xml):
        '''Возвращает код элемента (раздела/строки/колонки)'''
        return str_int(xml.attrib.get('code'))

    def _read_specs(self, xml):
        '''Чтение спицифик строки'''
        return {spec_key: xml.attrib.get(spec_key) for spec_key in SPEC_KEYS}

    # ---

    def _get_year(self, xml):
        '''Получение года из корня отчёта'''
        self._year = xml.xpath('/report/@year')[0]

    def _get_periods(self, xml):
        '''Получение и разбиение периода из корня отчёта'''
        self._period_raw = xml.xpath('/report/@period')[0]
        if len(self._period_raw) == 4:
            self._period_type = str_int(self._period_raw[:2])
            self._period_code = str_int(self._period_raw[2:])

    # ---

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
