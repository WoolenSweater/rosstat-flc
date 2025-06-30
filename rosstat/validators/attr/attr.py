from ..base import AbstractValidator
from .exceptions import (
    AttrError,
    IdpError,
    PeriodError,
    VersionError,
    YearError,
)
from .inspectors import PeriodInspector


class AttrValidator(AbstractValidator):
    name = "Проверка атрибутов"
    code = "1"

    def __init__(self, schema):
        self.errors = []
        self.version = schema.version

        self.period = PeriodInspector(schema)

    def __repr__(self):
        return (
            f"<AttrValidator "
            f"version={self.version} "
            f"period={self.period} "
            f"errors={self.errors}>"
        )

    def validate(self, report):
        try:
            self._check_version(report)
            self._check_year(report)
            self._recode_period(report)
            self._check_period(report)
        except AttrError as exc:
            self.error(exc.msg, exc.code)

        return not bool(self.errors)

    def _check_version(self, report):
        """Проверка совпадения версий отчёта и схемы"""
        if report.version != self.version:
            raise VersionError()

    def _check_year(self, report):
        """Проверка вхождения года в справочник схемы"""
        if report.year not in self.period.years:
            raise YearError()

    def _recode_period(self, report):
        """Разбор формата периода"""
        self.period.recode_period(report)

    def _check_period(self, report):
        """Проверка типа и номера периодичности"""
        if not self.period.validate_idp(report):
            raise IdpError()
        if not self.period.validate_period(report):
            raise PeriodError()
