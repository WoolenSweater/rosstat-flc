from lark import Lark

from .evaluator import EvaluateExpr
from .functions import getmask, invert
from .tools import MarkedTree
from .visitor import VisitExpr

__all__ = [
    "getmask",
    "invert",
]

parser = Lark.open(
    "grammar.lark",
    parser="lalr",
    strict=True,
    cache=True,
    tree_class=MarkedTree,
    rel_to=__file__,
)


def parse(control):
    return parser.parse(control.lower())


def visit(tree, report, schema):
    visitor = VisitExpr(report, schema)
    return visitor.visit_topdown(tree)


def eval(tree, ctx, lazy, type, mask, control):
    transformer = EvaluateExpr(tree, ctx, lazy, type, mask, control)
    return transformer.transform(tree)
