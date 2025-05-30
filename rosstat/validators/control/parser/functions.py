import operator

from numpy import (
    array_equal,
    atleast_1d,
    floor,
    frompyfunc,
    invert,
    logical_xor,
    ma,
    place,
    sum,
    trunc,
)

from .dtype import nan, nfloat
from .entities import MaskedElement

# -- service --

invert = invert
getmask = ma.getmask
cover = MaskedElement
xor = logical_xor
innerarray = operator.itemgetter(0)
isnan = frompyfunc(lambda item: item.isnan(), 1, 1)
around = frompyfunc(lambda item, decimals: round(item, decimals), 2, 1)

# -- user --


def round_(array, decimals, mode=0):
    if mode:
        return trunc(array, atleast_1d(array))
    else:
        return around(array, decimals)


def sum_(array, ctx=None):
    if array.size == 1:
        return array
    elif isinstance(ctx, nfloat | None):
        return sum(array)
    elif array.coords.cols == getattr(ctx.coords, "cols", None):
        return sum(array, axis=0, keepdims=True)
    elif array.coords.rows == getattr(ctx.coords, "rows", None):
        return sum(array, axis=1, keepdims=True)
    else:
        return sum(array)


def coalesce_(*arrays):
    return next(filter(lambda array: not isnan(array).any(), arrays), nan)


def nullif_(array1, array2):
    return nan if array_equal(array1, array2) else array1


def floor_(array):
    return floor(array)


def isnull_(array, val):
    place(array := atleast_1d(array), isnan(array), nfloat(val))
    return array


FUNCTION_MAP = {
    "<": operator.lt,
    "<=": operator.le,
    "=": operator.eq,
    ">": operator.gt,
    ">=": operator.ge,
    "<>": operator.ne,
    "and": operator.and_,
    "or": operator.or_,
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "abs": operator.abs,
    "floor": floor_,
    "round": round_,
    "isnull": isnull_,
    "nullif": nullif_,
    "coalesce": coalesce_,
}
