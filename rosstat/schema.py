import traceback
from collections import defaultdict
from .helpers import SchemaFormats, NestedDefaultdict
from .validators import (AttrValidator, TitleValidator,
                         FormatValidator, ControlValidator)


def str_int(v):
    return str(int(v)) if v.isdigit() else v


class Schema:
    def __init__(self, xml_tree, *, skip_warns):
        self.xml = xml_tree
        self.errors = []
        self.required = []
        self.skip_warns = skip_warns
        self.dimension = defaultdict(list)

        self.idp = self._get_idp()
        self.obj = self._get_obj()
        self.title = self._get_title()
        self.formats = self._get_formats()
        self.controls = self._get_controls()
        self.catalogs = self._get_catalogs()

        self.validators = self._init_validators()

    def __repr__(self):
        return '<Schema idp={idp} obj={obj} title={title}'.format(
            **self.__dict__)

    def _get_idp(self):
        '''Получение атрибута idp'''
        return str(int(self.xml.xpath('/metaForm/@idp')[0]))

    def _get_obj(self):
        '''Получение атрибута obj'''
        return self.xml.xpath('/metaForm/@obj')[0]

    def _get_title(self):
        '''Получение ноды с заголовком'''
        return self.xml.xpath('/metaForm/title')[0]

    def _get_formats(self):
        '''Итерация по секциям, строкам и колонокам с получением нод,
           определяющих формат строк и значений в отчёте
        '''
        form = SchemaFormats()
        for section in self.xml.xpath('/metaForm/sections/section'):
            sec_code = str_int(section.attrib['code'])
            defaults, specs = self.__get_default_formats(section, sec_code)
            form[sec_code] = {'specs': specs}

            for row in section.xpath('./rows/row[@type!="C"]'):
                row_code = str_int(row.attrib['code'])
                form[sec_code][row_code] = defaults.copy()

                for cell in row.xpath('./cell'):
                    col_code = str_int(cell.attrib['column'])
                    form[sec_code][row_code][col_code] = cell.attrib

                    if self.__required_cell(row, cell):
                        coords = (sec_code, row_code, col_code)
                        self.required.append(coords)
        return form

    def __required_cell(self, row, cell):
        '''Проверка, является ли ячейка обязательной к заполнению'''
        if cell.attrib['inputType'] == '1' and row.attrib['type'] != 'M':
            return True
        return False

    def __get_default_formats(self, section, sec_code):
        '''Получение нод определяющих формат строк и значений по умолчанию'''
        defaults, specs = {}, {}
        for column in section.xpath('./columns/column'):
            col_code = str_int(column.attrib['code'])

            if column.attrib['type'] == 'S':
                specs[col_code] = column.attrib['fld'][-1]
            elif column.attrib['type'] == 'Z':
                defaults[col_code] = self.__get_default_cell(column)
                self.dimension[sec_code].append(col_code)

        return defaults, specs

    def __get_default_cell(self, column):
        '''Возвращает словарь атрибутов дефолтной ячейки или пустой словарь'''
        try:
            return column.find('default-cell').attrib
        except AttributeError:
            return {}

    def _get_controls(self):
        '''Получение нод с контролями'''
        return self.xml.xpath('/metaForm/controls/control')

    def _get_catalogs(self):
        '''Получение справочников'''
        catalogs = defaultdict(dict)
        for catalog in self.xml.xpath('/metaForm/dics/dic'):
            catalog_id = catalog.attrib['id']
            catalogs[catalog_id]['full'] = NestedDefaultdict(set)
            catalogs[catalog_id]['ids'] = []

            for term_node in catalog.xpath('./term'):
                term_id = term_node.attrib.pop('id')

                catalogs[catalog_id]['ids'].append(term_id)

                for attr, value in term_node.attrib.items():
                    catalogs[catalog_id]['full'][term_id][attr].add(value)
        return catalogs

    def _init_validators(self):
        '''Инициализация валидаторов'''
        return (AttrValidator(self),
                TitleValidator(self),
                FormatValidator(self),
                ControlValidator(self))

    def validate(self, report):
        '''Валидация отчёта'''
        try:
            for validator in self.validators:
                if not validator.validate(report):
                    self._errors_handle(validator)
                    break
        except Exception:
            self.errors.append({'code': '0.0',
                                'name': 'Непредвиденная ошибка',
                                'message': 'Не удалось выполнить проверку'})
            print('Unexpected Error', traceback.format_exc())
        finally:
            return self.errors

    def _errors_handle(self, validator):
        '''Форматирование ошибок'''
        for error in validator.errors:
            self.errors.append({
                'code': f'{validator.code}.{error.code}',
                'name': validator.name,
                'message': error.message
            })
