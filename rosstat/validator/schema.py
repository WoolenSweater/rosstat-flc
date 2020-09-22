import re
import traceback
from collections import defaultdict
from .exceptions import FormatError
from .checkers import FormatChecker, ControlChecker

year_pattern = re.compile(r'18\d{2}|19\d{2}|20\d{2}')


def str_int(v):
    return str(int(v)) if v.isdigit() else v


class Schema:
    def __init__(self, xml_tree, *, skip_warns):
        self.xml = xml_tree
        self._required = []
        self._errors = []
        self._skip_warns = skip_warns
        self._dimension = defaultdict(list)

        self.idp = self._get_idp()
        self.obj = self._get_obj()
        self.title = self._prepare_title()
        self.dics = self._prepare_dics()
        self.format = self._prepare_format()
        self.controls = self._prepare_controls()

        self._check_list = ('attributes', 'title', 'sections', 'required',
                            'duplicates', 'format', 'controls')

    def __repr__(self):
        return '<Schema idp={idp} obj={obj} title={title}'.format(
            **self.__dict__)

    def _add_error(self, error):
        '''Добавление ошибки в список'''
        self._errors.append(error)

    def _get_idp(self):
        '''Получение idp из корня шаблона'''
        return str(int(self.xml.xpath('/metaForm/@idp')[0]))

    def _get_obj(self):
        '''Получение obj из корня шаблона'''
        return self.xml.xpath('/metaForm/@obj')[0]

    def _prepare_title(self):
        '''Получения множества полей тайтла из шаблона'''
        return set(f for f in self.xml.xpath('/metaForm/title/item/@field'))

    def _prepare_format(self):
        '''Создание словаря с чекерами полей отчета. Заполнения списка
           обязательных полей отчёта их координатами
        '''
        form = {}
        for section in self.xml.xpath('/metaForm/sections/section'):
            section_code = str_int(section.attrib['code'])
            form[section_code] = {}

            for row in section.xpath('./rows/row[@type!="C"]'):
                row_code = str_int(row.attrib['code'])
                row_type = row.attrib['type']
                form[section_code][row_code] = {}

                for cell in row.xpath('./cell'):
                    cell_code = str_int(cell.attrib['column'])
                    input_type = cell.attrib['inputType']
                    format_checker = FormatChecker(cell, self.dics)
                    form[section_code][row_code][cell_code] = format_checker

                    if input_type == '1' and row_type != 'M':
                        coords = (section_code, row_code, cell_code)
                        self._required.append(coords)

            form[section_code].update(self._get_adds(section, section_code))
        return form

    def _get_adds(self, section, section_code):
        '''Получение дополнительных данных для проверки: чекеры по умолчанию,
           заполнение словаря размерности секций отчёта, определение имен
           колонок специфик
        '''
        adds = {'default': {}, 'specs': {}}
        for col in section.xpath('./columns/column[@type!="B"]'):
            if col.attrib['type'] == 'S':
                adds['specs'][col.attrib['code']] = col.attrib['fld']
                continue
            for cell in col:
                cell_code = str_int(cell.attrib['column'])
                adds['default'][cell_code] = FormatChecker(cell, self.dics)
                self._dimension[section_code].append(cell_code)
        return adds

    def _prepare_controls(self):
        '''Создание списка с контролями'''
        controls = []
        for control in self.xml.xpath('/metaForm/controls/control'):
            controls.append(ControlChecker(control,
                                           dimension=self._dimension,
                                           skip_warns=self._skip_warns))
        return controls

    def _prepare_dics(self):
        '''Чтение справочников'''
        dics = {}
        for dic in self.xml.xpath('/metaForm/dics/dic'):
            dict_id = dic.attrib['id']
            dics[dict_id] = {}

            for term_node in dic.xpath('./term'):
                term_id = term_node.attrib.pop('id')
                if term_id not in dics[dict_id]:
                    dics[dict_id][term_id] = defaultdict(set)
                for k, v in term_node.attrib.items():
                    dics[dict_id][term_id][k].add(v)
        return dics

    def validate(self, report):
        '''Основной метод для вызова валидации отчёта'''
        try:
            self._check(report)
        except Exception:
            self._add_error('Непредвиденная ошибка валидации')
            print('Unexpected Error', traceback.format_exc())
        finally:
            return self._errors

    def _check(self, report):
        '''Вспомогательный метод для итерации по методам проверок'''
        for name in self._check_list:
            getattr(self, f'_check_{name}')(report)
            if self._errors:
                break

    def _check_attributes(self, report):
        '''Проверка соответствия атрибутов шаблона: периодов и года'''
        if report.period_type is not None and report.period_type != self.idp:
            self._add_error('Тип периодичности отчёта не соответствует '
                            'типу периодичности шаблона')

        if report.period_code is None and not report.set_periods(self):
            self._add_error('Неверное значение периода отчёта')

        if not year_pattern.match(report.year):
            self._add_error('Указан недопустимый год')

    def _check_title(self, report):
        '''Проверка полей тайтла'''
        checked = []
        for name, value in report.title:
            if name not in self.title:
                self._add_error(f'Блок title: лишнее поле "{name}"')
            if checked.count(name) != 0:
                self._add_error(f'Блок title: повтор поля "{name}"')
            if not value:
                self._add_error(f'Блок title: нет значения в поле "{name}"')
            if name == self.obj and not self.__check_obj(value):
                self._add_error(f'Блок title: код ОКПО должен содержать 8 '
                                f'или 14 знаков и быть числом')
            checked.append(name)

        if self.obj not in checked:
            self._add_error(f'Блок title: отсутствует обязательное '
                            f'поле "{self.obj}"')
            self.title.discard(self.obj)

        diff = self.title - set(checked)
        for filed in diff:
            self._add_error(f'Блок title: отсутствует поле "{filed}"')

    def __check_obj(self, value):
        '''Проверка формата ОКПО'''
        return True if len(value) in (8, 14) and value.isdigit() else False

    def _check_sections(self, report):
        '''Проверка наличия всех разделов в отчёте'''
        report_sec = set(code for code, _ in report.items())
        schema_sec = set(self._dimension.keys())

        diff = schema_sec - report_sec
        for section in diff:
            self._add_error(f'Блок sections: отсутствует раздел {section}')

    def _check_required(self, report):
        '''Проверка заполнения обязательных полей отчёта'''
        template = 'Раздел {}, строка {}, графа {} обязательна для заполнения'
        for s_idx, r_idx, c_idx in self._required:
            rows = list(report.get_section(s_idx).get_rows(r_idx))
            if not rows:
                self._add_error(template.format(s_idx, r_idx, c_idx))
            for row in rows:
                if not row.get_entry(c_idx):
                    self._add_error(template.format(s_idx, r_idx, c_idx))

    def _check_duplicates(self, report):
        '''Проверка дублирующихся строк в отчёте'''
        for row, counter in report.row_counters.items():
            if counter > 1:
                self._add_error(f'Строка "{row[0]}" повторяется '
                                f'{counter} раз(а)')

    def _check_format(self, report):
        '''Итерация по секциям и строкам с передачей их в собственные методы
           проверки формата. Для строки это проверка специфик, для полей -
           проверка введеного значения.
        '''
        for s_idx, section in report.items():
            for r_idx, rows in section.items():
                for row in rows:
                    self.__check_row(row, s_idx, r_idx)
                    self.__check_cells(row, s_idx, r_idx)

    def __check_row(self, row, s_idx, r_idx):
        '''Итерация по ожидаемым спецификам с их последующей проверкой'''
        specs_map = self.format[s_idx]['specs']
        for c_idx, spec in specs_map.items():
            self.__check_fmt(s_idx, r_idx, c_idx, row, spec, specs_map,
                             err_msg='Раздел {}, строка {}, специфика {}. {}')

    def __check_cells(self, row, s_idx, r_idx):
        '''Итерация по полям строки с их последующей проверкой'''
        for c_idx, cell in row.items():
            self.__check_fmt(s_idx, r_idx, c_idx, cell,
                             err_msg='Раздел {}, строка {}, графа {}. {}')

    def __check_fmt(self, s_idx, r_idx, c_idx, *args, err_msg=None):
        '''Непосредственная проверка значения с отловом и обработкой ошибки'''
        try:
            checker = self.__get_format_checker(s_idx, r_idx, c_idx)
            checker.check(*args)
        except FormatError as ex:
            self._add_error(err_msg.format(s_idx, r_idx, c_idx, ex.msg))
        except Exception:
            ex_msg = 'Непредвиденная ошибка проверки формата'
            self._add_error(err_msg.format(s_idx, r_idx, c_idx, ex_msg))
            print('Unexpected Error', traceback.format_exc())

    def __get_format_checker(self, s_idx, r_idx, c_idx):
        '''Получение чекера для поля/строки'''
        try:
            return self.format[s_idx][r_idx][c_idx]
        except KeyError:
            return self.format[s_idx]['default'][c_idx]

    def _check_controls(self, report):
        '''Проверка отчёта по контролям'''
        if report.blank:
            return
        for control in self.controls:
            try:
                control.check(report, self._errors)
            except Exception:
                self._add_error(f'{control.id} Непредвиденная ошибка '
                                f'проверки контроля')
                print('Unexpected Error', traceback.format_exc())
