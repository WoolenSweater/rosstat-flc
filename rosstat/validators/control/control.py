from ..base import AbstractValidator
from .inspectors import PeriodInspector, FormulaInspector


class ControlValidator(AbstractValidator):
    name = 'Проверка контролей'
    code = '4'

    def __init__(self, schema):
        self._schema = schema
        self.errors = []

        self._template = ('{control_name}; слева {left} {operator} '
                          'справа {right} разница {delta}')

    def __repr__(self):
        return '<ControlValidator errors={errors}>'.format(**self.__dict__)

    def __fmt_error(self, err, name):
        '''Форматирование сообщения о непройденном контроле'''
        return self._template.format(control_name=name, **err)

    def validate(self, report):
        self._check_controls(report)

        return not bool(self.errors)

    def _check_controls(self, report):
        '''Проверка отчёта по контролям'''
        if report.blank:
            return

        for control in self._schema.controls:
            if not self.__check_period(report, control):
                continue
            self.__check_control(report, control)

    def __check_period(self, report, control):
        '''Проверка соответствия периода контроля периоду в отчёте'''
        inspector = PeriodInspector(control)
        return inspector.check(report)

    def __check_control(self, report, control):
        '''Проверка контрольных значений отчёта'''
        inspector = FormulaInspector(control,
                                     formats=self._schema.formats,
                                     catalogs=self._schema.catalogs,
                                     dimension=self._schema.dimension,
                                     skip_warns=self._schema.skip_warns)
        for err in inspector.check(report):
            message = self.__fmt_error(err, inspector.name)
            self.error(message, inspector.id, tip=inspector.tip)
