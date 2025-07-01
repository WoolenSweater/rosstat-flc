from ..base import AbstractValidator
from .exceptions import (
    DuplicateRowError,
    FormatError,
    FormatInspectorError,
    NoRequiredValueError,
    NoRuleError,
    NoSectionReportError,
    NoSectionTemplateError,
)
from .helpers import ReqsChecker
from .inspectors import SpecInspector, ValueInspector


class FormatValidator(AbstractValidator):
    name = "Проверка формата"
    code = "3"

    def __init__(self, schema):
        self.errors = []

        self.allowempty = schema.allowempty
        self.dimension = schema.dimension
        self.required = schema.required
        self.catalogs = schema.catalogs
        self.formats = schema.formats

    def __repr__(self):
        return (
            f"<FormatValidator "
            f"dimension={self.dimension} "
            f"required={self.required} "
            f"formats={self.formats} "
            f"errors={self.errors}>"
        )

    @staticmethod
    def _fmt(specs):
        """Форматирование специфик"""
        return " ".join(f"s{i}={s}" for i, s in enumerate(specs, 1) if s)

    @staticmethod
    def __get_coords(*coords):
        """Группировка координат"""
        return coords

    def validate(self, report):
        try:
            if not report.empty or not self.allowempty:
                self._check_sections(report)
                self._check_duplicates(report)
                self._check_required(report)
                self._check_format(report)
        except FormatError as exc:
            self.error(exc.msg, exc.code)

        return not bool(self.errors)

    def _check_sections(self, report):
        """Проверка целостности отчёта"""
        for section in self.dimension.keys() - report.sections.keys():
            raise NoSectionReportError(section)

    def _check_duplicates(self, report):
        """Проверка дубликатов строк"""
        for section in report.iter():
            for row, counter in section.rows_counter.items():
                if counter > 1:
                    row_code, *specs = row
                    if any(specs):
                        row_code = f"{row_code} {self._fmt(specs)}"
                    raise DuplicateRowError(section.code, row_code, counter)

    def _check_required(self, report):
        """Проверка наличия обязательных к заполнению строк и значений"""
        for coords in self.required:
            if not ReqsChecker.has_value(report, coords):
                raise NoRequiredValueError(*coords)

    def _check_format(self, report):
        """Проверка формата строк и значений в них"""
        for section in report.iter():
            specs = self.__get_specs(section.code)

            for row in section.iter():
                self.__check_specs(section.code, row, specs)
                self.__check_cells(section.code, row)

    # ---

    def __check_specs(self, sec_code, row, specs):
        """Итерация по ожидаемым спецификам с их последующей проверкой"""
        for spec_key, col_code in specs.items():
            coords = self.__get_coords(sec_code, row.code, col_code)
            self.__check_format(SpecInspector, coords, row, specs, spec_key)

    def __check_cells(self, sec_code, row):
        """Итерация по значениям строки с их последующей проверкой"""
        for col in row.iter():
            coords = self.__get_coords(sec_code, row.code, col.code)
            self.__check_format(ValueInspector, coords, col)

    def __check_format(self, inspector, coords, *args):
        """Инициализация инспектора, проверка, обработка исключения"""
        try:
            inspector(self.catalogs, self.__get_format(*coords)).check(*args)
        except FormatInspectorError as exc:
            exc.update(coords)
            raise

    # ---

    def __get_format(self, sec_code, row_code, col_code):
        """Возвращает словарь с условиями проверки"""
        try:
            return self.formats[sec_code][row_code][col_code]
        except KeyError:
            raise NoRuleError(sec_code, row_code, col_code)

    def __get_specs(self, sec_code):
        """Возвращает словарь со спецификами"""
        try:
            return self.formats[sec_code]["specs"]
        except KeyError:
            raise NoSectionTemplateError(sec_code)
