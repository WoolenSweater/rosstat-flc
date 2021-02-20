from ..exceptions import SpecBaseError, SpecNotInDictError, SpecValueError


class SpecInspector:
    def __init__(self, params, catalogs):
        self._catalogs = catalogs

        self.catalog = params.get('dic')
        self.vld_type = params.get('vldType')
        self.vld_param = params.get('vld')

    def __repr__(self):
        return ('<SpecInspector vld_type={vld_type} '
                'vld_param={vld_param}>').format(**self.__dict__)

    def check(self, coords, row, spec_idx, specs_map):
        try:
            self._check(row, spec_idx, specs_map)
        except SpecBaseError as ex:
            ex.update(coords, spec_idx)
            raise

    def _check(self, row, spec_idx, specs_map):
        if self.vld_type == '4':
            self.__check_value_catalog_add(row, spec_idx)
        elif self.vld_type == '5':
            self.__check_value_catalog_coord(row, spec_idx, specs_map)

    def __check_value_catalog_add(self, row, spec_idx):
        '''Проверка на вхождение в справочник'''
        if row.get_spec(spec_idx) not in self._catalogs[self.vld_param]['ids']:
            raise SpecNotInDictError()

    def __check_value_catalog_coord(self, row, spec_idx, specs_map):
        '''Проверка на вхождение в справочник и связь с главной спецификой'''
        catalog, coords = self.vld_param.split('=#')
        *_, col_code = coords.split(',')

        spec = row.get_spec(spec_idx)
        ctx_spec = row.get_spec(specs_map[col_code])

        try:
            ctx_catalog = self._catalogs[self.catalog]['full'][spec][catalog]
            if ctx_spec not in ctx_catalog:
                raise SpecValueError()
        except KeyError:
            raise SpecValueError()
