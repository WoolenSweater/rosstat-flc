class ValueInspector:
    def __init__(self, node, schema_dics):
        self._schema_dics = schema_dics

        self.dic = node.attrib.get('dic')
        self.format = node.attrib.get('format')
        self.vld_type = node.attrib.get('vldType')
        self.vld_param = node.attrib.get('vld')

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
            raise ValueError('Значение не является числом')

        value_parts = tuple(len(n) for n in value.split('.'))
        if len(value_parts) == 1:
            i_part_len, f_part_len = value_parts[0], 0
        else:
            i_part_len, f_part_len = value_parts[0], value_parts[1]
        i_part_lim, f_part_lim = (int(n) for n in limits.split(','))

        if not (i_part_len <= i_part_lim and f_part_len <= f_part_lim):
            raise ValueError('Число не соответствует формату')

    @classmethod
    def _is_chars(self, value, limit):
        '''Проверка длины символьного значения поля'''
        if not len(value) <= int(limit):
            raise ValueError('Длина строки больше допустимого')

    def check(self, value):
        try:
            self.__check_format(value)
        except ValueError as ex:
            return str(ex)
        else:
            return self.__check_value(value)

    def __check_format(self, value):
        '''Разбор "формулы" проверки формата. Вызов метода проверки'''
        alias, args = self.format.strip(' )').split('(')
        format_check_func = self.format_funcs_map[alias]
        format_check_func(value, args)

    def __check_value(self, value):
        if self.vld_type == '1':
            return self.__check_value_dic(value)
        elif self.vld_type == '2':
            return self.__check_value_range(value)
        elif self.vld_type == '3':
            return self.__check_value_list(value)

    def __check_value_dic(self, value):
        '''Проверка на вхождение в справочник'''
        if value not in self._schema_dics[self.dic]:
            return 'Значение не существует в справочнике'

    def __check_value_range(self, value):
        '''Проверка на вхождение в диапазон'''
        value = float(value)
        start, end = (int(n) for n in self.vld_param.split('-'))
        if not (value >= start and value <= end):
            return 'Значение не входит в диапазон допустимых'

    def __check_value_list(self, value):
        '''Проверка на вхождение в список'''
        if value not in self.vld_param.split(','):
            return 'Значение не входит в список допустимых'
