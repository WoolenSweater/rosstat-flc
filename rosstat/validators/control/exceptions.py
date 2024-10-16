class BaseControlError(Exception):
    pass


# ---


class StopEvaluation(BaseControlError):
    """Прерывание проверки контроля"""


class NoSectionError(StopEvaluation):
    """Прерывание проверки при отсутствии раздела из формулы контроля"""


class NoCoordinatesError(StopEvaluation):
    """Прерывание проверки при отсутствии кодов координат"""


class BadShapeError(StopEvaluation):
    """Прерывание проверки при расхождении размерностей элементов"""


class ConditionCheckFailed(StopEvaluation):
    """Прерывание проверки условия при отсутствии положительных результатов"""


def raise_for_reason(exc):
    if "operands could not be broadcast together with shapes" in str(exc):
        raise BadShapeError()
    raise exc


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
