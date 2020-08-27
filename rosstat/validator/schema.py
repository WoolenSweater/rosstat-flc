import traceback
from .exceptions import FormatError
from .checkers import FormatChecker, ControlChecker


class Schema:
    def __init__(self, xml_tree):
        self.xml = xml_tree
        self._required = []
        self._errors = []

        self.idp = self._get_idp()
        self.title = self._prepare_title()
        self.dics = self._prepare_dics()
        self.format = self._prepare_format()
        self.controls = self._prepare_controls()

    def __repr__(self):
        return ('<Schema title={title}\nform={form}\ncontrols={controls}\n'
                'dics={dics}>').format(**self.__dict__)

    def _add_error(self, error):
        '''Добавление ошибки в список'''
        self._errors.append(error)

    def _get_idp(self):
        '''Получение idp из корня шаблона'''
        return str(int(self.xml.getroot().attrib['idp']))

    def _prepare_title(self):
        '''Получения множества полей тайтла из шаблона'''
        return set(f for f in self.xml.xpath('/metaForm/title/item/@field'))

    def _prepare_format(self):
        '''Создание словаря с чекерами полей отчета. Заполнения списка
           обязательных полей отчёта их координатами
        '''
        form = {}
        for section in self.xml.xpath('/metaForm/sections/section'):
            section_code = section.attrib['code']
            form[section_code] = {}

            for row in section.xpath('./rows/row[@type!="C"]'):
                row_code = row.attrib['code']
                row_type = row.attrib['type']
                form[section_code][row_code] = {}

                for cell in row.xpath('./cell'):
                    cell_code = cell.attrib['column']
                    input_type = cell.attrib['inputType']
                    format_checker = FormatChecker(
                        cell, self.dics, input_type, row_type=row_type)
                    form[section_code][row_code][cell_code] = format_checker

                    if input_type == '1' and row_type != 'M':
                        coords = (section_code, row_code, cell_code)
                        self._required.append(coords)

            form[section_code]['default'] = self._get_defaults(section)
        return form

    def _get_defaults(self, section):
        '''Создание словаря с чекерами "по умолчанию"'''
        defaults = {}
        for cell in section.xpath('./columns/column[@type!="B"]/default-cell'):
            cell_code = cell.attrib['column']
            input_type = cell.attrib['inputType']
            defaults[cell_code] = FormatChecker(cell, self.dics, input_type)
        return defaults

    def _prepare_controls(self):
        '''Создание списка с контролями'''
        controls = []
        for control in self.xml.xpath('/metaForm/controls/control'):
            controls.append(ControlChecker(control))
        return controls

    def _prepare_dics(self):
        '''Чтение справочников'''
        dics = {}
        for dic in self.xml.xpath('/metaForm/dics/dic'):
            dict_id = dic.attrib['id']
            dics[dict_id] = {}

            for term in dic.xpath('./term'):
                term_id = term.attrib['id']
                dics[dict_id][term_id] = term.text
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
        for name in ('period', 'title', 'required', 'format', 'controls'):
            getattr(self, f'_check_{name}')(report)
            if self._errors:
                break

    def _check_period(self, report):
        '''Проверка соответствия периода шаблона и периода в отчёте'''
        if self.idp != report.period_type:
            self._add_error('Тип периодичности отчёта не соответствует '
                            'типу периодичности шаблона')

    def _check_title(self, report):
        '''Проверка полей тайтла'''
        fields = list(report.title.keys())
        for field in self.title:
            num_of_fields = fields.count(field)

            if num_of_fields < 1:
                self._add_error(f'Отсутствует поле "{field}" в блоке title')
            elif num_of_fields > 1:
                self._add_error(f'Поле "{field}" в блоке title '
                                 f'указано более 1 раза')

        diff = set(fields) - self.title
        if diff:
            diffs = ', '.join(diff)
            self._add_error(f'Лишнее поле(я) "{diffs}" в блоке title')

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

    def _check_format(self, report):
        '''Проверка формата заполненых полей. Итерация по секциям и строкам'''
        for s_idx, section in report.items():
            for r_idx, rows in section.items():
                for row in rows:
                    self.__check_cells(row, s_idx, r_idx)

    def __check_cells(self, row, s_idx, r_idx):
        '''Итерация по полям строки с их последующей проверкой'''
        template = 'Раздел {}, строка {}, графа {}. {}'
        for c_idx, cell in row.items():
            if not cell:
                continue
            try:
                format_checker = self.__get_format_checker(s_idx, r_idx, c_idx)
                format_checker.check(cell, self._errors)
            except FormatError as ex:
                self._add_error(template.format(s_idx, r_idx, c_idx, ex.msg))
            except Exception:
                ex_msg = 'Непредвиденная ошибка проверки формата ячейки'
                self._add_error(template.format(s_idx, r_idx, c_idx, ex.msg))
                print('Unexpected Error', traceback.format_exc())

    def __get_format_checker(self, s_idx, r_idx, c_idx):
        '''Получение чекера для поля'''
        try:
            return self.format[s_idx][r_idx][c_idx]
        except KeyError:
            return self.format[s_idx]['default'][c_idx]

    def _check_controls(self, report):
        '''Проверка отчёта по контролям'''
        for control in self.controls:
            try:
                control.check(report, self._errors)
            except Exception:
                self._add_error(f'Непредвиденная ошибка проверки '
                                f'контроля {control.id}')
                print('Unexpected Error', traceback.format_exc())
