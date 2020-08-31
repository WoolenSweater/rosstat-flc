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

    def check(self, report, ctx_elem, fault, precision):
        self._read_data(report)
        self._apply_funcs(report, ctx_elem, fault, precision)
        return self._flatten_elems()

    def _read_data(self, report):
        '''Чтение отчёта и конвертация его в массивы элементов'''
        raw_sec = report.get_section(self.section)
        for row_code in self.rows:
            raw_rows = list(raw_sec.get_rows(row_code, self.specs))
            if not raw_rows:
                self._read_entries(row_code, raw_row=None)
                continue
            for raw_row in raw_rows:
                self._read_entries(row_code, raw_row=raw_row)

    def _read_entries(self, row_code, raw_row=None):
        '''Чтение графов отдельно взятой строки строки и создание элементов'''
        row = []
        for entry_code in self.entries:
            entry, stub = self._read_enrty_val(entry_code, raw_row)
            row.append(Elem(entry,
                            section=[self.section],
                            rows=[row_code],
                            entries=[entry_code],
                            stub=stub))
        if row:
            self.elems.append(row)

    def _read_enrty_val(self, entry_code, raw_row):
        '''Получение значения графы из строки. Если нет всей строки или
           значения, возвращаем нулевое значение и признак "заглушки"
        '''
        if raw_row is None:
            return 0, True
        entry = raw_row.get_entry(entry_code)
        return (entry, False) if entry else (0, True)

    def _apply_funcs(self, report, ctx_elem, fault, precision):
        '''Выполнение функций на эелементах массива'''
        for func, args in self.funcs:
            if func == 'sum':
                self._apply_sum(ctx_elem)
            elif func in ('abs', 'floor'):
                self._apply_unary(func)
            elif func in ('round', 'isnull'):
                self._apply_binary(report, func, fault, precision, args)
            else:
                self._apply_math(report, func, fault, precision, *args)

    def _apply_sum(self, ctx_elem):
        '''Суммирование строк и/или графов'''
        if self.entries == ctx_elem.entries:  # строк в каждой графе
            self.elems = [[reduce(operator.add, l)] for l in zip(*self.elems)]
        else:                                 # граф в каждой строке
            self.elems = [[reduce(operator.add, l)] for l in self.elems]

        if self.rows != ctx_elem.rows:        # всех элементов
            self.elems = [[reduce(operator.add, chain(*self.elems))]]

    def _apply_unary(self, func):
        '''Выполнение унарных операций (abs, floor, neg)'''
        for row in self.elems:
            for elem in row:
                getattr(elem, func)()

    def _apply_binary(self, report, func, fault, precision, elems):
        '''Выполнение бинарных операций (round, isnull)'''
        args = []
        for elem in elems:
            args.append(int(elem.check(report, self, fault, precision)[0].val))
        for row in self.elems:
            for elem in row:
                getattr(elem, func)(*args)

    def _apply_math(self, report, func, fault, precision, elem):
        '''Выполнение математических операций (add, sub, mul, truediv)'''
        left_operand = self._flatten_elems()
        right_operand = elem.check(report, self, fault, precision)

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

        self.fault = -1
        self.precision = 2
        self.elems = []

    def __repr__(self):
        return '<ElemLogic left={} operator="{}" right={}>'.format(
            self.l_elem, self.op_name, self.r_elem)

    def check(self, report, ctx_elem=None, fault=-1, precision=2):
        '''Основной метод для вызова проверки элемента.
           Все элементы принимают одинаковый набор аргументов, для поддержания
           единого интерфейса взамодействия, но могут не использовать какие-то
           из них.
           ctx_elem - контекстный элемент. Для логического элемента равен None,
               так как он и так уже содержит в себе левый и правый элементы
               логического условия, которые приходятся друг другу контекстом.
           fault - погрешность. Если логическое условие не выполнено,
               дополнительно проверяется погрешность. Отрицательное значение
               для проверки "condition", так как там отклонение не допустимо.
           precision - округление. Используется логическим элементом для
               округления перед проверкой условия.
        '''
        self.fault = fault
        self.precision = precision
        self._control(report)
        return self.elems

    def _check_elem(self, report, elem, ctx_elem):
        '''Вызов метода проверки у элемента'''
        return elem.check(report, ctx_elem, self.fault, self.precision)

    def _control(self, report):
        '''Подготовка элементов, слияние. Определение аттрибута контроля.
           Вызов метода проверки выполнения логического условия'''
        l_elems = self._check_elem(report, self.l_elem, self.r_elem)
        r_elems = self._check_elem(report, self.r_elem, self.l_elem)
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
           или "заглушкой" и скаляром
        '''
        if l_elem.stub and r_elem.stub:
            return False
        elif l_elem.stub and r_elem.scalar:
            return False
        elif l_elem.scalar and r_elem.stub:
            return False
        return True

    def __get_elem_values(self, l_elem, r_elem, attr):
        '''Округление и возвращение значений которые будут сравниваться'''
        l_elem.round(self.precision)
        r_elem.round(self.precision)
        return getattr(l_elem, attr), getattr(r_elem, attr)

    def __check_fault(self, l_elem_v, r_elem_v):
        '''Проверка погрешности'''
        return abs(l_elem_v - r_elem_v) <= self.fault


class ElemSelector(ElemList):
    def __init__(self, action, elems):
        self.action = action.lower()
        self.funcs = []
        self.elems = elems

    def __repr__(self):
        return '<ElemSelector action={} funcs={} elems={}>'.format(
            self.action, self.funcs, self.elems)

    def check(self, report, ctx_elem, fault, precision):
        self._select(report, ctx_elem, fault, precision)
        self._apply_funcs(report, ctx_elem, fault, precision)
        return self._flatten_elems()

    def _select(self, report, ctx_elem, fault, precision):
        '''Подготовка элементов, слияние. Очистка списка элементов.
           Вызов метода селектора по полю action'''
        elems_results = []
        for elem in self.elems:
            elems_results.append(
                elem.check(report, ctx_elem, fault, precision))
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
