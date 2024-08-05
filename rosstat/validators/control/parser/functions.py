import operator

from numpy import around, nan_to_num, nanmin, nansum, trunc


def round_(array, decimals, mode=0):
    if mode:
        return trunc(array)
    else:
        return around(array, decimals=int(decimals))


def sum_(array, ctx):
    if isinstance(ctx, float):
        return nansum(array)
    elif array.coords.rows == ctx.coords.rows:
        return nansum(array, axis=1)
    elif array.coords.cols == ctx.coords.cols:
        return nansum(array, axis=0)
    else:
        return nansum(array)


def coalesce_(*arrays):
    return next(filter(arrays), None)


def nullif_(array1, array2):
    None if array1 == array2 else array1


def floor_(array):
    return nanmin(array)


def isnull_(array, nan):
    return nan_to_num(array, nan=nan)


innerarray = operator.itemgetter(0)


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
