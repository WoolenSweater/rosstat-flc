from re import IGNORECASE, DOTALL
import ply.lex as lex

reserved = ['SUM', 'ABS', 'FLOOR', 'ROUND', 'ISNULL', 'NULLIF', 'COALESCE']
literals = [',', '+', '-', '/', '*', '(', ')', '{', '}']
tokens = ['CODE', 'LOGIC', 'NUM', 'COMP'] + reserved

reserved_map = {r.lower(): r for r in reserved}

t_ignore = ' |\r\t\f'

t_COMP = r'[><=]{1,2}'


def _range(rng):
    start, end = rng.split('-')
    return (str(i) for i in range(int(start), int(end) + 1))


def t_CODE(t):
    r'\[.+?\]'
    code = []
    for i in map(lambda i: i.strip(), t.value[1:-1].split(',')):
        if ('-' in i) and ('.' not in i):
            code.extend(_range(i))
        else:
            code.append(i)
    t.value = code
    return t


def t_NUM(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value)
    return t


def t_WORD(t):
    r'\w+'
    t.value = t.value.lower()
    t.type = reserved_map.get(t.value, 'LOGIC')
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)


lexer = lex.lex(reflags=IGNORECASE | DOTALL)
