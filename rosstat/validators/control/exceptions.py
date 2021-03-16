class ControlError(Exception):
    pass


class PeriodExprError(ControlError):
    '''Ошибка разбора формулы проверки периодичности'''


class ConditionExprError(ControlError):
    '''Ошибка разбора условия контроля'''


class RuleExprError(ControlError):
    '''Ошибка разбора правила контроля'''


class PrevPeriodNotImpl(ControlError):
    def __init__(self, id):
        self.id = id
        self.msg = 'Проверка со значениями из прошлого периода не реализована'
