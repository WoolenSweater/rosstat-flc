from numpy import True_, asarray, ndarray
from numpy.ma import MaskedArray

from ..exceptions import NoSectionError, TokenNotExist
from ..helpers import SPEC_KEYS, SpecType
from .dtype import nan, nfloat

nptrue = True_


class Codes(list):
    def __repr__(self):
        return f"[{','.join(self or "*")}]"


class Specs:
    def __init__(self, iterable=None, default=None, type=SpecType.CMN):
        self.default = default if default is None else default.lower()
        self.items = Codes() if iterable is None else Codes(iterable)
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
    def _flatten(cls, tokens, collection, spec=False, strip=False):
        for token in tokens:
            if cls._is_each(token):
                yield from collection
            elif cls._need_slice(token):
                yield from cls._slice(collection, *cls._fmt_two(strip, token))
            elif (token := cls._fmt(strip, token)) in collection or spec:
                yield token
            else:
                raise TokenNotExist()

    @staticmethod
    def _is_each(token):
        return token == "*"

    @staticmethod
    def _need_slice(token):
        return isinstance(token, list)

    @staticmethod
    def _fmt(strip, token):
        return token.value.lstrip("0") if strip else token.value

    @classmethod
    def _fmt_two(cls, strip, tokens):
        return (cls._fmt(strip, token) for token in tokens)

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
            yield self.section, row, self.cols

    @classmethod
    def _extend(cls, section, rows, cols, dimension):
        sec = section.pop().lstrip("0")

        if (dim := dimension.get(sec)) is None:
            raise NoSectionError()

        yield sec
        yield Codes(cls._flatten(rows, dim.rows, strip=True))
        yield Codes(cls._flatten(cols, dim.columns, strip=True))


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
                ids, default = cls._get_ids(row, col, catalogs)
                yield Specs(cls._flatten(spec, ids, spec=True), default, stype)
            else:
                yield Specs()

    @staticmethod
    def _get_col(sec, cols, key):
        if key in sec["specs"]:
            return sec["specs"][key], SpecType.ROW
        return cols[0], SpecType.COL

    @staticmethod
    def _get_ids(row, col, catalogs):
        dic = row.get(col).get("dic")
        default = row.get(col).get("default")
        return catalogs.get(dic, {}).get("ids", []), default


class Element(ndarray):
    def __new__(cls, coords, specs, data):
        obj = asarray(data or nan, dtype=nfloat).view(cls)
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
