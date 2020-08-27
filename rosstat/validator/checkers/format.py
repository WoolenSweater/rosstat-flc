from ..exceptions import (OutOfAdditionDict, OutOfList, OutOfRange, OutOfDict,
                          InvalidStrLength, InvalidNumFormat, NotNumericValue)


class FormatChecker:
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
        return ('<FormatChecker row={row_type} input={input_type} '
                'format={format} vld_type={vld_type} '
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
        if not len(value) <= limit:
            raise InvalidStrLength()

    def check(self, cell, errors_list):
        '''Метод вызова проверки формата значения'''
        self._check_format(cell)
        self._check_value(cell)

    def _check_format(self, cell):
        '''Разбор "формулы" проверки формата. Вызов метода проверки'''
        alias, args = self.format.strip(' )').split('(')
        format_check_func = self.format_funcs_map[alias]
        format_check_func(cell, args)

    def _check_value(self, cell):
        '''Определение и вызов метода проверки по типу'''
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
        '''Проверка на вхождение в справочник'''
        if cell not in self._dics[self.dic]:
            raise OutOfDict()

    def __check_value_range(self, cell):
        '''Проверка на вхождение в диапазон'''
        cell = float(cell)
        start, end = (int(n) for n in self.vld_param.split('-'))
        if not (cell >= start and cell <= end):
            raise OutOfRange()

    def __check_value_list(self, cell):
        '''Проверка на вхождение в список'''
        if cell not in self.vld_param.split(','):
            raise OutOfList()

    def __check_value_dic_add(self, cell):
        '''Проверка на вхождение в справочник приложение'''
        if cell not in self._dics[self.vld_param]:
            raise OutOfAdditionDict()

    def __check_value_coord(self, cell):
        return  # пока не ясно как это првоеряется
        attr, coords = self.vld_param.split('=#')
        s_idx, r_idx, c_idx = coords.split(',')
