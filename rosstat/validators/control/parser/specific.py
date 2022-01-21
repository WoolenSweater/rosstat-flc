class Specific:
    def __init__(self, key, specs):
        self._key = key
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
    def key(self):
        return self._key

    @property
    def default(self):
        return self._default

    def need_expand(self):
        return self._specs not in ({None}, {'*'})

    def expand(self, sec_code, row_code, params):
        '''Основной метод подготовки спефик. Получение формата,
           каталога и развертывание.
        '''
        formats = self.__get_spec_formats(params.formats, sec_code, row_code)
        catalog = self.__get_spec_catalog(params.catalogs, formats)

        self._default = formats.get('default')
        self._specs = set(self._expand(catalog))

    def __get_spec_formats(self, formats, sec_code, row_code):
        '''Определяем параметры для специфики указанной строки, раздела'''
        return formats.get_spec_params(sec_code, row_code, self.key)

    def __get_spec_catalog(self, catalogs, params):
        '''Выбираем список специфик по имени справочника из параметров'''
        return catalogs.get(params.get('dic'), {}).get('ids', [])

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
