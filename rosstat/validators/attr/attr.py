import re
from ..base import AbstractValidator

year_pattern = re.compile(r'18\d{2}|19\d{2}|20\d{2}')


class AttrValidator(AbstractValidator):
    name = 'Проверка аттрибутов'
    code = '1'

    def __init__(self, schema):
        self._schema = schema
        self.errors = []

    def __repr__(self):
        return '<AttrValidator errors={errors}>'.format(**self.__dict__)

    def validate(self, report):
        self._check_year(report)
        self._check_match(report)
        self._check_period(report)

        return not bool(self.errors)

    def _check_year(self, report):
        '''Проверка формата года'''
        if not year_pattern.match(report.year):
            self.error('Указан недопустимый год', '1')

    def _check_match(self, report):
        '''Проверка совпадения типа периода отчёта с периодом схемы'''
        if report.period_type is not None:
            if report.period_type != self._schema.idp:
                self.error('Тип периодичности отчёта не соответствует '
                           'типу периодичности шаблона', '2')

    def _check_period(self, report):
        '''Проверка кода периода'''
        if report.period_code is None:
            if not report.set_periods(self._schema.catalogs, self._schema.idp):
                self.error('Неверное значение периода отчёта', '3')
