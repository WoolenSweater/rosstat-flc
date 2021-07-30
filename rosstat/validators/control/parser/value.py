from math import floor


class Nullablefloat(float):
    def __new__(cls, val, *, is_null=False):
        return super().__new__(cls, val)

    def __init__(self, val, *, is_null=False):
        self.is_null = is_null

    def neg(self):
        return type(self)(-self)

    def abs(self):
        return self if self.is_null else type(self)(abs(self))

    def floor(self):
        return self if self.is_null else type(self)(floor(self))

    def round(self, n):
        return self if self.is_null else type(self)(round(self, n))

    def truncate(self, n):
        return self if self.is_null else type(self)(f'{self:.{int(n)}f}')

    def __add__(self, other):
        return self.__modify(super().__add__(other), other)

    def __sub__(self, other):
        return self.__modify(super().__sub__(other), other)

    def __mul__(self, other):
        return self.__modify(super().__mul__(other), other)

    def __truediv__(self, other):
        return self.__modify(super().__truediv__(other), other)

    def __modify(self, val, other):
        return type(self)(val, is_null=self.is_null & other.is_null)


def nullablefloat(val):
    try:
        return Nullablefloat(val, is_null=False)
    except (ValueError, TypeError):
        return Nullablefloat(0, is_null=True)
