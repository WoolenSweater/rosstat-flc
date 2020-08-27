from ..controls.period import PeriodClause
from ..controls import parser as control_parser
from ..exceptions import (PeriodCheckFail, ConditionExprError, RuleExprError,
                          ConditionCheckFail, RuleCheckFail)


class ControlChecker:
    def __init__(self, control):
        self._control = control

        self.id = control.attrib['id']
        self.name = control.attrib['name']
        self.rule = control.attrib['rule']
        self.condition = control.attrib['condition']

        self.tip = control.attrib.get('tip', '1')
        self.fault = control.attrib.get('fault', '0')
        self.precision = int(control.attrib.get('precision', '2'))

        self.period = PeriodClause(control, self.id)

    def __repr__(self):
        return ('<ControlChecker id={id} name={name} rule={rule} '
                'condition={condition} tip={tip} fault={fault} '
                'period={period} precision={precision}>').format(
                    **self.__dict__)

    def check(self, report, errors_list) -> None:
        '''Метод вызова проверки контроля'''
        try:
            self._check_period(report)
            self._check_condition(report)
            self._check_rule(report)
        except (PeriodCheckFail, ConditionCheckFail):
            pass
        except RuleCheckFail as ex:
            errors_list.extend(self._fmt_errors(ex.msg))
        except (ConditionExprError, RuleExprError) as ex:
            errors_list.append(ex.msg)

    def _fmt_errors(self, errors):
        '''Форматирование сообщения о непройденном контроле'''
        template = '{} {}; слева {} {} справа {} разница {}'
        for err in errors:
            yield template.format(self.id,
                                  self.name,
                                  err['left'],
                                  err['operator'],
                                  err['right'],
                                  err['delta'])

    def _check_period(self, report):
        '''Проверка соответствия периода контроля периоду в отчёте'''
        if not self.period.check(report):
            raise PeriodCheckFail()

    def __check_control(self, evaluator, report):
        '''Выполнение проверки. Возвращает список проваленых проверок'''
        flatten = []
        for result in evaluator.check(report, precision=self.precision):
            flatten.extend(result.controls)
        return flatten

    def _check_condition(self, report):
        '''Проверка условия для выполнения контроля'''
        if self.condition:
            condition = control_parser.parse(self.condition)
            if condition is None:
                raise ConditionExprError(self.id)

            fail_checks = self.__check_control(condition, report)
            if fail_checks:
                raise ConditionCheckFail()

    def _check_rule(self, report):
        '''Проверка правила контроля'''
        if self.rule:
            rule = control_parser.parse(self.rule)
            if rule is None:
                raise RuleExprError(self.id)

            fail_checks = self.__check_control(rule, report)
            if fail_checks:
                raise RuleCheckFail(fail_checks)
