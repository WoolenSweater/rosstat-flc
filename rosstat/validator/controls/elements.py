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
    def __init__(self, val, section=[], rows=[], entries=[],
                 stub=False, scalar=False):
        self.section = set(section)
        self.rows = set(rows)
        self.entries = set(entries)
        # Возможно стоит выпилить координаты из элементов
        # они часто не информативны и могу сбить с толку

        self._controls = []

        self.scalar = scalar
        self.stub = stub
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
        return ('<Elem {}{}{} stub={} scalar={}: {} {}>').format(
            sorted(int(i) for i in self.section),
            sorted(int(i) for i in self.rows if i.isdigit()),
            sorted(int(i) for i in self.entries if i.isdigit()),
            self.stub, self.scalar, self.val, self.bool)

    def __modify(self, elem, op_func):
        self.rows |= elem.rows
        self.entries |= elem.entries
        try:
            self.val = op_func(self.val, elem.val)
        except ZeroDivisionError:
            pass
        return self

    @property
    def controls(self):
        return self._controls

    def control_fail(self, l_elem, op_name):
        '''Добавление значений которые не прошли контроль и установка флага
           указывающего на провал проверки
        '''
        self.bool = False
        self._controls.append({
            'left': l_elem.val,
            'right': self.val,
            'operator': op_name,
            'delta': round(l_elem.val - self.val, 2)
        })

    def check(self, *args):
        return [self]

    def isnull(self, replace):
        '''Замена None на replace. Так же снимает признак "заглушки"'''
        self.val = self.val or float(replace)
        self.stub = False

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
    def __init__(self, section, rows, entries,
                 s1=[None], s2=[None], s3=[None]):
        self.section = section[0]
        self.rows = set(rows)
        self.entries = set(entries)

        self.specs = {1: set(s1), 2: set(s2), 3: set(s3)}

        self.funcs = []
        self.elems = []

    def __repr__(self):
        return '<ElemList [{}]{}{} funcs={} elems={}>'.format(
            self.section,
            sorted(int(i) for i in self.rows if i.isdigit()),
            sorted(int(i) for i in self.entries if i.isdigit()),
            self.funcs, self.elems)

    def __neg__(self):
        self._apply_unary('neg')
        return self

    def check(self, report, params, ctx_elem):
        self._read_data(report, params.dimension)
        self._apply_funcs(report, params, ctx_elem)
        return self._flatten_elems()

    def _read_data(self, report, dimension):
        '''Чтение отчёта и конвертация его в массивы элементов'''
        raw_sec = report.get_section(self.section)
        for row_code, raw_rows in self._read_rows(raw_sec):
            if not raw_rows:
                self.elems.append(self._proc_row_empty(row_code, dimension))
                continue
            for raw_row in raw_rows:
                self.elems.append(self._proc_row(raw_row, row_code, dimension))

    def _read_rows(self, raw_sec):
        '''Читаем строки'''
        if self.rows == {'*'}:
            return raw_sec.items(specs=self.specs)
        return raw_sec.items(codes=self.rows, specs=self.specs)

    def _read_entries(self, raw_row, dimension):
        '''Читаем графы если строка не пустая'''
        if self.entries == {'*'}:
            return raw_row.items(codes=dimension[self.section])
        return raw_row.items(codes=self.entries)

    def _read_entries_empty(self, dimension):
        '''Читаем графы если строка пустая'''
        if self.entries == {'*'}:
            return iter(dimension[self.section])
        return iter(self.entries)

    def _proc_row(self, raw_row, row_code, dimension):
        '''Заполняем строку элементами со значениями из отчета, отсутствующие
           значения замещаем заглушкой'''
        row = []
        for entry_code, value in self._read_entries(raw_row, dimension):
            value, stub = (value, False) if value else (0, True)
            row.append(
                Elem(value, self.section, [row_code], [entry_code], stub=stub))
        return row

    def _proc_row_empty(self, row_code, dimension):
        '''Заполняем строку элементами заглушками'''
        row = []
        for entry_code in self._read_entries_empty(dimension):
            row.append(
                Elem(0, self.section, [row_code], [entry_code], stub=True))
        return row

    def _apply_funcs(self, report, params, ctx_elem):
        '''Выполнение функций на эелементах массива'''
        for func, args in self.funcs:
            if func == 'sum':
                self._apply_sum(ctx_elem)
            elif func in ('abs', 'floor'):
                self._apply_unary(func)
            elif func in ('round', 'isnull'):
                self._apply_binary(report, params, func, args)
            else:
                self._apply_math(report, params, func, *args)

    def _apply_sum(self, ctx_elem):
        '''Суммирование строк и/или графов'''
        if self.entries == ctx_elem.entries:  # строк в каждой графе
            self.elems = [[reduce(operator.add, l)] for l in zip(*self.elems)]
        elif self.rows == ctx_elem.rows:      # граф в каждой строке
            self.elems = [[reduce(operator.add, l)] for l in self.elems]
        else:                                 # всех элементов
            self.elems = [[reduce(operator.add, chain(*self.elems))]]

    def _apply_unary(self, func):
        '''Выполнение унарных операций (abs, floor, neg)'''
        for row in self.elems:
            for elem in row:
                getattr(elem, func)()

    def _apply_binary(self, report, params, func, elems):
        '''Выполнение бинарных операций (round, isnull)'''
        args = [int(elem.check(report, params, self)[0].val) for elem in elems]
        for row in self.elems:
            for elem in row:
                getattr(elem, func)(*args)

    def _apply_math(self, report, params, func, elem):
        '''Выполнение математических операций (add, sub, mul, truediv)'''
        left_operand = self._flatten_elems()
        right_operand = elem.check(report, params, self)

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
        self.funcs.append((func, args))


