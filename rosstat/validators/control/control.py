from ..base import AbstractValidator
from .exceptions import PastPeriodError, RuleCheckFailed
from .helpers import Control
from .inspectors import FormulaInspector, PeriodInspector


class ControlValidator(AbstractValidator):
    name = "Проверка контролей"
    code = "4"

    def __init__(self, schema):
        self.errors = []
        self.schema = schema

    def __repr__(self):
        return f"<ControlValidator errors={self.errors}>"

    @staticmethod
    def _fmt(control, err):
        """Форматирование сообщения о непройденном контроле"""
        return (
            f"{control.name}; "
            f"слева {err.left} {err.operation} "
            f"справа {err.right} разница {err.delta}"
        )

    def validate(self, report):
        if not report.empty:
            self._check_controls(report)

        return not bool(self.errors)

    def _check_controls(self, report):
        """Проверка отчёта по контролям"""
        for control in map(Control, self.schema.controls):
            self._check_control(report, control)

    def _check_control(self, report, control):
        """Обёртка для обработки исключения"""
        try:
            if self.__check_period(report, control):
                self.__check_control(report, control)
        except PastPeriodError as err:
            self.__err_period(err, control)
        except RuleCheckFailed as err:
            self.__err_many(err, control)

    def __err_period(self, err, control):
        """Формат-ие ошибки о пропуске контроля со знач. из прошлого периода"""
        if self.schema.alerts:
            self.error(err.msg, control.id, level=0)

    def __err_many(self, errs, control):
        """Формат-ие ошибок проверки контроля"""
        for err in errs:
            self.error(self._fmt(control, err), control.id, level=control.tip)

    def __check_period(self, report, control):
        """Проверка соответствия периода контроля периоду в отчёте"""
        return PeriodInspector(control).check(report)

    def __check_control(self, report, control):
        """Проверка контрольных значений отчёта"""
        return FormulaInspector(control, self.schema).check(report)
