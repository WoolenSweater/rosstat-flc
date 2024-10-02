from lark import Lark

from .entities import nptrue
from .functions import getmask, invert
from .transformer import ControlExpr

__all__ = [
    "nptrue",
    "getmask",
    "invert",
]

parser = Lark.open(
    "grammar.lark", parser="lalr", strict=True, cache=True, rel_to=__file__
)


def parse(control):
    return parser.parse(control.lower())


def eval(tree, type, report, mask, schema, control):
    return ControlExpr(type, report, mask, schema, control).transform(tree)
