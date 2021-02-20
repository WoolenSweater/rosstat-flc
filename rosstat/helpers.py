from collections import defaultdict


class SchemaFormats(dict):
    def _get_spec_code(self, sec_code, spec_idx):
        '''Возвращает из указаной секции ключ специфики по её индексу'''
        for code, idx in self[sec_code]['specs'].items():
            if idx == spec_idx:
                return code

    def get_spec_params(self, sec_code, row_code, spec_idx):
        '''Возвращает для указанной секции и строки словарь параметров,
           определяющий формат проверок для специфики с указанным кодом
        '''
        spec_code = self._get_spec_code(sec_code, str(spec_idx))
        return self[sec_code][row_code][spec_code]


class NestedDefaultdict(dict):
    def __init__(self, default_factory):
        self.default_factory = default_factory

    def __repr__(self):
        return '<nesteddefaultdict {}>'.format(super().__repr__())

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            self[key] = defaultdict(self.default_factory)
            return self[key]
