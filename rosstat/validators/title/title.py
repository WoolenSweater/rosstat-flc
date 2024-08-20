from ..base import AbstractValidator


class TitleValidator(AbstractValidator):
    name = "Проверка полей заголовка"
    code = "2"

    def __init__(self, schema):
        self.schema = schema
        self.errors = []

        self.report_fields = []
        self.schema_fields = dict(self.__get_schema_fields(schema))

    def __repr__(self):
        return (
            f"<TitleValidator "
            f"schema_fields={self.schema_fields} "
            f"report_fields={self.report_fields} "
            f"errors={self.errors}>"
        )

    @staticmethod
    def __get_schema_fields(schema):
        """Чтение полей заголовка схемы"""
        for item in schema.title.iterfind("item"):
            yield item.get("field"), item.get("name")

    @staticmethod
    def __is_valid_okpo(value):
        """Проверка формата ОКПО"""
        return len(value) in (8, 10, 14) and value.isdigit()

    def validate(self, report):
        self._check_common_rules(report)
        self._check_required_field()
        self._drop_required_field()
        self._check_missing_fields()

        return not bool(self.errors)

    def _check_common_rules(self, report):
        """Выполенние цикла первичных проверок"""
        for field, value in report.title.items():
            self.__check_extra(field)
            self.__check_dup(field)
            self.__check_value(field, value)
            self.__check_okpo(field, value)

            self.report_fields.append(field)

    def _drop_required_field(self):
        """Удаление ключевого поля, чтобы не мешало следующей проверке"""
        del self.schema_fields[self.schema.obj]

    def _fmt(self, field):
        """Форматированные название и идентификатор поля"""
        return f"'{self.schema_fields[field]}' [{field}]"

    # ---

    def __check_extra(self, field):
        """Проверка, является ли поле лишним"""
        if field not in self.schema_fields:
            self.error(f"Лишнее поле [{field}]", "1")

    def __check_dup(self, field):
        """Проверка, является ли поле дубликатом"""
        if field in self.report_fields:
            self.error(f"Повтор поля {self._fmt(field)}", "2")

    def __check_value(self, field, value):
        """Проверка значения в поле"""
        if not value:
            self.error(f"Отсутствует значение в поле {self._fmt(field)}", "3")

    def __check_okpo(self, field, value):
        """Проверка формата ОКПО"""
        if field == self.schema.obj and not self.__is_valid_okpo(value):
            self.error("Код ОКПО должен быть длиной 8, 10 или 14 цифр", "4")

    # ---

    def _check_required_field(self):
        """Проверка наличия ключевого поля в заголовке"""
        if self.schema.obj not in self.report_fields:
            self.error(
                f"Отсутствует ключевое поле {self._fmt(self.schema.obj)}", "5"
            )

    def _check_missing_fields(self):
        """Проверка на отсутствие в отчёте полей, описанных в схеме"""
        for field in self.schema_fields.keys() - self.report_fields:
            self.error(f"Отсутствует поле {self._fmt(field)}", "6")
