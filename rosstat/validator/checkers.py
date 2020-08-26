from .controls.period import PeriodClause
from .controls import parser as control_parser
from .exceptions import ValidationError, InvalidValue


class CellChecker:
    def __init__(self, cell, dics, input_type, row_type=None):
        self._cell = cell
        self._dics = dics

        self.row_type = row_type
        self.input_type = input_type

        self.dic = cell.attrib.get('dic')
        self.format = cell.attrib.get('format')
        self.vld_type = cell.attrib.get('vldType')
        self.vld_param = cell.attrib.get('vld')

        self.format_funcs_map = {'N': self._is_num, 'C': self._is_chars}

    def __repr__(self):
        return ('<CellChecker row={row_type} input={input_type} '
                'format={format} vld_type={vld_type} '
                'vld_param={vld_param}>').format(**self.__dict__)

    @classmethod
    def _is_num(self, value, limits):
        try:
            _ = float(value)
        except ValueError:
            raise InvalidValue('Значение не является числом')

        value_parts = tuple(len(n) for n in value.split('.'))
        if len(value_parts) == 1:
            i_part_len, f_part_len = value_parts[0], 0
        else:
            i_part_len, f_part_len = value_parts[0], value_parts[1]
        i_part_lim, f_part_lim = (int(n) for n in limits.split(','))

        if not (i_part_len <= i_part_lim and f_part_len <= f_part_lim):
            print(i_part_len, f_part_len, i_part_lim, f_part_lim)
            raise InvalidValue('Число не соответствует формату')

    @classmethod
    def _is_chars(self, value, limit):
        if not len(value) <= limit:
            raise InvalidValue('Длина строки больше допустимого')

    def check(self, cell):
        check_list = ('format', 'value')
        for name in check_list:
            getattr(self, f'_check_{name}')(cell)

    def _check_format(self, cell):
        alias, args = self.format.strip(' )').split('(')
        format_check_func = self.format_funcs_map[alias]
        format_check_func(cell, args)

    def _check_value(self, cell):
        if self.vld_type == '1':
            self.__check_value_dic(cell)
        elif self.vld_type == '2':
            self.__check_value_range(cell)
        elif self.vld_type == '3':
            self.__check_value_list(cell)
        elif self.vld_type == '4':
            self.__check_value_dic_add(cell)
        elif self.vld_type == '5':
            self.__check_value_dic_coord(cell)

    def __check_value_dic(self, cell):
        if cell not in self._dics[self.dic]:
            raise InvalidValue('Значение не существует в справочнике')

    def __check_value_range(self, cell):
        cell = float(cell)
        start, end = (int(n) for n in self.vld_param.split('-'))
        if not (cell >= start and cell <= end):
            raise InvalidValue('Значение не входит в диапазон допустимых')

    def __check_value_list(self, cell):
        if cell not in self.vld_param.split(','):
            raise InvalidValue('Значение не входит в список допустимых')

    def __check_value_dic_add(self, cell):
        if cell not in self._dics[self.vld_param]:
            raise InvalidValue('Значение не существует в '
                               'справочнике приложении')

    def __check_value_coord(self, cell):
        return  # пока не ясно как это првоеряется
        attr, coords = self.vld_param.split('=#')
        s_idx, r_idx, c_idx = coords.split(',')


class ControlChecker:
    def __init__(self, control):
        self._control = control

        self.id = control.attrib['id']
        self.name = control.attrib['name']
        self.rule = control.attrib['rule']
        self.condition = control.attrib['condition']

        self.tip = control.attrib.get('tip', '1')
        self.fault = control.attrib.get('fault', '0')
        self.precision = control.attrib.get('precision', '2')

        self.period = PeriodClause(control, self.id)

    def __repr__(self):
        return ('<ControlChecker id={id} name={name} rule={rule} '
                'condition={condition} tip={tip} fault={fault} '
                'period={period} precision={precision}>').format(
                    **self.__dict__)

    def check(self, report, errors_list):
        if not self._check_period(report):
            return
        if not self._check_condition(report):
            return

        rule_checks = self._check_rule(report)
        if len(rule_checks) != 0:
            self._fmt_error(rule_checks, errors_list)

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

    def _check_period(self, report):
        return self.period.check(report)

    def _check_condition(self, report):
        if not self.condition:
            return True

        condition = control_parser.parse(self.condition)
        if condition is None:
            raise ValidationError(f'ошибка разбора условия {self.id}')

        for check in condition.check(report, precision=int(self.precision)):
            if len(check.controls) != 0:
                return False
        return True

    def _check_rule(self, report):
        res = []
        if not self.rule:
            return res

        rule = control_parser.parse(self.rule)
        if rule is None:
            raise ValidationError(f'ошибка разбора правила {self.id}')

        for check in rule.check(report, precision=int(self.precision)):
            res.extend(check.controls)
        return res
