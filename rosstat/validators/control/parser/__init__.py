from lark import Lark

from rosstat.validators.control.parser.transformer import ControlExpr

parser = Lark.open("grammar.lark", rel_to=__file__, strict=True, parser="lalr")


def parse(control):
    return parser.parse(control.lower())


def transform(tree, report, type, schema, control):
    return ControlExpr(report, type, schema, control).transform(tree)
