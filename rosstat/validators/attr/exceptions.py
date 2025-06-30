class AttrError(Exception):
    pass


class VersionError(AttrError):
    msg = "Версия шаблона не соответствует версии проверяемого отчёта"
    code = "1"


class YearError(AttrError):
    msg = "Указан недопустимый год"
    code = "2"


class IdpError(AttrError):
    msg = (
        "Тип периодичности отчёта не соответствует типу периодичности шаблона"
    )
    code = "3"


class PeriodError(AttrError):
    msg = "Неверное значение периода отчёта"
    code = "4"
