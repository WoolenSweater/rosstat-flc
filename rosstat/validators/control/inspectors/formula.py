from contextlib import suppress

from lark.exceptions import UnexpectedInput, VisitError

from ..exceptions import (
    ConditionExprError,
    PastPeriodError,
    RuleExprError,
    StopEvaluation,
)
from ..helpers import FormulaType
from ..parser import eval, getmask, invert, parse, visit


class FormulaInspector:
    def __init__(self, control, schema):
        self.schema = schema
        self.control = control

    def __repr__(self):
        return f"<FormulaInspector control={self.control}>"

    def check(self, report):
        with suppress(StopEvaluation):
            if invert(mask := getmask(self._check_condition(report))).any():
                return self._check_rule(report, mask)

    def _check_condition(self, report):
        """Проверка условия контроля"""
        return self._check_formula(
            self.control.condition, FormulaType(0), ConditionExprError, report
        )

    def _check_rule(self, report, mask):
        """Проверка правила"""
        return self._check_formula(
            self.control.rule, FormulaType(1), RuleExprError, report, mask
        )

    def _check_formula(self, formula, type, exc, report, mask=None):
        """Проверка, парсинг, препроцессинг и применение формулы на отчёт"""
        if self.__proper(formula):
            tree = self.__parse(formula, exc)
            ctx, lazy = self.__prepare(tree, report)
            return self.__check(tree, ctx, lazy, type, mask)

    def __parse(self, formula, exc):
        """Парсинг формулы"""
        try:
            return parse(formula)
        except UnexpectedInput:
            raise exc(self.control.id)

    def __prepare(self, tree, report):
        """Препроцессинг. Формирование элементов и контекста"""
        try:
            return visit(tree, report, self.schema)
        except VisitError as exc:
            raise exc.orig_exc

    def __check(self, tree, ctx, lazy, type, mask):
        """Выполнение проверки"""
        try:
            return eval(tree, ctx, lazy, type, mask, self.control)
        except VisitError as exc:
            raise exc.orig_exc

    def __proper(self, formula):
        """
        Две фигурные скобки говорят о том, что значение необходимо брать из
        отчёта за прошлый период. Такой функционал не будет реализован
        """
        if formula:
            if "{{" in formula:
                raise PastPeriodError()
            return True
