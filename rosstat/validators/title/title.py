from ..base import AbstractValidator


class TitleValidator(AbstractValidator):
    name = 'Проверка полей заголовка'
    code = '2'

    def __init__(self, schema):
        self._schema = schema
        self.errors = []

        self._report_fields = []
        self._schema_fields = self._get_schema_fields()

    def __repr__(self):
        return ('<TitleValidator schema_fields={_schema_fields} '
                'report_fields={_report_fields} errors={errors}>').format(
                    **self.__dict__)

    def _get_schema_fields(self):
        '''Создание словаря {идентификатор: название} полей заголовка'''
        title_items = self._schema.title.findall('./item')
        return {item.get('field'): item.get('name') for item in title_items}

    def validate(self, report):
        self._check_common(report)
        self._check_required_fields()
        self._check_missing_fields()

        return not bool(self.errors)

    def _check_common(self, report):
        '''Выполенние цикла опервичных проверок'''
        for field, value in report.title:
            self.__check_extra(field)
            self.__check_dup(field)
            self.__check_value(field, value)
            self.__check_okpo(field, value)

            self._report_fields.append(field)

    def __format_field(self, field):
        '''Возвращает отформатированные название и идентификатор поля'''
        return f'"{self._schema_fields[field]}" [{field}]'

    def __check_extra(self, field):
        '''Проверка, является ли поле лишним'''
        if field not in self._schema_fields:
            self.error(f'Лишнее поле [{field}]', '1')

    def __check_dup(self, field):
        '''Проверка, является ли поле дубликатом'''
        if field in self._report_fields:
            field = self.__format_field(field)
            self.error(f'Повтор поля {field}', '2')

    def __check_value(self, field, value):
        '''Проверка значения в поле'''
        if not value:
            field = self.__format_field(field)
            self.error(f'Отсутствует значение в поле {field}', '3')

    def __check_okpo(self, field, value):
        '''Проверка формата ОКПО'''
        def __is_valid_okpo():
            if len(value) in (8, 10, 14) and value.isdigit():
                return True
            return False

        if field == self._schema.obj and not __is_valid_okpo():
            self.error('Код ОКПО должен быть длиной 8, 10 или 14 цифр', '4')

    def _check_required_fields(self):
        '''Проверка наличия ключевого поля в заголовке'''
        if self._schema.obj not in self._report_fields:
            field = self.__format_field(self._schema.obj)
            self.error(f'Отсутствует ключевое поле {field}', '5')
            self._schema_fields.pop(self._schema.obj, None)

    def _check_missing_fields(self):
        '''Проверка на отсутствие в отчёте полей, описанных в схеме'''
        for field in set(self._schema_fields) - set(self._report_fields):
            field = self.__format_field(field)
            self.error(f'Отсутствует поле {field}', '6')
