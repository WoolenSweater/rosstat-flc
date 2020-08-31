from typing import List, Dict, Tuple
from dataclasses import dataclass, field, InitVar
from lxml.etree import _ElementTree


@dataclass
class Row:
    code: str
    s1: str
    s2: str
    s3: str
    cols: Dict[str, str] = field(default_factory=dict)

    def items(self):
        for k, v in self.cols.items():
            yield k, v

    def get_entry(self, _entry_code):
        return self.cols.get(_entry_code)

    def add_col(self, col_code, col_text):
        self.cols[col_code] = col_text


@dataclass
class Section:
    code: str
    rows: List[Row] = field(default_factory=list)
    row_codes: List[str] = field(default_factory=list)

    _ignore_specs: Tuple[set] = ({None}, {'*'}, {'0'})

    def items(self):
        for row_code in set(self.row_codes):
            yield row_code, list(self.get_rows(row_code))

    def get_rows(self, _row_code, specs=None):
        for row_code, row in zip(self.row_codes, self.rows):
            if row_code == _row_code and self._check_specs(row, specs):
                yield row

    def _check_specs(self, row, specs):
        if specs is None:
            return True
        for i in range(1, 4):
            row_spec = getattr(row, f's{i}')
            if specs[i] not in self._ignore_specs and row_spec not in specs[i]:
                return False
        return True

    def add_row(self, row_code, row):
        self.row_codes.append(row_code)
        self.rows.append(row)


@dataclass
class Report:
    xml: InitVar[_ElementTree]
    _title: Dict[str, str] = None
    _data: Dict[str, Section] = None
    _period_type: str = '1'
    _period_code: str = '1'

    def __repr__(self):
        return '<Report title={_title}\ndata={_data}>'.format(**self.__dict__)

    def __post_init__(self, xml):
        self._title = self._read_title(xml)
        self._data = self._read_data(xml)

        self._get_periods(xml)

    @property
    def title(self):
        return self._title

    @property
    def period_type(self):
        return self._period_type

    @property
    def period_code(self):
        return self._period_code

    def items(self):
        for k, v in self._data.items():
            yield k, v

    def get_section(self, section_code):
        return self._data.get(section_code)

    def _read_title(self, xml):
        title = {}
        for item in xml.xpath('/report/title/item'):
            title[item.attrib['name']] = item.attrib.get('value', '').strip()
        return title

    def _read_data(self, xml):
        data = {}
        for section_xml in xml.xpath('/report/sections/section'):
            section_code = str(int(section_xml.attrib['code']))
            section = Section(section_code)

            for row_xml in section_xml.xpath('./row'):
                row_code = str(int(row_xml.attrib['code']))
                row = Row(row_code, *self._read_row_specs(row_xml))

                for col in row_xml.xpath('./col'):
                    col_code = str(int(col.attrib['code']))

                    row.add_col(col_code, col.text)
                section.add_row(row_code, row)
            data[section_code] = section
        return data

    def _read_row_specs(self, row):
        return (row.attrib.get(f's{i}') for i in range(1, 4))

    def _get_periods(self, xml):
        period = xml.xpath('/report/@period')[0]
        if len(period) != 4:
            self._period_code = str(int(period))
        else:
            period_type, period_code = period[:2], period[2:]
            self._period_type = str(int(period_type))
            self._period_code = str(int(period_code))
