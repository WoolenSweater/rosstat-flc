from ..base import AbstractValidator
from .inspectors import ValueInspector, SpecInspector


class FormatValidator(AbstractValidator):
    name = 'Проверка формата'
    code = '3'

    def __init__(self, schema):
        self._schema = schema
        self.errors = []

    def __repr__(self):
        return '<FormatValidator errors={errors}>'.format(**self.__dict__)

    def validate(self, report):
        self._check_sections(report)
        self._check_duplicates(report)
        self._check_required(report)
        self._check_format(report)

        return not bool(self.errors)

    def _check_sections(self, report):
        '''Проверка целостности отчёта'''
        report_sections = set(code for code, _ in report.items())
        schema_sections = set(self._schema.dimension.keys())

        for section in schema_sections - report_sections:
            self.error(f'Отсутствует раздел - {section}', '1')

    def _check_duplicates(self, report):
        '''Проверка дубликатов строк'''
        def __fmt_specs(specs):
            return ' '.join(f's{i}={s}' for i, s in enumerate(specs, 1))

        for row, counter in report.row_counters.items():
            if counter > 1:
                row_code, *specs = row
                row = f'{row_code} {__fmt_specs(specs)}' if specs else row_code
                self.error(f'Строка {row} повторяется {counter} раз(а)', '2')

    def _check_required(self, report):
        '''Проверка наличия обязательных к заполнению строк и значений'''
        for sec_code, row_code, col_code in self._schema.required:
            rows = list(report.get_section(sec_code).get_rows(row_code))
            if not rows:
                self.error(f'Раздел {sec_code}, строка {row_code} '
                           f'не может быть пустой', '3')

            for row in rows:
                if not row.get_col(col_code):
                    self.error(f'Раздел {sec_code}, строка {row_code}, графа '
                               f'{col_code} не может быть пустой', '4')

    def _check_format(self, report):
        '''Проверка формата строк и значений в них'''
        for sec_code, section in report.items():
            for row_code, rows in section.items():
                for row in rows:
                    self.__check_row(sec_code, row_code, row)
                    self.__check_cells(sec_code, row_code, row)

    def __check_row(self, sec_code, row_code, row):
        '''Итерация по ожидаемым спецификам с их последующей проверкой'''
        specs_map = self.__get_specs(sec_code)
        for col_code, spec in specs_map.items():
            coords = (sec_code, row_code, col_code)
            self.__check_fmt(
                coords, SpecInspector, row, spec, specs_map,
                err_msg='Раздел {}, строка {}, специфика {}. {}', code='5')

    def __check_cells(self, sec_code, row_code, row):
        '''Итерация по значениям строки с их последующей проверкой'''
        for col_code, value in row.items():
            coords = (sec_code, row_code, col_code)
            self.__check_fmt(
                coords, ValueInspector, value,
                err_msg='Раздел {}, строка {}, графа {}. {}', code='6')

    def __check_fmt(self, coords, inspector_class, *args, err_msg, code):
        '''Инициализация инспектора, проверка'''
        fmt_node = self.__get_format_node(*coords)
        inspector = inspector_class(fmt_node, self._schema.dics)
        error = inspector.check(*args)
        if error:
            self.error(err_msg.format(*coords, error), code)

    def __get_format_node(self, sec_code, row_code, col_code):
        '''Возвращает ноду с услвоиями проверки'''
        return self._schema.format[sec_code][row_code][col_code]

    def __get_specs(self, sec_code):
        '''Возвращает словарь со спецификами'''
        return self._schema.format[sec_code]['specs']
