import re

from ..base import AbstractValidator

year_pattern = re.compile(r"18\d{2}|19\d{2}|20\d{2}")


class AttrValidator(AbstractValidator):
    name = "Проверка атрибутов"
    code = "1"

    def __init__(self, schema):
        self.errors = []

        self.idp = schema.idp
        self.catalogs = schema.catalogs
        self.version = schema.version

    def __repr__(self):
        return f"<AttrValidator idp={self.idp} errors={self.errors}>"

    def validate(self, report):
        if self._check_version(report):
            self._check_year(report)
            self._check_match(report)
            self._check_period(report)

        return not bool(self.errors)

    def _check_version(self, report):
        """Проверка совпадения версий отчёта и схемы"""
        if not (match := self.version == report.version):
            self.error(
                "Версия шаблона не соответствует версии проверяемого отчёта",
                "1",
            )
        return match

    def _check_year(self, report):
        """Проверка формата года"""
        if not year_pattern.match(report.year):
            self.error("Указан недопустимый год", "2")

    def _check_match(self, report):
        """Проверка совпадения типа периода отчёта с периодом схемы"""
        if report.period_type is not None:
            if report.period_type != str(int(self.idp)):
                self.error(
                    "Тип периодичности отчёта не соответствует "
                    "типу периодичности шаблона",
                    "3",
                )

    def _check_period(self, report):
        """Проверка кода периода"""
        if report.period_code is None:
            if not report.set_periods(self.catalogs, self.idp):
                self.error("Неверное значение периода отчёта", "4")
