import operator
from copy import deepcopy
from itertools import chain
from functools import reduce
from .value import nullablefloat
from .specific import Specific
from ..exceptions import NoElemToCompareError, NoFormatForRowError
from ....helpers import SPEC_KEYS

OPERATOR_MAP = {
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
BOOL_TYPE = {
    'and': 'bool',
    'or': 'bool'
}


class Elem:
    def __init__(self, val, section=None, rows=None, columns=None):
        self.section = set() if section is None else {section}
        self.rows = set() if rows is None else {rows}
        self.columns = set() if columns is None else {columns}

        self._controls = []
        self._func = None

        self.bool = True
        self.val = nullablefloat(val)

    def __add__(self, elem):
        return self.__modify(elem, operator.add)

    def __sub__(self, elem):
        return self.__modify(elem, operator.sub)

    def __mul__(self, elem):
        return self.__modify(elem, operator.mul)

    def __truediv__(self, elem):
        return self.__modify(elem, operator.truediv)

    def __neg__(self):
        self.val = self.val.neg()
        return self

    def __repr__(self):
        return '<Elem {}{}{} value={} bool={}>'.format(
            list(self.section),
            list(self.rows),
            list(self.columns),
            repr(self.val),
            self.bool
        )

    def __modify(self, elem, op_func):
        self.rows |= elem.rows
        self.columns |= elem.columns
        try:
            self.val = op_func(self.val, elem.val)
        except ZeroDivisionError:
            pass
        return self

    @property
    def controls(self):
        return self._controls

    def controls_clear(self):
        '''Очищение списка контролей'''
        self._controls.clear()

    def controls_extend(self, r_elem):
        '''Расширение списка контролей, контролями из правого элемента'''
        self._controls.extend(r_elem._controls)

    def controls_append(self, r_elem, op_name):
        '''Форматирование и добавление непройденного контроля'''
        self._controls.append({
            'left': self.val,
            'operator': op_name,
            'right': r_elem.val,
            'delta': round(self.val - r_elem.val, 2)
        })

    def check(self, report, params, ctx_elem):
        if self._func:
            return self._apply_func(report, params, *self._func)
        return [self]

    def _apply_func(self, report, params, func, right_elem):
        '''Выполнение функций на элементах массива'''
        elems = []
        for r_elem in right_elem.check(report, params, self):
            elems.append(getattr(operator, func)(deepcopy(self), r_elem))
        return elems

    def isnull(self, replace):
        '''Замена "нулёвого" значения на replace'''
        if self.val.is_null:
            self.val = nullablefloat(replace)

    def round(self, ndig, trunc=0):
        '''Округление/отсечение до ndig знаков'''
        if trunc > 0:
            self.val = self.val.truncate(ndig)
        else:
            self.val = self.val.round(ndig)

    def abs(self):
        '''Выполнение функции abs над значением'''
        self.val = self.val.abs()

    def floor(self):
        '''Выполнение функции floor над значением'''
        self.val = self.val.floor()

    def add_func(self, func, arg):
        '''Добавляем функцию элементу при парсинге'''
        self._func = (func, arg)


class ElemList:
    def __init__(self, sections, rows, columns, s1='*', s2='*', s3='*'):
        self.sections = sections
        self.rows = rows
        self.columns = columns

        self.s1 = s1
        self.s2 = s2
        self.s3 = s3

        self.specs = {}
        self.funcs = []
        self.elems = []

    def __repr__(self):
        return "<ElemList {}{}{} specs={} funcs={} elems={}>".format(
            self.sections,
            self.rows,
            self.columns,
            self.specs,
            self.funcs,
            self.elems
        )

    def __neg__(self):
        self._apply_unary('neg')
        return self

    def check(self, report, params, ctx_elem):
        self._read_data(report, params)
        self._apply_funcs(report, params, ctx_elem)
        return self._flatten_elems()

    def _read_data(self, report, params):
        '''Чтение отчёта и конвертация его в массивы элементов'''
        for section in self._read_sections(report):
            for row in self._read_rows(params, section):
                self.add_row(self._read_columns(params, section, row))

    def _read_sections(self, report):
        '''Получаем итератор по секциям'''
        return report.iter(self.sections)

    def _read_rows(self, params, section):
        '''Итерируемся по строкам и проверяем их на соответствие спецификам'''
        for row in section.iter(self.rows):
            if not params.formats.has(section.code, row.code):
                raise NoFormatForRowError()
            if row.match(self._get_specs(section.code, row.code, params)):
                yield row

    def _get_specs(self, sec_code, row_code, params):
        '''Подготавливаем и возвращаем специфики для строки,
           либо возвращаем уже готовые
        '''
        if row_code not in self.specs:
            self.specs[row_code] = list(self._prepare_specs(sec_code,
                                                            row_code,
                                                            params))
        return self.specs[row_code]

    def _prepare_specs(self, sec_code, row_code, params):
        '''Подготавливаем специфики для строки. Создаём специфику и проверяем,
           необходимо ли её "развернуть"
        '''
        for key in SPEC_KEYS:
            spec = Specific(key, getattr(self, key))
            if spec.need_expand():
                spec.expand(sec_code, row_code, params)
            yield spec

    def _read_columns(self, params, section, row):
        '''Читаем графы. Конвертируем их в элементы'''
        dimension = self._get_dimension(section.code, params)
        for col in row.iter(self.columns, dimension=dimension):
            yield Elem(col.value, section.code, row.code, col.code)

    def _get_dimension(self, sec_code, params):
        '''Возвращаем "размерность" для секции" '''
        return params.dimension[sec_code]

    def _apply_funcs(self, report, params, ctx_elem):
        '''Выполнение функций на элементах массива'''
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
        if isinstance(ctx_elem, ElemLogic):     # для случаев SUM{}|=|1|=|SUM{}
            self.elems = [[reduce(operator.add, chain(*self.elems))]]
        elif self.columns == ctx_elem.columns:  # строк в каждой графе
            self.elems = [[reduce(operator.add, l)] for l in zip(*self.elems)]
        elif self.rows == ctx_elem.rows:        # граф в каждой строке
            self.elems = [[reduce(operator.add, l)] for l in self.elems]
        elif not self.elems:                    # всех ячеек (секция пустая)
            self.elems = [[Elem(None, self.sections[0], '*', '*')]]
        else:                                   # всех ячеек (секция не пустая)
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

        self.elems.clear()
        for l_elem, r_elem in zip(left_operand, right_operand):
            self.elems.append([getattr(operator, func)(l_elem, r_elem)])

    def _zip(self, l_list, r_list):
        '''Сбираем списки в список кортежей. Если короткий список пустой,
           создаём "нулевой" элемент. Добиваем длину короткого списка
           до длины длинного если они различаются.
           [1, 2, 3], [4] > [1, 2, 3], [4, 4, 4] > [1, 4], [2, 4], [3, 4]
        '''
        lists = [l_list, r_list]
        if len(l_list) != len(r_list):
            short_list, long_list = self.__order_lists(l_list, r_list)
            short_list_index = self.__get_short_list_index(lists, short_list)
            lists[short_list_index] = self.__generate_short_list(short_list,
                                                                 long_list)
        return zip(*lists)

    def __order_lists(self, l_list, r_list):
        '''Упорядочивание двух списков от меньшего к большему'''
        if len(l_list) < len(r_list):
            return l_list, r_list
        return r_list, l_list

    def __get_short_list_index(self, lists, short_list):
        '''Возвращаем индекс короткого списка'''
        return lists.index(short_list)

    def __generate_short_list(self, short_list, long_list):
        '''Генерация списка, который заёмет место короткого'''
        return [deepcopy(short_list[0]) for _ in range(len(long_list))]

    def _flatten_elems(self):
        '''Возвращаем плоский массив элементов'''
        return list(chain(*self.elems))

    def add_row(self, columns):
        self.elems.append(list(columns))

    def add_func(self, func, *args):
        '''Добавляем функцию в "очередь" при парсинге'''
        self.funcs.append((func, args))


class ElemLogic(ElemList):
    def __init__(self, l_elem, operator, r_elem):
        self.l_elem = l_elem
        self.r_elem = r_elem
        self.op_name = operator.lower()
        self.op_func = OPERATOR_MAP.get(self.op_name)
        self.elem_type = BOOL_TYPE.get(self.op_name, 'val')

        self.funcs = []
        self.elems = []

        self.params = None

    def __repr__(self):
        return '<ElemLogic left={} operator="{}" right={} funcs={}>'.format(
            self.l_elem,
            self.op_name,
            self.r_elem,
            self.funcs
        )

    def check(self, report, params, ctx_elem=None):
        '''Основной метод вызова проверки'''
        self.params = params
        self._control(report)
        return self.elems

    def _control(self, report):
        '''Подготовка элементов, слияние, передача в метод контроля'''
        l_elems = self.l_elem.check(report, self.params, self.r_elem)
        r_elems = self.r_elem.check(report, self.params, self.l_elem)

        self.__check_elems(l_elems, r_elems)
        self.__apply_funcs(l_elems)
        self.__control(self._zip(l_elems, r_elems))

    def __check_elems(self, *elems):
        if not all(elems):
            raise NoElemToCompareError()

    def __apply_funcs(self, elems):
        '''Выполнение функций на элементах массива'''
        for func, _ in self.funcs:
            for elem in elems:
                getattr(elem, func)()

    def __control(self, elems_pairs):
        '''Определение аттрибута контроля. Итерация по парам элементов,
           выполнение проверок, обработка результата
        '''
        for l_elem, r_elem in elems_pairs:
            if not self.__logic_control(l_elem, r_elem):
                self.__get_result(l_elem, r_elem, success=False)
            else:
                self.__get_result(l_elem, r_elem, success=True)

            self.elems.append(l_elem)

    def __get_result(self, l_elem, r_elem, *, success):
        '''Обработка результата. При проверке логического "or", если левый
           элемент уже содержит ошибки, затираем их, инчае затираем список
           контролей правого. При неуспешной проверке, формируется ошибка
           которая прибавляется к списку контролей левого элемента.
           Затем в левый элемент сливаются все ошибки из списка правого.
        '''
        if self.op_name == 'or':
            if l_elem.controls:
                l_elem.controls_clear()
            else:
                r_elem.controls_clear()

        if not success:
            l_elem.controls_append(r_elem, self.op_name)
        l_elem.val = r_elem.val
        l_elem.controls_extend(r_elem)

    def __logic_control(self, l_elem, r_elem):
        '''Получение значений и проведение проверки'''
        if not self.op_func(*self.__get_elem_values(l_elem, r_elem)):
            return self.__check_fault(l_elem, r_elem)
        return True

    def __get_elem_values(self, l_elem, r_elem):
        '''Округление и возвращение значений которые будут сравниваться'''
        l_elem.round(self.params.precision)
        r_elem.round(self.params.precision)
        return getattr(l_elem, self.elem_type), getattr(r_elem, self.elem_type)

    def __check_fault(self, l_elem, r_elem):
        '''Проверка погрешности'''
        return abs(l_elem.val - r_elem.val) <= self.params.fault


class ElemSelector(ElemList):
    def __init__(self, action, elems):
        self.action = action.lower()
        self.funcs = []
        self.elems = elems

    def __repr__(self):
        return '<ElemSelector action={} funcs={} elems={}>'.format(
            self.action,
            self.funcs,
            self.elems
        )

    def check(self, *args):
        self._select(args)
        self._apply_funcs(*args)
        return self._flatten_elems()

    def _select(self, args):
        '''Подготовка элементов, слияние. Очистка списка элементов.
           Вызов метода селектора по полю action
        '''
        elems_results = self._zip(*(elem.check(*args) for elem in self.elems))
        self.elems.clear()
        getattr(self, self.action)(elems_results)

    def nullif(self, elems_results):
        '''Сравнивает результаты левого и правого элементов. Добавляем к
           результату элемент со значением None если значения равны,
           иначе добавляем левый элемент
        '''
        for l_elem, r_elem in elems_results:
            if l_elem.val == r_elem.val:
                self.elems.append([Elem(None)])
            else:
                self.elems.append([l_elem])

    def coalesce(self, elems_results):
        '''Сравнивает результаты элементов каждой "линии" (строки/графа).
           Добавляем к результату первый элемент значение которого не None
        '''
        for line_elems in elems_results:
            first_elem = next([e] for e in line_elems if e.val is not None)
            self.elems.append(first_elem)
