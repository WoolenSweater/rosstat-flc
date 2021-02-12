from ..exceptions import SpecBaseError, SpecNotInDictError, SpecValueError


class SpecInspector:
    def __init__(self, node, schema_dics):
        self._schema_dics = schema_dics

        self.dic = node.attrib.get('dic')
        self.vld_type = node.attrib.get('vldType')
        self.vld_param = node.attrib.get('vld')

    def __repr__(self):
        return ('<SpecInspector vld_type={vld_type} '
                'vld_param={vld_param}>').format(**self.__dict__)

    def check(self, coords, row, spec, specs_map):
        try:
            self._check(row, spec, specs_map)
        except SpecBaseError as ex:
            ex.update(coords, spec)
            raise

    def _check(self, row, spec, specs_map):
        if self.vld_type == '4':
            self.__check_value_dic_add(row, spec)
        elif self.vld_type == '5':
            self.__check_value_dic_coord(row, spec, specs_map)

    def __check_value_dic_add(self, row, spec):
        '''Проверка на вхождение в справочник'''
        if getattr(row, spec) not in self._schema_dics[self.vld_param]:
            raise SpecNotInDictError()

    def __check_value_dic_coord(self, row, spec, specs_map):
        '''Проверка на вхождение в справочник и связь с главной спецификой'''
        dic, coords = self.vld_param.split('=#')
        *_, col_code = coords.split(',')

        spec_value = getattr(row, spec)
        ctx_spec_value = getattr(row, specs_map[col_code])

        try:
            ctx_dic = self._schema_dics[self.dic][spec_value][dic]
            if ctx_spec_value not in ctx_dic:
                raise SpecValueError()
        except KeyError:
            raise SpecValueError()
