import operator

from numpy import atleast_1d, floor, frompyfunc, place, round, sum, trunc

from .dtype import nan, nfloat

# -- service --

innerarray = operator.itemgetter(0)
isnan = frompyfunc(lambda item: item.isnan(), 1, 1)

# -- user --


def round_(array, decimals, mode=0):
    if mode:
        return trunc(array)
    else:
        return round(array, decimals=decimals)


def sum_(array, ctx=None):
    if array.size == 0:
        return nan
    elif isinstance(ctx, nfloat | None):
        return sum(array)
    elif array.coords.rows == ctx.coords.rows:
        return sum(array, axis=1, keepdims=True)
    elif array.coords.cols == ctx.coords.cols:
        return sum(array, axis=0, keepdims=True)

def coalesce_(*arrays):
    return next(filter(lambda array: not isnan(array).any(), arrays), nan)


def nullif_(array1, array2):
    return nan if array1 == array2 else array1


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
