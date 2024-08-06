from dataclasses import dataclass

from lark.exceptions import UnexpectedCharacters, UnexpectedToken, VisitError

from ..exceptions import (
    ConditionExprError,
    ControlFault,
    PrevPeriodNotImpl,
    RuleExprError,
)
from ..parser import parse, transform


@dataclass
class ControlParams:
    precision: int
    fault: float
    formats: dict
    catalogs: dict
    dimension: dict


class FormulaInspector:
    def __init__(self, control, *, formats, catalogs, dimension, alerts=False):
        self.alerts = alerts

        self.id = control.attrib["id"]
        self.name = control.attrib["name"]
        self.rule = control.attrib["rule"]
        self.condition = control.attrib["condition"]

        self.tip = int(control.attrib.get("tip", "1"))
        self.fault = float(control.attrib.get("fault", "0"))
        self.precision = int(control.attrib.get("precision", "2"))

        self.params = self.__params(formats, catalogs, dimension)

    def __params(self, formats, catalogs, dimension):
        return ControlParams(
            self.precision, self.fault, formats, catalogs, dimension
        )

    def __str__(self):
        return (
            f"<FormulaInspector id={self.id} tip={self.tip} "
            f"fault={self.fault} precision={self.precision} "
            f"condition={self.condition} rule={self.rule}>"
        )

    def check(self, report):
        if self._check_condition(report) is None:
            return self._check_rule(report)

    def _check_condition(self, report):
        """Проверка условия контроля"""
        return self._check_formula(report, self.condition, ConditionExprError)

    def _check_rule(self, report):
        """Проверка правила"""
        return self._check_formula(report, self.rule, RuleExprError)

    def _check_formula(self, report, formula, exc):
        """Проверка, парсинг и применение формулы на отчёт"""
        try:
            if formula and not self._is_previous_period(formula):
                self.__check(report, self.__parse(formula, exc))
        except ControlFault as exc:
            return exc

    def __parse(self, formula, exc):
        """Парсинг формулы"""
        try:
            return parse(formula)
        except (UnexpectedCharacters, UnexpectedToken):
            raise exc(self.id)

    def __check(self, report, tree):
        """Выполнение проверки"""
        try:
            transform(report, tree, self.params)
        except VisitError as exc:
            raise exc.orig_exc

    def _is_previous_period(self, formula):
        """
        Две фигурные скобки говорят о том, что значение необходимо брать из
        отчёта за прошлый период. Такой функционал не будет реализован
        """
        if "{{" in formula:
            if self.alerts:
                raise PrevPeriodNotImpl(self.id)
            return True
