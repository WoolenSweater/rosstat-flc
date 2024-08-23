from lark.exceptions import UnexpectedCharacters, UnexpectedToken, VisitError

from ..exceptions import (
    ConditionExprError,
    ControlFault,
    PrevPeriodNotImpl,
    RuleExprError,
)
from ..helpers import Formula
from ..parser import parse, transform


class FormulaInspector:
    def __init__(self, control, schema):
        self.schema = schema
        self.control = control

    def __repr__(self):
        return f"<FormulaInspector control={self.control}>"

    def check(self, report):
        if self._check_condition(report) is None:
            return self._check_rule(report)

    def _check_condition(self, report):
        """Проверка условия контроля"""
        return self._check_formula(
            report, self.control.condition, Formula(0), ConditionExprError
        )

    def _check_rule(self, report):
        """Проверка правила"""
        return self._check_formula(
            report, self.control.rule, Formula(1), RuleExprError
        )

    def _check_formula(self, report, formula, type, exc):
        """Проверка, парсинг и применение формулы на отчёт"""
        try:
            if formula and not self.__is_previous_period(formula):
                self.__check(self.__parse(formula, exc), report, type)
        except ControlFault as exc:
            return exc

    def __parse(self, formula, exc):
        """Парсинг формулы"""
        try:
            return parse(formula)
        except (UnexpectedCharacters, UnexpectedToken):
            raise exc(self.control.id)

    def __check(self, tree, report, type):
        """Выполнение проверки"""
        try:
            transform(tree, report, type, self.schema, self.control)
        except VisitError as exc:
            raise exc.orig_exc

    def __is_previous_period(self, formula):
        """
        Две фигурные скобки говорят о том, что значение необходимо брать из
        отчёта за прошлый период. Такой функционал не будет реализован
        """
        if "{{" in formula:
            if self.schema.alerts:
                raise PrevPeriodNotImpl()
            return True
