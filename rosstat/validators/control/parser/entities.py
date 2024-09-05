from numpy import asarray, ndarray

from .dtype import nfloat


class All(str):
    def __repr__(self):
        return "All"


class Specs:
    def __init__(self, s1=None, s2=None, s3=None):
        self.s1 = s1 or []
        self.s2 = s2 or []
        self.s3 = s3 or []

    def __repr__(self):
        return f"<Specs {self.s1}{self.s2}{self.s3}>"


class Coords:
    def __init__(self, section, rows, cols):
        self.section = section
        self.rows = rows
        self.cols = cols

    def __repr__(self):
        return f"<Coords [{self.section}]{self.rows}{self.cols}>"


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
