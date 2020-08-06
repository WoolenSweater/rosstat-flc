import operator
from math import floor
from copy import deepcopy
from itertools import chain
from functools import reduce

operator_map = {
    '<': operator.lt,
    '<=': operator.le,
    '=': operator.eq,
    '>': operator.gt,
    '>=': operator.ge,
    '<>': operator.ne,
    'and': operator.and_,
    'or': operator.or_,
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
}


class Elem:
    def __init__(self, val, section=None, row=None, entry=None):
        self.section = section or ''
        self.row = set([row]) if row else set()
        self.entry = set([entry]) if entry else set()
        # Возможно стоит выпилить координаты из элементов
        # они не всегда информативны и могу даже сбить с толку

        self._controls = []

        self.bool = True
        self.val = None if val is None else float(val)

    def __add__(self, elem):
        return self.__modify(elem, operator.add)

    def __sub__(self, elem):
        return self.__modify(elem, operator.sub)

    def __mul__(self, elem):
        return self.__modify(elem, operator.mul)

    def __truediv__(self, elem):
        return self.__modify(elem, operator.truediv)

    def __neg__(self):
        self.val = -self.val
        return self

    def __repr__(self):
        return ('<Elem [{section}]{row_f}{entry_f} controls={_controls}: '
                '{val} {bool}>').format(**self.__dict__,
                                        row_f=list(self.row),
                                        entry_f=list(self.entry))

    def __fmt_fail_msg(self, l_elem, ctrl_name, op_name):
        if op_name in ('and', 'or'):
            l_val, r_val = l_elem.bool, self.bool
        else:
            l_val, r_val = l_elem.val, self.val

        return 'Условие "{}" не выполнено, [{}]{}{} {} {} [{}]{}{} {}'.format(
            ctrl_name, l_elem.section, sorted(list(l_elem.row)),
            sorted(list(l_elem.entry)), l_val, op_name, self.section,
            sorted(list(self.row)), sorted(list(self.entry)), r_val
        )

    def __modify(self, elem, op_func):
        self.row |= elem.row
        self.entry |= elem.entry
        self.val = op_func(self.val, elem.val)
        return self

    @property
    def controls(self):
        return self._controls

    def control_fail(self, l_elem, ctrl_name, op_name):
        self.bool = False
        self._controls.append(self.__fmt_fail_msg(l_elem, ctrl_name, op_name))

    def check(self, raw_data, ctx_elem, ctrl_name=None):
        return [self]

    def isnull(self, replace):
        '''Замена None на replace'''
        self.val = self.val or float(replace)

    def round(self, ndig, trunc=0):
        '''Округление/отсечение до ndig знаков'''
        if trunc > 0:
            self.val = float(f'{self.val:.{abs(ndig)}f}')
        else:
            self.val = round(self.val, ndig)

    def abs(self):
        '''Выполнение функции abs над значением'''
        self.val = abs(self.val)

    def floor(self):
        '''Выполнение функции floor над значением'''
        self.val = floor(self.val)


class ElemList:
    def __init__(self,
                 section=None, rows=None, entries=None,
                 s1=None, s2=None, s3=None):
        self.section = section[0] if section is not None else ''
        self.rows = rows or []
        self.entries = entries or []

        self.specs = [(1, None if s1 is None else s1[0]),
                      (2, None if s2 is None else s2[0]),
                      (3, None if s3 is None else s3[0])]

        self.rounded_off = False
        self.funcs = []
        self.elems = []

    def __repr__(self) -> str:
        return ('<ElemList [{section}]{rows}{entries} specs={specs} '
                'rounded_off={rounded_off} funcs={funcs} '
                'elems={elems}>').format(**self.__dict__)

    def __neg__(self) -> None:
        for row in self.elems:
            for elem in row:
                operator.neg(elem)
        return self

    def check(self, raw_data, ctx_elem, ctrl_name=None) -> list:
        self._check_coords(raw_data)
        self._read_data(raw_data)
        self._apply_funcs(raw_data, ctx_elem)
        return self._flatten_elems()

    def _check_coords(self, raw_data) -> None:
        '''Замена * на реальные значения ключей массивов'''
        if self.rows == ['*']:
            raw_section = raw_data[self.section]
            self.rows = [raw_section.keys()]

        if self.entries == ['*']:
            raw_row = raw_data[self.section][self.rows[0]]
            self.entries = [k for k in raw_row.keys() if isinstance(k, int)]

    def _read_data(self, raw_data) -> None:
        '''Заполнение массива элементами удовлетворяющими условиям специфик'''
        raw_section = raw_data[self.section]
        for row_code in self.rows:
            if not self.__check_spec(raw_section[row_code]):
                continue
            row = []
            for entry_code in self.entries:
                row.append(Elem(raw_section[row_code][entry_code],
                                section=self.section,
                                row=row_code,
                                entry=entry_code))
            self.elems.append(row)

    def __check_spec(self, raw_row) -> bool:
        '''Проверка удовлетворения строки набору специфик'''
        for idx, spec in self.specs:
            if spec is None or spec == '*':
                continue
            elif raw_row.get(f's{idx}') != spec:
                return False
        return True

    def _apply_funcs(self, raw_data, ctx_elem):
        '''Выполнение функций на эелементах массива'''
        for func, args in self.funcs:
            if func == 'sum':
                self._apply_sum(ctx_elem)
            elif func in ('abs', 'floor'):
                self._apply_unary(func)
            elif func in ('round', 'isnull'):
                self._apply_binary(raw_data, func, *args)
            else:
                self._apply_math(raw_data, func, *args)

        if not self.rounded_off:  # округление по умолчанию
            self._apply_binary(raw_data, 'round', Elem(2))

    def _apply_sum(self, ctx_elem):
        '''Суммирование строк и/или графов'''
        if self.entries == ctx_elem.entries:  # всех строк в каждой графе
            self.elems = [[reduce(operator.add, l)] for l in zip(*self.elems)]
        else:                                 # всех граф в каждой строке
            self.elems = [[reduce(operator.add, l)] for l in self.elems]

        if self.rows != ctx_elem.rows:        # всех элементов массива
            self.elems = [[reduce(operator.add, chain(*self.elems))]]

    def _apply_unary(self, func):
        '''Выполнение унарных операций (abs, floor)'''
        for row in self.elems:
            for elem in row:
                getattr(elem, func)()

    def _apply_binary(self, raw_data, func, elem):
        '''Выполнение бинарных операций (round, isnull)'''
        arg = int(elem.check(raw_data, self)[0].val)
        for row in self.elems:
            for elem in row:
                getattr(elem, func)(arg)

    def _apply_math(self, raw_data, func, elem):
        '''Выполнение математических операций (add, sub, mul, truediv)'''
        left_operand = self._flatten_elems()
        right_operand = elem.check(raw_data, self)

        operand_pairs = self._zip(left_operand, right_operand)
        self.elems.clear()
        for l_elem, r_elem in operand_pairs:
            self.elems.append([getattr(operator, func)(l_elem, r_elem)])

    def _zip(self, *lists):
        '''Сбираем массивы в список кортежей. Если длина массивов различается
           и самый короткий длиной в 1 элемент, заменяем его на массив равной
           длины с полными копиями этого элемента
           (Предполагается, что только 1 массив может быть короче других и
           его длина всегда равна 1, но проверку на всякий случай оставил)
           [1, 2], [3], [4, 5] > [1, 2], [3, 3], [4, 5] > [1, 3, 4], [2, 3, 5]
        '''
        smallest, *_, biggest = sorted(lists, key=len)
        if len(smallest) != len(biggest) and len(smallest) == 1:
            lists = list(lists)
            s_idx, s_elem = lists.index(smallest), smallest[0]
            lists[s_idx] = [deepcopy(s_elem) for _ in range(len(biggest))]
        return zip(*lists)

    def _flatten_elems(self):
        '''Возвращаем плоский массив элементов'''
        return list(chain(*self.elems))

    def add_func(self, func, *args):
        '''Добавляем функцию в "очередь" при парсинге'''
        if func == 'round':
            self.rounded_off = True
        self.funcs.append((func, args))


