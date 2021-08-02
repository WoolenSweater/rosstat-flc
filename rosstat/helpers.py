from collections import defaultdict


def str_int(v):
    return str(int(v)) if v.isdigit() else v


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
        try:
            return self[sec_code][row_code][spec_code]
        except KeyError:
            return {}


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


class MultiDict:
    def __init__(self):
        self.keys = []
        self.values = []

    def __iter__(self):
        return iter(sorted(set(self.keys), key=int))

    def __repr__(self):
        return '<MultiDict {}>'.format(list(zip(self.keys, self.values)))

    def add(self, key, value):
        self.keys.append(key)
        self.values.append(value)

    def getall(self, key):
        values = []
        for k, v in zip(self.keys, self.values):
            if k == key:
                values.append(v)
        return values
