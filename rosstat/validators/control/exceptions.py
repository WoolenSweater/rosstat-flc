class ControlError(Exception):
    pass


class PeriodExprError(ControlError):
    """Ошибка разбора формулы проверки периодичности"""


class ConditionExprError(ControlError):
    """Ошибка разбора условия контроля"""


class RuleExprError(ControlError):
    """Ошибка разбора правила контроля"""


class StopEvaluation(ControlError):
    """Прерывание проверки контроля"""


class NoElemToCompareError(StopEvaluation):
    """Нет элемента для сравнения"""


class NoFormatForRowError(StopEvaluation):
    """Нет формата для строки из формулы контроля"""


class ControlFault(StopEvaluation):
    def __init__(self, left, right, delta):
        self.left = float(left)
        self.right = float(right)
        self.delta = float(delta)


class PrevPeriodNotImpl(ControlError):
    msg = "Проверка со значениями из прошлого периода невозможна"
