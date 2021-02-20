from ..exceptions import (ValueBaseError, ValueNotNumberError, ValueBadFormat,
                          ValueNotInRangeError, ValueNotInListError,
                          ValueNotInDictError, ValueLengthError)


class ValueInspector:
    def __init__(self, params, catalogs):
        self._catalogs = catalogs

        self.catalog = params.get('dic')
        self.format = params.get('format')
        self.vld_type = params.get('vldType')
        self.vld_param = params.get('vld')

        self.format_funcs_map = {'N': self._is_num, 'C': self._is_chars}

    def __repr__(self):
        return ('<ValueInspector format={format} vld_type={vld_type} '
                'vld_param={vld_param}>').format(**self.__dict__)

    @classmethod
    def _is_num(self, value, limits):
        '''Проверка длины целой и дробной частей числового значения поля'''
        try:
            float(value)
        except ValueError:
            raise ValueNotNumberError()

        value_parts = tuple(len(n) for n in value.split('.'))
        if len(value_parts) == 1:
            i_part_len, f_part_len = value_parts[0], 0
        else:
            i_part_len, f_part_len = value_parts[0], value_parts[1]
        i_part_lim, f_part_lim = (int(n) for n in limits.split(','))

        if not (i_part_len <= i_part_lim and f_part_len <= f_part_lim):
            raise ValueBadFormat()

    @classmethod
    def _is_chars(self, value, limit):
        '''Проверка длины символьного значения поля'''
        if not len(value) <= int(limit):
            raise ValueLengthError()

    def check(self, coords, value):
        try:
            self.__check_format(value)
            self.__check_value(value)
        except ValueBaseError as ex:
            ex.update(coords)
            raise

    def __check_format(self, value):
        '''Разбор "формулы" проверки формата. Вызов метода проверки'''
        alias, args = self.format.strip(' )').split('(')
        format_check_func = self.format_funcs_map[alias]
        format_check_func(value, args)

    def __check_value(self, value):
        if self.vld_type == '1':
            self.__check_value_catalog(value)
        elif self.vld_type == '2':
            self.__check_value_range(value)
        elif self.vld_type == '3':
            self.__check_value_list(value)

    def __check_value_catalog(self, value):
        '''Проверка на вхождение в справочник'''
        if value not in self._catalogs[self.catalog]['ids']:
            raise ValueNotInDictError()

    def __check_value_range(self, value):
        '''Проверка на вхождение в диапазон'''
        value = float(value)
        start, end = (int(n) for n in self.vld_param.split('-'))
        if not (value >= start and value <= end):
            raise ValueNotInRangeError()

    def __check_value_list(self, value):
        '''Проверка на вхождение в список'''
        if value not in self.vld_param.split(','):
            raise ValueNotInListError()
