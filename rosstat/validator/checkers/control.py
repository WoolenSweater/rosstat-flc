from typing import Dict
from dataclasses import dataclass
from ..controls.period import PeriodClause
from ..controls import parser as control_parser
from ..exceptions import (PeriodCheckFail, ConditionExprError, RuleExprError,
                          ConditionCheckFail, RuleCheckFail, PrevPeriodNotImpl)


class ControlChecker:
    def __init__(self, control, *, dimension, skip_warns):
        self._control = control
        self._dimension = dimension
        self._skip_warns = skip_warns

        self.id = control.attrib['id']
        self.name = control.attrib['name']
        self.rule = control.attrib['rule'].strip()
        self.condition = control.attrib['condition'].strip()

        self.tip = control.attrib.get('tip', '1')
        self.fault = float(control.attrib.get('fault', '-1'))
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
        except PrevPeriodNotImpl:
            if not self._skip_warns:
                errors_list.append(ex.msg)

    def _fmt_errors(self, errors):
        '''Форматирование сообщения о непройденном контроле'''
        template = '{} {}; слева {} {} справа {} разница {}; обязательность {}'
        for err in errors:
            yield template.format(self.id,
                                  self.name,
                                  err['left'],
                                  err['operator'],
                                  err['right'],
                                  err['delta'],
                                  'да' if self.tip == '1' else 'нет')

    def _check_period(self, report):
        '''Проверка соответствия периода контроля периоду в отчёте'''
        if not self.period.check(report):
            raise PeriodCheckFail()

    def __check_control(self, evaluator, report, is_rule=False):
        '''Выполнение проверки. Возвращает список проваленых проверок'''
        flatten = []
        params = ControlParams(self._dimension,
                               self.precision,
                               self.fault,
                               is_rule=is_rule)
        for result in evaluator.check(report, params):
            flatten.extend(result.controls)
        return flatten

    def _check_condition(self, report):
        '''Проверка условия для выполнения контроля'''
        if self.condition and not self._is_previous_period(self.condition):
            condition = control_parser.parse(self.condition)
            if condition is None:
                raise ConditionExprError(self.id)

            fail_checks = self.__check_control(condition, report)
            if fail_checks:
                raise ConditionCheckFail()

    def _check_rule(self, report):
        '''Проверка правила контроля'''
        if self.rule and not self._is_previous_period(self.rule):
            rule = control_parser.parse(self.rule)
            if rule is None:
                raise RuleExprError(self.id)

            fail_checks = self.__check_control(rule, report, is_rule=True)
            if fail_checks:
                raise RuleCheckFail(fail_checks)

    def _is_previous_period(self, formula):
        '''Проверка наличия в формуле элемента в двух фигурных скобках,
           что говорит о том, что значение берётся за прошлый период.
           Такой функционал пока неизвестно когда получится реализовать
        '''
        if '{{' in formula:
            raise PrevPeriodNotImpl(self.id)


@dataclass
class ControlParams:
    dimension: Dict[str, list]
    precision: int
    fault: float
    is_rule: bool = False

    def __post_init__(self):
        self.fault = float(-1) if not self.is_rule else self.fault