class ElemLogic(ElemList):
    def __init__(self, l_elem, operator, r_elem):
        self.l_elem = l_elem
        self.r_elem = r_elem
        self.op_name = operator.lower()
        self.op_func = operator_map[self.op_name]
        self.ctrl_name = 'Unknown Check'

        self.elems = []

    def __repr__(self):
        return ('<ElemLogic left={l_elem} operator="{op_name}" '
                'right={r_elem}>').format(**self.__dict__)

    def check(self, raw_data, ctx_elem=None, ctrl_name=None):
        self.ctrl_name = ctrl_name or self.ctrl_name
        self._control(raw_data)
        return self.elems

    def _control(self, raw_data):
        '''Подготовка элементов, слияние. Определение аттрибута контроля.
           Вызов метода проверки выполнения логического условия'''
        l_elems = self.l_elem.check(raw_data, self.r_elem, self.ctrl_name)
        r_elems = self.r_elem.check(raw_data, self.l_elem, self.ctrl_name)
        elems_pairs = self._zip(l_elems, r_elems)

        ctrl_attr = 'bool' if self.op_name in ('and', 'or') else 'val'
        self.__control(elems_pairs, attr=ctrl_attr)

    def __control(self, elems_pairs, attr) -> None:
        '''Проверка пары на выполнение условий логического оператора'''
        for l_elem, r_elem in elems_pairs:
            if not self.op_func(getattr(l_elem, attr), getattr(r_elem, attr)):
                r_elem.control_fail(l_elem, self.ctrl_name, self.op_name)

            r_elem.controls.extend(l_elem.controls)
            self.elems.append(r_elem)


class ElemSelector(ElemList):
    def __init__(self, action, elems):
        self.action = action.lower()

        self.rounded_off = False
        self.funcs = []

        self.elems = elems

    def __repr__(self):
        return ('<ElemSelector action={action} rounded_off={rounded_off} '
                'funcs={funcs} elems={elems}>').format(**self.__dict__)

    def check(self, raw_data, ctx_elem, ctrl_name=None):
        self._select(raw_data, ctx_elem)
        self._apply_funcs(raw_data, ctx_elem)
        return self._flatten_elems()

    def _select(self, raw_data, ctx_elem):
        '''Подготовка элементов, слияние. Очистка списка элементов.
           Вызов метода селектора по полю action'''
        elems_results = [elem.check(raw_data, ctx_elem) for elem in self.elems]
        elems_results = self._zip(*elems_results)

        self.elems.clear()
        getattr(self, self.action)(elems_results)

    def nullif(self, elems_results):
        '''Сравнивает результаты левого и правого элементов. Добавляем к
           результату элемент со значением None если значения равны,
           иначе добавляем левый элемент'''
        for l_elem, r_elem in elems_results:
            if l_elem.val == r_elem.val:
                self.elems.append([Elem(None)])
            else:
                self.elems.append([l_elem])

    def coalesce(self, elems_results):
        '''Сравнивает результаты элементов каждой "линии" (строки/графа).
           Добавляем к результату первый элемент значение которого не None'''
        for line_elems in elems_results:
            first_elem = next([e] for e in line_elems if e.val is not None)
            self.elems.append(first_elem)
