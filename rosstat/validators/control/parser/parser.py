import ply.yacc as yacc
from .lexer import tokens
from .elements import ElemLogic, ElemSelector, ElemList, Elem

precedence = (
    ('left', 'LOGIC'),
    ('left', 'COMP'),
    ('left', '+', '-'),
    ('left', '*', '/'),
    ('left', ','),
    ('left', 'COALESCE', 'NULLIF', 'ISNULL', 'ROUND', 'SUM', 'ABS', 'FLOOR'),
    ('left', '(', ')'),
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
    p[0] = ElemLogic(p[1], p[2], p[3])


def p_elem_selector(p):
    '''elem : COALESCE elems
            | NULLIF elems'''
    p[0] = ElemSelector(p[1], p[2])


def p_elem_func(p):
    '''elem : ABS elem
            | SUM elem
            | FLOOR elem'''
    p[0] = p[2]
    p[0].add_func(p[1], None)


def p_elem_func_args(p):
    '''elem : ISNULL elems
            | ROUND elems'''
    p[0], *args = p[2]
    p[0].add_func(p[1], *args)


def p_elem_math(p):
    '''elem : elem '+' elem
            | elem '-' elem
            | elem '*' elem
            | elem '/' elem'''
    p[0] = p[1]
    p[0].add_func(op_name[p[2]], p[3])


def p_elem_num(p):
    '''elem : NUM'''
    p[0] = Elem(p[1])


def p_elem(p):
    '''elem : '{' coords '}' '''
    p[0] = ElemList(*p[2])


def p_coord(p):
    '''coords : CODE'''
    p[0] = [p[1]]


def p_coords(p):
    '''coords : coords CODE'''
    p[0] = p[1]
    p[0].append(p[2])


def p_elem_group(p):
    '''elems : elem ',' elem'''
    p[0] = [p[1], p[3]]


def p_elem_groups(p):
    '''elems : elems ',' elem'''
    p[0] = p[1]
    p[0].append(p[3])


def p_elem_ne(p):
    '''elem : '-' elem %prec UMINUS'''
    p[0] = -p[2]


def p_elem_parens(p):
    '''elem : '(' elem ')'
       elems : '(' elems ')' '''
    p[0] = p[2]


def p_error(p):
    print('Unexpected token:', p)


parser = yacc.yacc()
