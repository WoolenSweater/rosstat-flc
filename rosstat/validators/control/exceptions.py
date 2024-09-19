class BaseControlError(Exception):
    pass


# ---


class StopEvaluation(BaseControlError):
    """Прерывание проверки контроля"""


class NoSectionError(StopEvaluation):
    """Прерывание проверки при отсутствии раздела из формулы контроля"""


class EmptyElementError(StopEvaluation):
    """Прерывание проверки при полном отсутствии данных"""


class ConditionCheckFailed(StopEvaluation):
    """Прерывание проверки условия при отсутствии положительных результатов"""


# ---


class CriticalError(BaseControlError):
    """Критическая ошибка проверки контроля"""


class ConditionExprError(CriticalError):
    """Ошибка разбора формулы условия контроля"""


class RuleExprError(CriticalError):
    """Ошибка разбора формулы правила контроля"""


class PeriodExprError(CriticalError):
    """Ошибка разбора формулы периодичности"""


class PrevPeriodNotImpl(CriticalError):
    msg = "Проверка со значениями из прошлого периода невозможна"


class RuleCheckFailed(CriticalError):
    def __init__(self, operation, left, right, delta):
        self.operation = operation
        self.left = left
        self.right = right
        self.delta = delta
