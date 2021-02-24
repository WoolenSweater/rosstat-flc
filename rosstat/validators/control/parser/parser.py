import ply.yacc as yacc
from .lexer import tokens
from .elements import ElemLogic, ElemSelector, ElemList, Elem

precedence = (
    ('left', 'LOGIC'),
    ('left', 'COMP'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MULTIPLY', 'DIVIDE'),
    ('left', 'SUM', 'ABS'),
    ('right', 'UMINUS'),            # Unary minus operator
)

op_name = {
    '+': 'add',
    '-': 'sub',
    '*': 'mul',
    '/': 'truediv',
}


def p_elem_logic(p):
    '''elem : elem COMP elem
            | elem LOGIC elem'''
    p[0] = ElemLogic(p[1], p[2].strip('|'), p[3])


def p_elem_selector(p):
    '''elem : COALESCE elems
            | NULLIF elems'''
    p[0] = ElemSelector(p[1].lower(), p[2])


def p_elem_func(p):
    '''elem : ABS elem
            | SUM elem
            | FLOOR elem'''
    p[0] = p[2]
    p[0].add_func(p[1].lower(), None)


def p_elem_func_args(p):
    '''elem : ISNULL LPAREN elems RPAREN
            | ROUND LPAREN elems RPAREN'''
    p[0], *args = p[3]
    p[0].add_func(p[1].lower(), *args)


def p_elem_func_sum(p):
    '''elem : SUM LPAREN elem RPAREN'''
    p[0] = p[3]
    p[0].add_func(p[1].lower(), None)


def p_elem_math(p):
    '''elem : elem PLUS elem
            | elem MINUS elem
            | elem MULTIPLY elem
            | elem DIVIDE elem'''
    p[1].add_func(op_name[p[2]], p[3])
    p[0] = p[1]


def p_elem(p):
    '''elem : ELEM_START coords ELEM_END'''
    p[0] = ElemList(*p[2])


def p_num_elem(p):
    '''elem : NUM'''
    p[0] = Elem(p[1])


def p_coords(p):
    '''coords : CODE
              | coords CODE'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[2])
        p[0] = p[1]


def p_elem_group(p):
    '''elems : elem COMMA elem
             | elems COMMA elem'''
    if isinstance(p[1], list):
        p[1].append(p[3])
        p[0] = p[1]
    else:
        p[0] = [p[1], p[3]]


def p_ne_elem(p):
    '''elem : MINUS elem %prec UMINUS'''
    p[0] = -p[2]


def p_elem_in_parens(p):
    '''elem : LPAREN elem RPAREN
       elems : LPAREN elems RPAREN'''
    p[0] = p[2]


def p_error(p):
    print('Unexpected token:', p)


parser = yacc.yacc()
