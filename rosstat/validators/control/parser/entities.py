from numpy import asarray, full, ndarray
from numpy.ma import MaskedArray

from ..exceptions import (
    NoCoordinatesError,
    NonKeySpecificError,
    NoSectionError,
    SliceError,
)
from ..helpers import SPEC_KEYS, SpecType
from .dtype import nan, nfloat

star = "*"


class Codes(list):
    def __init__(self, iterable):
        list.__init__(self, iterable)
        self.set = set(self)

    def __contains__(self, item):
        return item in self.set

    def __repr__(self):
        return f"[{','.join(self or star)}]"


class Specs:
    def __init__(self, iterable=(), default=None, type=SpecType.CMN):
        self.default = default
        self.items = Codes(iterable)
        self.type = type

    def __bool__(self):
        return bool(self.items)

    def __contains__(self, spec):
        return spec in self.items

    def __repr__(self):
        return f"{repr(self.items)}[{self.type.name}][{self.default}]"


class Extendable:
    @classmethod
    def create(cls, *args):
        return cls(*cls._extend(*args))

    @classmethod
    def _flat(cls, tokens, collection, *params):
        for token in tokens:
            if cls._is_each(token):
                yield from collection
            elif cls._need_slice(token):
                yield from cls._slice(collection, *token)
            elif token := cls._special_case(collection, token, *params):
                yield token

    @staticmethod
    def _is_each(token):
        return token == "*"

    @staticmethod
    def _need_slice(token):
        return isinstance(token, list)

    @classmethod
    def _slice(cls, collection, start, end):
        try:
            start = collection.index(cls._fmt(start))
            end = collection.index(cls._fmt(end))

            return collection[start : end + 1]
        except ValueError:
            raise SliceError()


class Coords(Extendable):
    def __init__(self, section, rows, cols):
        self.section = section
        self.rows = rows
        self.cols = cols

        if not rows or not cols:
            raise NoCoordinatesError()

    def __repr__(self):
        return f"<Coords [{self.section}]{self.rows}{self.cols}>"

    def __iter__(self):
        for row in self.rows:
            yield self.section, row, self.cols

    @property
    def shape(self):
        return (len(self.rows), len(self.cols))

    @staticmethod
    def _fmt(token):
        return token.value.lstrip("0")

    @classmethod
    def _special_case(cls, collection, token):
        if (token := cls._fmt(token)) in collection:
            return token

    @classmethod
    def _extend(cls, section, rows, cols, dimension):
        sec = section.pop().lstrip("0")

        if (dim := dimension.get(sec)) is None:
            raise NoSectionError()

        yield sec
        yield Codes(cls._flat(rows, dim.rows))
        yield Codes(cls._flat(cols, dim.columns))


class SpecHolder(dict):
    def __repr__(self):
        return f"<SpecHolder {super().__repr__()}>"

    @classmethod
    def create(cls, coords, *args):
        return cls(cls._forrow(*coord, args) for coord in coords)

    @staticmethod
    def _forrow(sec, row, cols, args):
        return row, SpecList.create(sec, row, cols, *args)


class SpecList(Extendable):
    def __init__(self, s1, s2, s3):
        self.s1 = s1
        self.s2 = s2
        self.s3 = s3

    def __repr__(self):
        return f"<SpecList s1={self.s1} s2={self.s2} s3={self.s3}>"

    def __iter__(self):
        for key in SPEC_KEYS:
            yield key, getattr(self, key)

    @staticmethod
    def _fmt(token):
        return token.value

    @classmethod
    def _special_case(cls, collection, token, default, grv):
        if (token := cls._fmt(token)) != default and not grv:
            raise NonKeySpecificError()
        return token

    @classmethod
    def _extend(cls, sec, row, cols, specs, catalogs, formats):
        if specs is None:
            yield from cls._stubs()
        else:
            yield from cls._catalogs(sec, row, cols, specs, catalogs, formats)

    @staticmethod
    def _stubs():
        return (Specs() for i in range(3))

    @classmethod
    def _catalogs(cls, sec, row, cols, specs, catalogs, formats):
        sec = formats.get(sec)
        row = sec.get(row)

        for spec, key in zip(specs, SPEC_KEYS):
            if spec:
                col, stype = cls._get_col(sec, cols, key)
                ids, grv, default = cls._get_ids(row, col, catalogs)
                yield Specs(cls._flat(spec, ids, default, grv), default, stype)
            else:
                yield Specs()

    @staticmethod
    def _get_col(sec, cols, key):
        if key in sec["specs"]:
            return sec["specs"][key], SpecType.ROW
        return cols[0], SpecType.COL

    @staticmethod
    def _get_ids(row, col, catalogs):
        grv = row.get("grv")
        dic = row.get(col).get("dic")
        default = row.get(col).get("default", "").lower()
        return catalogs.get(dic, {}).get("ids", []), col in grv, default


class Element(ndarray):
    def __new__(cls, coords, specs, data):
        if data:
            obj = asarray(data, dtype=nfloat).view(cls)
        else:
            obj = full(coords.shape, nan, dtype=nfloat).view(cls)

        obj.coords = coords
        obj.specs = specs
        return obj

    @classmethod
    def create(cls, coords, specs, report):
        return cls(coords, specs, list(cls._read(coords, specs, report)))

    @staticmethod
    def _read(coords, specs, report):
        sec = report.get_section(coords.section)

        for row in sec.iter(coords.rows, specs):
            spec = specs.get(row.code)
            yield [nfloat(col) for col in row.iter(coords.cols, spec.s1)]

    def __array_finalize__(self, obj):
        if obj is not None:
            self.coords = getattr(obj, "coords", None)
            self.specs = getattr(obj, "specs", None)

    def __repr__(self):
        return f"<Element {self.coords!r} {self.specs!s} data={self}>"


class MaskedElement(MaskedArray):
    def __new__(cls, data, mask):
        obj = super().__new__(cls, data, mask=mask)
        obj.coords = getattr(data, "coords", None)
        obj.specs = getattr(data, "specs", None)
        return obj

    def __repr__(self):
        return (
            f"<MaskedElement {self.coords!r} {self.specs!s} "
            f"data={self} "
            f"mask={self.mask}>"
        )
