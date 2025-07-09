from lark.visitors import Visitor, v_args

from .dtype import nfloat
from .entities import (
    Coords,
    Element,
    SpecHolder,
)
from .tools import Context, Transformer, pop


class ElementBuilder(Transformer):
    def __init__(self, report, schema):
        self._report = report

        self._formats = schema.formats
        self._catalogs = schema.catalogs
        self._dimension = schema.dimension

    code = pop
    ident = pop
    all = pop

    def num(self, children):
        return nfloat(pop(children))

    @v_args(inline=True)
    def element(self, section, rows, cols, specs=None):
        coords = Coords.create(section, rows, cols, self._dimension)
        specs = SpecHolder.create(coords, specs, self._catalogs, self._formats)
        return Element.create(coords, specs, self._report)


class VisitExpr(Visitor):
    def __init__(self, report, schema):
        self._lazy = True

        self._ctx = Context()
        self._builder = ElementBuilder(report, schema)

    def visit_topdown(self, tree):
        super().visit_topdown(tree)
        return self._ctx, self._lazy

    def bool_op(self, tree):
        if self._lazy is True and tree.children[0] == "or":
            self._lazy = False

    def params(self, tree):
        for subtree in tree.find_data("num"):
            subtree.contextual = False

    def num(self, tree):
        if tree.contextual:
            tree.children = [self._ctx.add(self._builder.transform(tree))]
        else:
            tree.children = [self._builder.transform(tree)]

    def element(self, tree):
        tree.children = [self._ctx.add(self._builder.transform(tree))]
