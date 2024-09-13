from functools import partial

from lark import Transformer
from lark.visitors import v_args

from ..exceptions import ControlFault
from ..helpers import Formula
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
    xor,
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

        self._precision = partial(round_, decimals=control.precision)

    def __default__(self, data, children, meta):
        return children

    @property
    def _is_condition(self):
        return self._type == Formula.CONDITION

    @property
    def _has_fault(self):
        return self._fault > 0

    @staticmethod
    def _is_eq(op):
        return op in {"<=", "=", "<>", ">="}

    @staticmethod
    def _pop(children):
        return children.pop()

    # ---

    def _exec(self, op, *args):
        return FUNCTION_MAP.get(op)(*args)

    def _round(self, left, right):
        left = self._precision(left)
        right = self._precision(right)
        return left, right

    def _call_partial(self, operand, ctx=None):
        if isinstance(operand, partial):
            if isinstance(ctx, partial):
                ctx = innerarray(ctx.args)
            return operand(ctx)
        return operand

    def _call(self, left, right):
        left = self._call_partial(left, right)
        right = self._call_partial(right, left)
        return left, right

    @v_args(inline=True)
    def _math_expr(self, left, op, right):
        left, right = self._call(left, right)
        result = self._exec(op, left, right)
        return result

    @v_args(inline=True)
    def _bool_expr(self, left, op, right):
        left, right = self._call(left, right)
        result = self._exec(op, left, right)

        self._check(op, left, right, result, 1)

        return result

    @v_args(inline=True)
    def _logic_expr(self, left, op, right):
        left, right = self._call(left, right)
        left, right = self._round(left, right)
        result = self._exec(op, left, right)

        if self._is_condition:
            self._check(op, left, right, result, 1)
        elif self._has_fault and self._is_eq(op):
            self._check(op, left, right, *self._xor(result, abs(left - right)))
        else:
            self._check(op, left, right, result, abs(left - right))

        return result

    def _check(self, op, left, right, result, delta):
        if not result.all():
            raise ControlFault(op, left, right, delta)

    def _xor(self, array, delta):
        return xor(array, 0 < delta <= self._fault), delta

    # ---

    @v_args(inline=True)
    def function(self, func, params):
        return self._exec(func, *map(self._call_partial, params))

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
