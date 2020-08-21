from .exceptions import ValidationError
from .controls import parser as control_parser


class CellChecker:
    def __init__(self, cell, input_type, dics):
        self._cell = cell
        self._dics = dics

        self.input_type = input_type
        self.dic = cell.attrib.get('dic')
        self.default = cell.attrib.get('default')
        self.vld_type = cell.attrib.get('vld_type', '0')
        self.vld_param = self._get_vld_param()

    def __repr__(self):
        return ('<CellChecker input={input_type} dic={dic} default={default} '
                'vld_type={vld_type} vld_param={vld_param}>').format(
                    **self.__dict__)

    def _get_vld_param(self):
        if self.vld_type in ('1', '4'):
            return self._cell.attrib.get('vld')
        elif self.vld_type == '2':
            start, end = self._cell.attrib.get('vld').split('-')
            return list(range(int(start), int(end) + 1))
        elif self.vld_type == '3':
            return self._cell.attrib.get('vld').split(',')
        elif self.vld_type == '5':
            attr, coords = self._cell.attrib.get('vld').split('=#')
            return (attr, coords.split(','))

    def check(self, cell, errors_list):
        pass


class ControlChecker:
    def __init__(self, control):
        self._control = control

        self.id = control.attrib['id']
        self.name = control.attrib['name']
        self.rule = control.attrib['rule']
        self.condition = control.attrib['condition']

        self.tip = control.attrib.get('tip', '1')
        self.fault = control.attrib.get('fault', '0')
        self.period = control.attrib.get('periodClause')
        self.precision = control.attrib.get('precision', '2')

    def __repr__(self):
        return ('<ControlChecker id={id} name={name} rule={rule} '
                'condition={condition} tip={tip} fault={fault} '
                'period={period} precision={precision}>').format(
                    **self.__dict__)

    def check(self, data, errors_list):
        if not self._check_period():
            return
        if not self._check_condition(data):
            return

        rule_checks = self._check_rule(data)
        if len(rule_checks) != 0:
            self._fmt_error(rule_checks, errors_list)
            return

    def _fmt_error(self, check_list, errors_list):
        template = '{} {}; слева {} {} справа {} разница {}'
        for check in check_list:
            if isinstance(check, str):
                errors_list.append('{} {}; {}'.format(self.id,
                                                      self.name,
                                                      check))
            else:
                errors_list.append(template.format(self.id,
                                                   self.name,
                                                   check['left'],
                                                   check['operator'],
                                                   check['right'],
                                                   check['delta']))

    def _check_period(self):
        return True

    def _check_condition(self, data):
        if not self.condition:
            return True

        condition = control_parser.parse(self.condition)
        if condition is None:
            raise ValidationError(f'ошибка разбора условия {self.id}')

        for check in condition.check(data, precision=int(self.precision)):
            if len(check.controls) != 0:
                return False
        return True

    def _check_rule(self, data):
        res = []
        if not self.rule:
            return res

        rule = control_parser.parse(self.rule)
        if rule is None:
            raise ValidationError(f'ошибка разбора правила {self.id}')

        for check in rule.check(data, precision=int(self.precision)):
            res.extend(check.controls)
        return res
