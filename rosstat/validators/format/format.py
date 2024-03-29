from ..base import AbstractValidator
from .inspectors import ValueInspector, SpecInspector
from .exceptions import (FormatError, DuplicateError, EmptyRowError,
                         EmptyColumnError, NoSectionReportError,
                         NoSectionTemplateError, NoRuleError)


class FormatValidator(AbstractValidator):
    name = 'Проверка формата'
    code = '3'

    def __init__(self, schema):
        self._schema = schema
        self.errors = []

    def __repr__(self):
        return '<FormatValidator errors={errors}>'.format(**self.__dict__)

    def validate(self, report):
        try:
            self._check_sections(report)
            self._check_duplicates(report)
            self._check_required(report)
            self._check_format(report)
        except FormatError as ex:
            self.error(ex.msg, ex.code)

        return not bool(self.errors)

    def _check_sections(self, report):
        '''Проверка целостности отчёта'''
        report_sections = set(section.code for section in report.iter())
        schema_sections = set(self._schema.dimension.keys())

        for section in schema_sections - report_sections:
            raise NoSectionReportError(section)

    def _check_duplicates(self, report):
        '''Проверка дубликатов строк'''
        def __fmt_specs(specs):
            return ' '.join(f's{i}={s}' for i, s in enumerate(specs, 1) if s)

        for section in report.iter():
            for row, counter in section.rows_counter.items():
                if counter > 1:
                    row_code, *specs = row
                    if any(specs):
                        row_code = f'{row_code} {__fmt_specs(specs)}'
                    raise DuplicateError(section.code, row_code, counter)

    def _check_required(self, report):
        '''Проверка наличия обязательных к заполнению строк и значений'''
        for sec_code, row_code, col_code in self._schema.required:
            rows = list(report.get_section(sec_code).get_rows(row_code))
            if not rows:
                raise EmptyRowError(sec_code, row_code)

            for row in rows:
                if not row.get_column(col_code):
                    raise EmptyColumnError(sec_code, row_code, col_code)

    def _check_format(self, report):
        '''Проверка формата строк и значений в них'''
        for section in report.iter():
            for row in section.iter():
                self.__check_row(section.code, row.code, row)
                self.__check_cells(section.code, row.code, row)

    def __check_row(self, sec_code, row_code, row):
        '''Итерация по ожидаемым спецификам с их последующей проверкой'''
        specs_map = self.__get_specs(sec_code)
        for col_code, spec_idx in specs_map.items():
            self.__check_format((sec_code, row_code, col_code),
                                SpecInspector, row, spec_idx, specs_map)

    def __check_cells(self, sec_code, row_code, row):
        '''Итерация по значениям строки с их последующей проверкой'''
        for column in row.iter():
            self.__check_format((sec_code, row_code, column.code),
                                ValueInspector, column.value)

    def __check_format(self, coords, inspector_class, *args):
        '''Инициализация инспектора, проверка'''
        inspector = inspector_class(self.__get_format(*coords),
                                    self._schema.catalogs)
        inspector.check(coords, *args)

    def __get_format(self, sec_code, row_code, col_code):
        '''Возвращает словарь с условиями проверки'''
        try:
            return self._schema.formats[sec_code][row_code][col_code]
        except KeyError:
            raise NoRuleError(sec_code, row_code, col_code)

    def __get_specs(self, sec_code):
        '''Возвращает словарь со спецификами'''
        try:
            return self._schema.formats[sec_code]['specs']
        except KeyError:
            raise NoSectionTemplateError(sec_code)
