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
        '''Создание множества с именами полей заголовка'''
        return set(f for f in self._schema.title.xpath('./item/@field'))

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

    def __check_extra(self, field):
        '''Проверка, является ли поле лишним'''
        if field not in self._schema_fields:
            self.error(f'Лишнее поле - {field}', '1')

    def __check_dup(self, field):
        '''Проверка, является ли поле дубликатом'''
        if self._report_fields.count(field) != 0:
            self.error(f'Повтор поля - {field}', '2')

    def __check_value(self, field, value):
        '''Проверка значения в поле'''
        if not value:
            self.error(f'Отсутствует значение в поле - {field}', '3')

    def __check_okpo(self, field, value):
        '''Проверка формата ОКПО'''
        def __is_valid_okpo():
            return True if len(value) in (8, 14) and value.isdigit() else False

        if field == self._schema.obj and not __is_valid_okpo():
            self.error('Код ОКПО должен быть 8-и или 14-и значным числом', '4')

    def _check_required_fields(self):
        '''Проверка наличия ключевого поля в заголовке'''
        if self._schema.obj not in self._report_fields:
            self._schema_fields.discard(self._schema.obj)
            self.error(f'Отсутствует ключевое поле - {self._schema.obj}', '5')

    def _check_missing_fields(self):
        '''Проверка на отсутствие в отчёте полей, описанных в схеме'''
        for filed in self._schema_fields - set(self._report_fields):
            self.error(f'Отсутствует поле - {filed}', '6')
