from numpy import asarray, ndarray

from .dtype import nfloat


class Codes(list):
    def __repr__(self):
        return f"[{','.join(self or "*")}]"


class Extendable:
    @classmethod
    def create(cls, *args):
        return cls(*cls._extend(*args))

    @classmethod
    def _flatten(cls, tokens, collection, strip=False):
        for token in tokens:
            if cls._is_each(token):
                yield from collection
            elif cls._need_slice(token):
                yield from cls._slice(collection, *cls._fmt(strip, *token))
            else:
                yield from cls._fmt(strip, token)

    @staticmethod
    def _is_each(token):
        return token == "*"

    @staticmethod
    def _need_slice(token):
        return isinstance(token, list)

    @staticmethod
    def _fmt(strip, *tokens):
        for token in tokens:
            yield token.value.lstrip("0") if strip else token.value

    @staticmethod
    def _slice(collection, start, end):
        return collection[collection.index(start) : collection.index(end) + 1]


class Coords(Extendable):
    def __init__(self, section, rows, cols):
        self.section = section
        self.rows = rows
        self.cols = cols

    def __repr__(self):
        return f"<Coords [{self.section}]{self.rows}{self.cols}>"

    def __iter__(self):
        for row in self.rows:
            yield self.section, row

    @classmethod
    def _extend(cls, section, rows, cols, dimension):
        sec = section.pop().lstrip("0")
        dim = dimension.get(sec)

        yield sec
        yield Codes(cls._flatten(rows, dim.rows, strip=True))
        yield Codes(cls._flatten(cols, dim.columns, strip=False))


class Specs(dict):
    def __repr__(self):
        return f"<Specs {super().__repr__()}>"

    @classmethod
    def create(cls, coords, *args):
        return cls((row, Spec.create(sec, row, *args)) for sec, row in coords)


class Spec(Extendable):
    def __init__(self, s1, s2, s3):
        self.s1 = s1
        self.s2 = s2
        self.s3 = s3

    def __repr__(self):
        return f"<Spec {self.s1}{self.s2}{self.s3}>"

    def __iter__(self):
        for key in ("s1", "s2", "s3"):
            yield key, getattr(self, key)

    @classmethod
    def _extend(cls, sec, row, specs, catalogs, formats):
        if specs is None:
            yield from cls._stubs()
        else:
            yield from cls._catalogs(sec, row, specs, catalogs, formats)

    @staticmethod
    def _stubs():
        return (Codes() for i in range(3))

    @classmethod
    def _catalogs(cls, sec, row, specs, catalogs, formats):
        collection = cls._get_collections(sec, row, catalogs, formats)
        for i, spec in enumerate(specs):
            if spec:
                yield Codes(cls._flatten(spec, collection[i]))
            else:
                yield Codes()

    @staticmethod
    def _get_collections(sec, row, catalogs, formats):
        sec = formats.get(sec)
        row = sec.get(row)

        dics = (row.get(col).get("dic") for col in sec.get("specs").values())

        return [catalogs.get(dic, {}).get("ids", []) for dic in dics]


class Element(ndarray):
    def __new__(cls, coords, specs, values):
        obj = asarray(values, dtype=nfloat).view(cls)
        obj.coords = coords
        obj.specs = specs
        return obj

    def __array_finalize__(self, obj):
        if obj is not None:
            self.coords = getattr(obj, "coords", None)
            self.specs = getattr(obj, "specs", None)

    def __repr__(self):
        return f"<Element {self.coords!r} {self.specs!s} values={self}>"
