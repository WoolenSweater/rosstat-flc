from collections import namedtuple

from lark.exceptions import VisitError

from ..exceptions import ConditionExprError, PrevPeriodNotImpl, RuleExprError
from ..parser import parse, transform

ControlParams = namedtuple(
    "ControlParams",
    ("is_rule", "formats", "catalogs", "dimension", "precision", "fault"),
)


class FormulaInspector:
    def __init__(self, control, *, formats, catalogs, dimension, skip_warns):
        self._skip_warns = skip_warns

        self.formats = formats
        self.catalogs = catalogs
        self.dimension = dimension
        self.id = control.attrib["id"]
        self.name = control.attrib["name"]
        self.rule = control.attrib["rule"].strip()
        self.condition = control.attrib["condition"].strip()

        self.tip = int(control.attrib.get("tip", "1"))
        self.fault = float(control.attrib.get("fault", "-1"))
        self.precision = int(control.attrib.get("precision", "2"))

    def __repr__(self):
        return (
            "<FormulaInspector id={id} name={name} rule={rule} "
            "condition={condition} fault={fault} "
            "precision={precision}>"
        ).format(**self.__dict__)

    def check(self, report):
        if self._check_condition(report) is None:
            return self._check_rule(report)

    def _check_condition(self, report):
        """Проверка условия для выполнения контроля"""
        if self.condition and not self._is_previous_period(self.condition):
            evaluator = self.__parse(self.condition, ConditionExprError)
            return self.__check(report, evaluator, self.__params())

    def _check_rule(self, report):
        """Проверка правила контроля"""
        if self.rule and not self._is_previous_period(self.rule):
            evaluator = self.__parse(self.rule, RuleExprError)
            return self.__check(report, evaluator, self.__params(is_rule=True))

    def __params(self, is_rule=False):
        """Упаковка параметров для проверки в именованный кортеж"""
        return ControlParams(
            is_rule,
            self.formats,
            self.catalogs,
            self.dimension,
            self.precision,
            self.fault if is_rule else float(-1),
        )

    def __parse(self, formula, exc):
        """Парсинг формулы контроля"""
        evaluator = parse(formula)
        if evaluator is None:
            raise exc(self.id)
        return evaluator

    def __check(self, report, tree, params):
        """Выполнение проверки. Возвращает список проваленых проверок"""
        try:
            transform(report, tree, params)
        except VisitError as exc:
            return exc.orig_exc

    def _is_previous_period(self, formula):
        """Проверка наличия в формуле элемента в двух фигурных скобках,
        что говорит о том, что значение берётся за прошлый период.
        Такой функционал пока неизвестно когда получится реализовать
        """
        if "{{" in formula:
            if self._skip_warns:
                return True
            else:
                raise PrevPeriodNotImpl(self.id)
