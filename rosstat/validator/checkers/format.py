from ..exceptions import (OutOfAdditionDict, OutOfList, OutOfRange, OutOfDict,
                          InvalidStrLength, InvalidNumFormat, NotNumericValue,
                          OutOfAdditionDictCoord)


class FormatChecker:
    def __init__(self, cell, dics):
        self._dics = dics

        self.dic = cell.attrib.get('dic')
        self.format = cell.attrib.get('format')
        self.vld_type = cell.attrib.get('vldType')
        self.vld_param = cell.attrib.get('vld')

        self.format_funcs_map = {'N': self._is_num, 'C': self._is_chars}

    def __repr__(self):
        return ('<FormatChecker format={format} vld_type={vld_type} '
                'vld_param={vld_param}>').format(**self.__dict__)

    @classmethod
    def _is_num(self, value, limits):
        '''Проверка длины целой и дробной частей числового значения поля'''
        try:
            float(value)
        except ValueError:
            raise NotNumericValue()

        value_parts = tuple(len(n) for n in value.split('.'))
        if len(value_parts) == 1:
            i_part_len, f_part_len = value_parts[0], 0
        else:
            i_part_len, f_part_len = value_parts[0], value_parts[1]
        i_part_lim, f_part_lim = (int(n) for n in limits.split(','))

        if not (i_part_len <= i_part_lim and f_part_len <= f_part_lim):
            raise InvalidNumFormat()

    @classmethod
    def _is_chars(self, value, limit):
        '''Проверка длины символьного значения поля'''
        if not len(value) <= int(limit):
            raise InvalidStrLength()

    def check(self, obj, spec=None, specs_map=None):
        if isinstance(obj, str):
            self._check_cell(obj)
        else:
            self._check_row(obj, spec, specs_map)

    def _check_cell(self, cell):
        '''Метод проверки значения'''
        self.__check_format(cell)
        if self.vld_type == '1':
            self.__check_value_dic(cell)
        elif self.vld_type == '2':
            self.__check_value_range(cell)
        elif self.vld_type == '3':
            self.__check_value_list(cell)

    def _check_row(self, row, spec, specs_map):
        '''Метод проверки специфик строки'''
        if self.vld_type == '4':
            self.__check_value_dic_add(row, spec)
        elif self.vld_type == '5':
            self.__check_value_dic_coord(row, spec, specs_map)

    def __check_format(self, value):
        '''Разбор "формулы" проверки формата. Вызов метода проверки'''
        alias, args = self.format.strip(' )').split('(')
        format_check_func = self.format_funcs_map[alias]
        format_check_func(value, args)

    def __check_value_dic(self, value):
        '''Проверка на вхождение в справочник'''
        if value not in self._dics[self.dic]:
            raise OutOfDict()

    def __check_value_range(self, value):
        '''Проверка на вхождение в диапазон'''
        value = float(value)
        start, end = (int(n) for n in self.vld_param.split('-'))
        if not (value >= start and value <= end):
            raise OutOfRange()

    def __check_value_list(self, value):
        '''Проверка на вхождение в список'''
        if value not in self.vld_param.split(','):
            raise OutOfList()

    def __check_value_dic_add(self, row, spec):
        '''Проверка на вхождение в справочник'''
        if getattr(row, spec) not in self._dics[self.vld_param]:
            raise OutOfAdditionDict()

    def __check_value_dic_coord(self, row, spec, specs_map):
        '''Проверка на вхождение в справочник и связь с главной спецификой'''
        dic, coords = self.vld_param.split('=#')
        *_, c_idx = coords.split(',')
        spec_value = getattr(row, spec)
        ctx_spec_value = getattr(row, specs_map[c_idx])

        try:
            if ctx_spec_value not in self._dics[self.dic][spec_value][dic]:
                raise OutOfAdditionDictCoord()
        except KeyError:
            raise OutOfAdditionDictCoord()
