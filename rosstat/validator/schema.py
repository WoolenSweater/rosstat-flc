import traceback
from .exceptions import ValidationError
from .checkers import CellChecker, ControlChecker


class Schema:
    def __init__(self, xml_tree):
        self.xml = xml_tree
        self._required = []
        self._errors = []

        self.idp = self._get_idp()
        self.title = self._prepare_title()
        self.dics = self._prepare_dics()
        self.form = self._prepare_form()
        self.controls = self._prepare_controls()

    def __repr__(self) -> str:
        return ('<Schema title={title}\nform={form}\ncontrols={controls}\n'
                'dics={dics}>').format(**self.__dict__)

    def _get_idp(self):
        return str(int(self.xml.getroot().attrib['idp']))

    def _prepare_title(self) -> set:
        return set(f for f in self.xml.xpath('/metaForm/title/item/@field'))

    def _prepare_form(self) -> dict:
        form = {}
        for section in self.xml.xpath('/metaForm/sections/section'):
            section_code = section.attrib['code']
            form[section_code] = {}

            for row in section.xpath('./rows/row[@type!="C"]'):
                row_code = row.attrib['code']
                form[section_code][row_code] = {}

                for cell in row.xpath('./cell'):
                    cell_code = cell.attrib['column']
                    input_type = cell.attrib['inputType']
                    cell_checker = CellChecker(cell, input_type, self.dics)
                    form[section_code][row_code][cell_code] = cell_checker

                    if input_type == '1':
                        coords = (section_code, row_code, cell_code)
                        self._required.append(coords)

            form[section_code]['default'] = self._get_defaults(section)
        return form

    def _get_defaults(self, section) -> dict:
        defaults = {}
        for cell in section.xpath('./columns/column[@type!="B"]/default-cell'):
            cell_code = cell.attrib['column']
            input_type = cell.attrib['inputType']
            defaults[cell_code] = CellChecker(cell, input_type, self.dics)
        return defaults

    def _prepare_controls(self) -> list:
        controls = []
        for control in self.xml.xpath('/metaForm/controls/control'):
            controls.append(ControlChecker(control))
        return controls

    def _prepare_dics(self) -> dict:
        dics = {}
        for dic in self.xml.xpath('/metaForm/dics/dic'):
            dict_id = dic.attrib['id']
            dics[dict_id] = {}

            for term in dic.xpath('./term'):
                term_id = term.attrib['id']
                dics[dict_id][term_id] = term.text
        return dics

    def validate(self, report) -> list:
        try:
            check_list = ('period', 'title', 'required', 'form', 'controls')
            self._check(check_list, report)
        except ValidationError as ex:
            self._errors.append(ex)
            print('Validation Error', traceback.format_exc())
        except Exception as ex:
            self._errors.append('Непредвиденная ошибка')
            print('Unexpected Error', traceback.format_exc())
        finally:
            return self._errors

    def _check(self, check_list, report) -> None:
        for name in check_list:
            getattr(self, f'_check_{name}')(report)
            if self._errors:
                break

    def _check_period(self, report):
        if self.idp != report.period_type:
            self._errors.append('Тип периодичности отчёта не соответствует '
                                'типу периодичности шаблона')

    def _check_title(self, report) -> None:
        fields = list(report.title.keys())
        for field in self.title:
            check = fields.count(field)

            if check < 1:
                message = f'Отсутствует поле "{field}" в блоке title'
                self._errors.append(message)
            elif check > 1:
                message = f'Поле "{field}" в блоке title указано более 1 раза'
                self._errors.append(message)

        diff = set(fields) - self.title
        if diff:
            diffs = ','.join(list(diff))
            self._errors.append(f'Лишнее поле(я) "{diffs}" в блоке title')

    def _check_required(self, report) -> None:
        errors = set()
        for section, row, col in self._required:
            for row in report.get_section(section).get_rows(row):
                if not row.get_entry(col):
                    errors.add(f'Раздел {section}, строка {row}, '
                               f'графа {col} обязательна для заполнения')
        self._errors.extend(errors)

    def _check_form(self, report) -> None:
        for s_idx, section in report.items():
            for r_idx, rows in section.items():
                for row in rows:
                    for c_idx, cell in row.items():
                        cell_checker = self.__get_cell_checker(s_idx,
                                                               r_idx,
                                                               c_idx)
                        cell_checker.check(cell, self._errors)

    def __get_cell_checker(self, s_idx, r_idx, c_idx) -> CellChecker:
        try:
            return self.form[s_idx][r_idx][c_idx]
        except KeyError:
            return self.form[s_idx]['default'][c_idx]

    def _check_controls(self, report):
        for control in self.controls:
            try:
                control.check(report, self._errors)
            except ValidationError:
                raise
            except Exception as ex:
                raise ValidationError(f'Ошибка при проверке {control.id}')
