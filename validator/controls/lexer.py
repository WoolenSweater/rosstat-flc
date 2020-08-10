from re import IGNORECASE
import ply.lex as lex
from ply.lex import TOKEN

tokens = ('COMMA', 'PLUS', 'MINUS', 'MULTIPLY', 'DIVIDE', 'LPAREN', 'RPAREN',
          'ELEM_START', 'ELEM_END', 'CODE', 'SPEC', 'SUM', 'ABS', 'FLOOR',
          'ROUND', 'ISNULL', 'NULLIF', 'COALESCE', 'LOGIC', 'NUM', 'COMP')

states = (('elem', 'exclusive'),)

t_ignore = ' \r\t\f'
t_elem_ignore = ' \r\t\f'

t_COMMA = r','
t_PLUS = r'\+'
t_MINUS = r'-'
t_DIVIDE = r'/'
t_MULTIPLY = r'\*'
t_LPAREN = r'\('
t_RPAREN = r'\)'

t_LOGIC = r'and|or'
t_COMP = r'\|<\||\|<=\||\|=\||\|>=\||\|>\||\|<>\|'

t_SUM = r'SUM'
t_ABS = r'abs'
t_FLOOR = r'floor'
t_ROUND = r'round'
t_ISNULL = r'isnull'
t_NULLIF = r'nullif'
t_COALESCE = r'coalesce'


@TOKEN(r'{')
def t_ANY_ELEM_START(t):
    if t.lexer.current_state() != 'elem':
        t.lexer.push_state('elem')
        return t


@TOKEN(r'}')
def t_ANY_ELEM_END(t):
    if t.lexer.current_state() == 'elem':
        t.lexer.pop_state()
        return t


@TOKEN(r'\[\d+\..+?\]')
def t_elem_SPEC(t):
    t.value = [t.value[1:-1]]
    return t


def _range(rng):
    _from, _to = rng.split('-')
    return list(range(int(_from), int(_to) + 1))


@TOKEN(r'\[[\d\s\*,-]+\]')
def t_elem_CODE(t):
    code = []
    for i in t.value[1:-1].split(','):
        if i.isdigit():
            code.append(int(i))
        elif '-' in i:
            code.extend(_range(i))
        else:
            code.append(i)
    t.value = code
    return t


@TOKEN(r'\d+')
def t_NUM(t):
    t.value = float(t.value)
    return t


@TOKEN(r'\n+')
def t_newline(t):
    t.lexer.lineno += len(t.value)


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


def t_elem_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


lexer = lex.lex(reflags=IGNORECASE)
