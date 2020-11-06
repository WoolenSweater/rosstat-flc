class PeriodExprError(Exception):
    msg = 'Ошибка разбора формулы проверки периодичности'


# ---


class ControlError(Exception):
    pass


class ConditionExprError(ControlError):
    msg = 'Ошибка разбора условия контроля'


class RuleExprError(ControlError):
    msg = 'Ошибка разбора правила контроля'


class PrevPeriodNotImpl(ControlError):
    msg = 'Проверка со значениями из прошлого периода не реализована'
