class Specific:
    def __init__(self, specs):
        self._specs = set(specs)
        self._default = None

    def __repr__(self):
        return "<Specific {} default={}>".format(self._specs, self._default)

    def __iter__(self):
        return iter(self._specs)

    def __contains__(self, spec):
        return spec in self._specs

    def __eq__(self, other):
        return self._specs == other

    @property
    def default(self):
        return self._default

    def need_expand(self):
        return self._specs not in ({None}, {'*'})

    def params(self, params):
        self._default = params.get('default')

    def expand(self, dic):
        self._specs = set(self._expand(dic))

    def _expand(self, dic):
        '''Перебираем специфики. Простые специфики сразу возвращаем. Если
           имеем диапазон, определяем индекс начальной и конечной специфик
           из списка-справочника, итерируемся по определенному диапазону,
           возвращая соответствующие специфики из списка-справочника
        '''
        for spec in self._specs:
            if '-' in spec:
                start, end = spec.split('-')
                for i in range(dic.index(start.strip()),
                               dic.index(end.strip()) + 1):
                    yield dic[i]
            else:
                yield spec
