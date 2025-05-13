from numpy import broadcast_to
from numpy.ma import getmask, nomask

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


class RuleCheckFailed(CriticalError):
    def __init__(self, operation, left, right, delta, result):
        self.operation = operation

        mask = self.__get_mask(result)
        left, right = self.__equalize_operands(left, right)

        self.stack = zip(left.flat, right.flat, delta.flat, mask.flat)

    def __get_mask(self, result):
        return result if (mask := getmask(result)) is nomask else mask

    def __equalize_operands(self, left, right):
        if left.size > right.size:
            right = broadcast_to(right, left.shape)
        elif left.size < right.size:
            left = broadcast_to(left, right.shape)
        return left, right

    def __iter__(self):
        for left, right, delta, masked in self.stack:
            if not masked:
                yield RuleFail(
                    operation=self.operation,
                    left=left,
                    right=right,
                    delta=delta,
                )
