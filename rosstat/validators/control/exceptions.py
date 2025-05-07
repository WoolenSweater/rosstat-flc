from numpy.ma import array, is_masked, nomask

from .helpers import RuleFail


class BaseControlError(Exception):
    pass


# ---


class StopEvaluation(BaseControlError):
    """Прерывание проверки контроля"""


class NoSectionError(StopEvaluation):
    """Прерывание проверки при отсутствии раздела из формулы контроля"""


class NoCoordinatesError(StopEvaluation):
    """Прерывание проверки при отсутствии кодов координат"""


class NonKeySpecificError(StopEvaluation):
    """
    Прерывание проверки если у элемента указана специфика,
    но она не входит в ключевые (grv) и не является спецификой по умолчанию
    """


class BadShapeError(StopEvaluation):
    """
    Прерывание проверки при расхождении размерностей элементов
    Обнаружено в usl_1ol_01 (0609508)
    """


class SliceError(StopEvaluation):
    """
    Прерывание проверки при невозможности развернуть диапазон
    Обнаружено в f_1rc2rc_01 (0616005)
    """


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


def fround(value):
    return round(float(getattr(value, "data", value)), ndigits=2)


class RuleCheckFailed(CriticalError):
    def __init__(self, operation, left, right, delta, result):
        self.operation = operation
        self.left = left.flat
        self.right = right.flat
        self.delta = self.__cover(delta, result).flat

    def __cover(self, delta, result):
        return array(delta, mask=result | getattr(result, "mask", nomask))

    def __iter__(self):
        for left, right, delta in zip(self.left, self.right, self.delta):
            if not is_masked(delta):
                yield RuleFail(
                    operation=self.operation,
                    left=fround(left),
                    right=fround(right),
                    delta=fround(delta),
                )
