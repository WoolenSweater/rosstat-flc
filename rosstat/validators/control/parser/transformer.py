from functools import partial

from lark import Transformer
from lark.visitors import v_args

from ..exceptions import ControlFault
from .dtype import nfloat
from .entities import (
    Coords,
    Element,
    Specs,
)
from .functions import (
    FUNCTION_MAP,
    innerarray,
    round_,
    sum_,
)


class ControlExpr(Transformer):
    def __init__(self, report, type, schema, control):
        super().__init__(visit_tokens=False)
        self._report = report
        self._type = type

        self._fault = control.fault
        self._formats = schema.formats
        self._catalogs = schema.catalogs
        self._dimension = schema.dimension

        self._round = partial(round_, decimals=control.precision)

    def __default__(self, data, children, meta):
        return children

    @staticmethod
    def _pass(array):
        return array

    @staticmethod
    def _pop(children):
        return children.pop()

    # ---

    def _call_partial(self, operand, ctx=None):
        if isinstance(operand, partial):
            if isinstance(ctx, partial):
                ctx = innerarray(ctx.args)
            return operand(ctx)
        return operand

    def _call(self, left, right, func):
        left = self._call_partial(left, right)
        right = self._call_partial(right, left)

        return func(left), func(right)

    def __exact_expr(self, left, op, right):
        left, right = self._call(left, right, self._pass)

        return FUNCTION_MAP.get(op)(left, right), left, right

    def __approx_expr(self, left, op, right):
        left, right = self._call(left, right, self._round)

        return FUNCTION_MAP.get(op)(left, right), left, right

    @v_args(inline=True)
    def _math_expr(self, left, op, right):
        result, left, right = self.__exact_expr(left, op, right)
        return result

    @v_args(inline=True)
    def _bool_expr(self, left, op, right):
        result, left, right = self.__exact_expr(left, op, right)
        if not result.all():
            raise ControlFault(op, left, right, 1)
        return result

    @v_args(inline=True)
    def _logic_expr(self, left, op, right):
        result, left, right = self.__approx_expr(left, op, right)
        if not result.all():
            if ((delta := abs(left - right)) >= self._fault).any():
                raise ControlFault(op, left, right, delta)
        return result

    # ---

    @v_args(inline=True)
    def function(self, func, params):
        return FUNCTION_MAP.get(func)(*map(self._call_partial, params))

    @v_args(inline=True)
    def sum(self, elem):
        return partial(sum_, elem)

    # ---

    add_op = _pop
    mul_op = _pop
    bool_op = _pop
    logic_op = _pop

    func_name = _pop

    code = _pop
    ident = _pop
    all = _pop

    math_term = _math_expr
    math_factor = _math_expr
    bool_expr = _bool_expr
    logic_expr = _logic_expr

    def num(self, children):
        return nfloat(self._pop(children))

    # ---

    @v_args(inline=True)
    def element(self, section, rows, cols, specs=None):
        coords = Coords.create(section, rows, cols, self._dimension)
        specs = Specs.create(coords, specs, self._catalogs, self._formats)

        return Element(coords, specs, list(self._read_report(coords, specs)))

    def _read_report(self, coords, specs):
        sec = self._report.get_section(coords.section)

        for row in sec.iter(coords.rows, specs):
            yield [nfloat(col) for col in row.iter(coords.cols)]