class ElemLogic(ElemList):
    def __init__(self, l_elem, operator, r_elem):
        self.l_elem = l_elem
        self.r_elem = r_elem
        self.op_name = operator.lower()
        self.op_func = operator_map[self.op_name]

        self.elems = []

        self.params = None

    def __repr__(self):
        return '<ElemLogic left={} operator="{}" right={}>'.format(
            self.l_elem, self.op_name, self.r_elem)

    def check(self, report, params, ctx_elem=None):
        '''Основной метод вызова проверки'''
        self.params = params
        self._control(report)
        return self.elems

    def _control(self, report):
        '''Подготовка элементов, слияние. Определение аттрибута контроля.
           Вызов метода проверки выполнения логического условия'''
        l_elems = self.l_elem.check(report, self.params, self.r_elem)
        r_elems = self.r_elem.check(report, self.params, self.l_elem)
        elems_pairs = self._zip(l_elems, r_elems)

        ctrl_attr = 'bool' if self.op_name in ('and', 'or') else 'val'
        self.__control(elems_pairs, attr=ctrl_attr)

    def __control(self, elems_pairs, attr):
        '''Проверка пары на выполнение условий логического оператора'''
        for l_elem, r_elem in elems_pairs:
            if not self.__can_logic_control(l_elem, r_elem):
                r_elem.controls.extend(l_elem.controls)
                continue

            l_elem_v, r_elem_v = self.__get_elem_values(l_elem, r_elem, attr)
            if not self.op_func(l_elem_v, r_elem_v):
                if not self.__check_fault(l_elem.val, r_elem.val):
                    r_elem.control_fail(l_elem, self.op_name)

            r_elem.controls.extend(l_elem.controls)
            self.elems.append(r_elem)

    def __can_logic_control(self, l_elem, r_elem):
        '''Логический контроль не проводится между "заглушками"
           или "заглушкой" и скаляром при условии, что выполняется проверка
           "rule", а не "condition"
        '''
        if not self.params.is_rule:
            return True
        elif l_elem.stub and r_elem.stub:
            return False
        elif l_elem.stub and r_elem.scalar:
            return False
        elif l_elem.scalar and r_elem.stub:
            return False
        return True

    def __get_elem_values(self, l_elem, r_elem, attr):
        '''Округление и возвращение значений которые будут сравниваться'''
        l_elem.round(self.params.precision)
        r_elem.round(self.params.precision)
        return getattr(l_elem, attr), getattr(r_elem, attr)

    def __check_fault(self, l_elem_v, r_elem_v):
        '''Проверка погрешности'''
        return abs(l_elem_v - r_elem_v) <= self.params.fault


class ElemSelector(ElemList):
    def __init__(self, action, elems):
        self.action = action.lower()
        self.funcs = []
        self.elems = elems

    def __repr__(self):
        return '<ElemSelector action={} funcs={} elems={}>'.format(
            self.action, self.funcs, self.elems)

    def check(self, *args):
        self._select(args)
        self._apply_funcs(*args)
        return self._flatten_elems()

    def _select(self, args):
        '''Подготовка элементов, слияние. Очистка списка элементов.
           Вызов метода селектора по полю action'''
        elems_results = self._zip(*(elem.check(*args) for elem in self.elems))
        self.elems.clear()
        getattr(self, self.action)(elems_results)

    def nullif(self, elems_results):
        '''Сравнивает результаты левого и правого элементов. Добавляем к
           результату элемент со значением None если значения равны,
           иначе добавляем левый элемент'''
        for l_elem, r_elem in elems_results:
            if l_elem.val == r_elem.val:
                self.elems.append([Elem(0, stub=True)])
            else:
                self.elems.append([l_elem])

    def coalesce(self, elems_results):
        '''Сравнивает результаты элементов каждой "линии" (строки/графа).
           Добавляем к результату первый элемент значение которого не None'''
        for line_elems in elems_results:
            first_elem = next([e] for e in line_elems if e.val is not None)
            self.elems.append(first_elem)
