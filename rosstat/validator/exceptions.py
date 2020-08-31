class ValidationError(Exception):
    pass


class FormatError(ValidationError):
    pass


class NotNumericValue(FormatError):
    msg = 'Значение не является числом'


class InvalidNumFormat(FormatError):
    msg = 'Число не соответствует формату'


class InvalidStrLength(FormatError):
    msg = 'Длина строки больше допустимого'


class OutOfDict(FormatError):
    msg = 'Значение не существует в справочнике'


class OutOfRange(FormatError):
    msg = 'Значение не входит в диапазон допустимых'


class OutOfList(FormatError):
    msg = 'Значение не входит в список допустимых'


class OutOfAdditionDict(FormatError):
    msg = 'Значение не существует в справочнике приложении'


class ControlError(ValidationError):
    pass


class PeriodCheckFail(ControlError):
    pass


class ConditionCheckFail(ControlError):
    pass


class RuleCheckFail(ControlError):
    def __init__(self, failed_controls):
        self.msg = failed_controls


class ConditionExprError(ControlError):
    def __init__(self, _id):
        self.msg = f'Ошибка разбора условия контроля {_id}'


class RuleExprError(ControlError):
    def __init__(self, _id):
        self.msg = f'Ошибка разбора правила контроля {_id}'


class PeriodExprError(ControlError):
    def __init__(self, _id):
        self.msg = f'Ошибка разбора формулы проверки периодичности {_id}'


class PrevPeriodNotImpl(ControlError):
    def __init__(self, _id):
        self.msg = (f'Проверка со значениями из прошлого периода '
                    f'не реализована {_id}')
