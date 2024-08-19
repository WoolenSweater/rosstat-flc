from collections import defaultdict

SPEC_KEYS = ("s1", "s2", "s3")


def str_int(v):
    return str(int(v)) if v.isdigit() else v


class SchemaFormat(dict):
    def get_spec_params(self, sec_code, row_code, spec_key):
        """
        Возвращает для указанного раздела и строки словарь параметров,
        определяющий формат проверок для специфики с указанным кодом
        """
        col_code = self[sec_code]["specs"][spec_key]
        return self[sec_code][row_code].get(col_code, {})

    def add(self, sec_code, specs):
        """Добавляем раздел и идентификаторы специфик"""
        self[sec_code] = {"specs": specs}

    def has(self, sec_code, row_code):
        """Проверяем наличие формата для указанных раздела и строки"""
        try:
            return bool(self[sec_code][row_code])
        except KeyError:
            return False


class SchemaCatalog(dict):
    def set(self, term_id):
        """Установка термину пустого словаря сетов если ещё нет"""
        self.setdefault(term_id, defaultdict(set))

    def sort(self):
        """Сортировка идентификаторов терминов"""
        self["ids"] = sorted(self.keys())


class SchemaDimension:
    def __init__(self):
        self.rows = []
        self.columns = []

    def __repr__(self):
        return f"<SchemaDimension rows={self.rows} columns={self.columns}>"

    def add_row(self, row_code):
        """Добавление кода строки"""
        self.rows.append(row_code)

    def add_column(self, col_code):
        """Добавление кода колонки"""
        self.columns.append(col_code)


class MultiDict:
    def __init__(self):
        self.keys = []
        self.values = []

    def __iter__(self):
        return iter(sorted(set(self.keys), key=int))

    def __repr__(self):
        return "<MultiDict {}>".format(list(zip(self.keys, self.values)))

    def add(self, key, value):
        self.keys.append(key)
        self.values.append(value)

    def get(self, key):
        values = []
        for k, v in zip(self.keys, self.values):
            if k == key:
                values.append(v)
        return values

    def getall(self):
        return self.values
