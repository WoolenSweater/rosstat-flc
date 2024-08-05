from lark import Lark

from rosstat.validators.control.parser.transformer import ControlExpr

parser = Lark.open("grammar.lark", rel_to=__file__, strict=True, parser="lalr")


def parse(control):
    return parser.parse(control.lower())


def transform(report, tree, params):
    return ControlExpr(report, params).transform(tree)
