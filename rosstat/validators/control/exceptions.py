class ControlError(Exception):
    pass


class PeriodExprError(ControlError):
    '''Ошибка разбора формулы проверки периодичности'''


class ConditionExprError(ControlError):
    '''Ошибка разбора условия контроля'''


class RuleExprError(ControlError):
    '''Ошибка разбора правила контроля'''


class StopEvaluation(ControlError):
    '''Прерывание проверки контроля'''


class NoElemToCompareError(StopEvaluation):
    '''Нет элемента для сравнения'''


class NoFormatForRowError(StopEvaluation):
    '''Нет формата для строки из формулы контроля'''


class PrevPeriodNotImpl(ControlError):
    def __init__(self, id):
        self.id = id
        self.msg = 'Проверка со значениями из прошлого периода не реализована'
