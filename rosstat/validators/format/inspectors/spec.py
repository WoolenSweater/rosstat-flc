class SpecInspector:
    def __init__(self, node, schema_dics):
        self._schema_dics = schema_dics

        self.dic = node.attrib.get('dic')
        self.vld_type = node.attrib.get('vldType')
        self.vld_param = node.attrib.get('vld')

    def __repr__(self):
        return ('<SpecInspector vld_type={vld_type} '
                'vld_param={vld_param}>').format(**self.__dict__)

    def check(self, row, spec, specs_map):
        if self.vld_type == '4':
            return self.__check_value_dic_add(row, spec)
        elif self.vld_type == '5':
            return self.__check_value_dic_coord(row, spec, specs_map)

    def __check_value_dic_add(self, row, spec):
        '''Проверка на вхождение в справочник'''
        if getattr(row, spec) not in self._schema_dics[self.vld_param]:
            return 'Значение не существует в справочнике приложении'

    def __check_value_dic_coord(self, row, spec, specs_map):
        '''Проверка на вхождение в справочник и связь с главной спецификой'''
        dic, coords = self.vld_param.split('=#')
        *_, col_code = coords.split(',')

        spec_value = getattr(row, spec)
        ctx_spec_value = getattr(row, specs_map[col_code])

        try:
            ctx_dic = self._schema_dics[self.dic][spec_value][dic]
            if ctx_spec_value not in ctx_dic:
                return 'Недопустимое значение'
        except KeyError:
            return 'Недопустимое значение'
