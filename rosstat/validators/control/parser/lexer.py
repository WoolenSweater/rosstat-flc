from re import IGNORECASE
import ply.lex as lex
from ply.lex import TOKEN

tokens = ('COMMA', 'PLUS', 'MINUS', 'MULTIPLY', 'DIVIDE', 'LPAREN', 'RPAREN',
          'ELEM_START', 'ELEM_END', 'CODE', 'SUM', 'ABS', 'FLOOR', 'ROUND',
          'ISNULL', 'NULLIF', 'COALESCE', 'LOGIC', 'NUM', 'COMP')

t_ignore = ' \r\t\f'

t_COMMA = r','
t_PLUS = r'\+'
t_MINUS = r'-'
t_DIVIDE = r'/'
t_MULTIPLY = r'\*'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_ELEM_START = r'{?{'
t_ELEM_END = r'}?}'

t_LOGIC = r'and|or'
t_COMP = r'\|<\||\|<=\||\|=\||\|>=\||\|>\||\|<>\|'

t_SUM = r'SUM'
t_ABS = r'abs'
t_FLOOR = r'floor'
t_ROUND = r'round'
t_ISNULL = r'isnull'
t_NULLIF = r'nullif'
t_COALESCE = r'coalesce'


def _range(rng):
    _from, _to = rng.split('-')
    return [str(i) for i in range(int(_from), int(_to) + 1)]


@TOKEN(r'\[.+?\]')
def t_CODE(t):
    code = []
    for i in t.value[1:-1].split(','):
        if i.isdigit():
            code.append(i)
        elif '-' in i:
            code.extend(_range(i))
        else:
            code.append(i)
    t.value = code
    return t


@TOKEN(r'\d+(\.\d+)?')
def t_NUM(t):
    t.value = float(t.value)
    return t


@TOKEN(r'\n+')
def t_newline(t):
    t.lexer.lineno += len(t.value)


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


lexer = lex.lex(reflags=IGNORECASE)
