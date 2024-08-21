class FormatError(Exception):
    pass


# ---


class NoSectionReportError(FormatError):
    def __init__(self, sec_code):
        self.code = "1"
        self.msg = "Раздел {} отсутствует в отчёте".format(sec_code)


class DuplicateError(FormatError):
    def __init__(self, sec_code, row_code, counter):
        self.code = "2"
        self.msg = "Раздел {}, cтрока {} повторяется {} раз(а)".format(
            sec_code, row_code, counter
        )


class EmptyRowError(FormatError):
    def __init__(self, sec_code, row_code):
        self.code = "3"
        self.msg = "Раздел {}, строка {} не может быть пустой".format(
            sec_code, row_code
        )


class EmptyColumnError(FormatError):
    def __init__(self, sec_code, row_code, col_code):
        self.code = "4"
        self.msg = (
            "Раздел {}, строка {}, графа {} не может быть пустой".format(
                sec_code, row_code, col_code
            )
        )


class NoSectionTemplateError(FormatError):
    def __init__(self, sec_code):
        self.code = "5"
        self.msg = "Раздел {} не описан в шаблоне".format(sec_code)


class NoRuleError(FormatError):
    def __init__(self, sec_code, row_code, col_code):
        self.code = "6"
        self.msg = (
            "Раздел {}, строка {}, графа {}. "
            "В шаблоне отсутствует правило для проверки этого поля".format(
                sec_code, row_code, col_code
            )
        )


# ---


class FormatInspectorError(FormatError):
    def update(self, coords):
        self.msg = "Раздел {}, строка {}, графа {}. {}".format(
            *coords, self.msg
        )


class SpecNotInDictError(FormatInspectorError):
    msg = "Специфика отсутствует в справочнике"
    code = "7"


class SpecValueError(FormatInspectorError):
    msg = "Недопустмое значение"
    code = "8"


class ValueNotNumberError(FormatInspectorError):
    msg = "Значение не является числом"
    code = "9"


class ValueBadFormat(FormatInspectorError):
    msg = "Число не соответствует формату"
    code = "10"


class ValueLengthError(FormatInspectorError):
    msg = "Длина строки больше допустимого"
    code = "11"


class ValueNotInDictError(FormatInspectorError):
    msg = "Значение отсутствует в справочнике"
    code = "12"


class ValueNotInRangeError(FormatInspectorError):
    msg = "Значение не входит в диапазон допустимых"
    code = "13"


class ValueNotInListError(FormatInspectorError):
    msg = "Значение не входит в список допустимых"
    code = "14"
