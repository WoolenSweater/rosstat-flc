import operator
from math import isnan

from numpy import False_, True_

NPBOOL = {False: False_, True: True_}


def coerce(func):
    def wrapper(cls, value):
        if isinstance(value, type(cls)):
            return func(cls, value)
        elif isinstance(value, (int, float, str)):
            return func(cls, type(cls)(value))
        return NotImplemented

    return wrapper


class nfloat:
    def __init__(self, value):
        self.value = float(value)

    def __repr__(self):
        return f"n{repr(self.value)}"

    def __str__(self):
        return str(self.value)

    def __bool__(self):
        return bool(self.value)

    def __index__(self):
        return int(self.value)

    def __float__(self):
        return self.value

    def __neg__(self):
        self.value = -self.value
        return self

    def __abs__(self):
        self.value = abs(self.value)
        return self

    def isnan(self):
        return isnan(self.value)

    def view(self, cls):
        return cls(self)

    def rint(self):
        return self if self.isnan() else nfloat(round(self.value))

    def _cmp(self, func, other):
        if self.isnan() and other.isnan():
            return NPBOOL[True]

        sv = 0 if self.isnan() else self.value
        ov = 0 if other.isnan() else other.value

        return NPBOOL[func(sv, ov)]

    def _add(self, other):
        if not self.isnan():
            if not other.isnan():
                return nfloat(self.value + other.value)
            return self
        return other

    def _sub(self, other):
        if not self.isnan():
            if not other.isnan():
                return nfloat(self.value - other.value)
            return self
        return -other

    def _mul(self, other):
        if not self.isnan() and not other.isnan():
            return nfloat(self.value * other.value)
        return nan

    def _truediv(self, other):
        if not self.isnan():
            if not other.isnan() and other.value != 0:
                return nfloat(self.value / other.value)
        elif not other.isnan():
            return nfloat(0)
        return nan

    @coerce
    def __gt__(self, other):
        return self._cmp(operator.gt, other)

    @coerce
    def __ge__(self, other):
        return self._cmp(operator.ge, other)

    @coerce
    def __eq__(self, other):
        return self._cmp(operator.eq, other)

    @coerce
    def __ne__(self, other):
        return self._cmp(operator.ne, other)

    @coerce
    def __le__(self, other):
        return self._cmp(operator.le, other)

    @coerce
    def __lt__(self, other):
        return self._cmp(operator.lt, other)

    @coerce
    def __add__(self, other):
        return self._add(other)

    @coerce
    def __sub__(self, other):
        return self._sub(other)

    @coerce
    def __mul__(self, other):
        return self._mul(other)

    @coerce
    def __truediv__(self, other):
        return self._truediv(other)

    @coerce
    def __radd__(self, other):
        return other._add(self)

    @coerce
    def __rsub__(self, other):
        return other._sub(self)

    @coerce
    def __rmul__(self, other):
        return other._mul(self)

    @coerce
    def __rtruediv__(self, other):
        return other._truediv(self)


nan = nfloat("nan")
