import traceback
from collections import defaultdict

from .helpers import SchemaCatalog, SchemaDimension, SchemaFormat, str_int
from .validators import (
    AttrValidator,
    ControlValidator,
    FormatValidator,
    TitleValidator,
)


class Schema:
    def __init__(self, xml, *, alerts=False):
        self.alerts = alerts
        self.xml = xml
        self.errors = []
        self.required = []
        self.dimension = defaultdict(SchemaDimension)

        self.idp = self._get_idp()
        self.obj = self._get_obj()
        self.title = self._get_title()
        self.formats = self._get_formats()
        self.controls = self._get_controls()
        self.catalogs = self._get_catalogs()

        self.validators = self._init_validators()

    def __repr__(self):
        return (
            f"<Schema "
            f"idp={self.idp} "
            f"obj={self.obj} "
            f"alerts={self.alerts} "
            f"formats={self.formats.keys()} "
            f"catalogs={self.catalogs.keys()}>"
        )

    def _get_idp(self):
        """Получение атрибута idp"""
        return self.xml.xpath("string(@idp)")

    def _get_obj(self):
        """Получение атрибута obj"""
        return self.xml.xpath("string(@obj)")

    def _get_title(self):
        """Получение ноды с заголовком"""
        return self.xml.find("title")

    def _get_controls(self):
        """Получение итератора по нодам контролей"""
        return self.xml.iterfind("controls/control")

    # ---

    def _get_formats(self):
        """Чтение атрибутов определяющих формат строк и значений в отчёте"""
        form = SchemaFormat()

        for section in self.xml.iterfind("sections/section"):
            sec_code = str_int(section.get("code"))

            defaults, specs = self._read_defaults(section, sec_code)
            form.add(sec_code, specs)

            for row in section.iterfind("rows/row"):
                row_code = str_int(row.get("code"))

                form[sec_code][row_code] = defaults.copy()

                if self.__is_input_row(row):
                    self.dimension[sec_code].add_row(row_code)

                for cell in row.iterfind("cell"):
                    col_code = cell.get("column")

                    form[sec_code][row_code][col_code] = cell.attrib

                    if self.__is_required_cell(row, cell):
                        self.required.append((sec_code, row_code, col_code))
        return form

    def __is_input_row(self, row):
        """Строка доступная для ввода данных"""
        return row.get("type") != "C"

    def _read_defaults(self, section, sec_code):
        """Чтение атрибутов определяющих дефолтный формат и специфики"""
        defaults, specs = {}, {}

        for column in section.iterfind("columns/column"):
            col_code = column.get("code")
            col_type = column.get("type")

            defaults[col_code] = self.__get_default_cell(column)

            if col_type == "S":
                specs[column.get("fld")] = col_code
            elif col_type == "Z":
                self.dimension[sec_code].add_column(col_code)

        return defaults, specs

    def __get_default_cell(self, column):
        """Получение дефолтного словаря атрибутов ячейки"""
        try:
            return column.find("default-cell").attrib
        except AttributeError:
            return {}

    def __is_required_cell(self, row, cell):
        """Обязательная к заполнению ячейка"""
        return cell.get("inputType") == "1" and row.get("type") != "M"

    # ---

    def _get_catalogs(self):
        """Чтение справочников"""
        catalogs = defaultdict(SchemaCatalog)

        for catalog in self.xml.iterfind("dics/dic"):
            catalog_id = catalog.attrib.get("id")

            for term in catalog.iterfind("term"):
                term_id = term.attrib.pop("id")

                catalogs[catalog_id].set(term_id)

                for dic_id, dic_value in term.attrib.items():
                    catalogs[catalog_id][term_id][dic_id].add(dic_value)

            catalogs[catalog_id].sort()
        return catalogs

    def _init_validators(self):
        """Инициализация валидаторов"""
        return (
            AttrValidator(self),
            TitleValidator(self),
            FormatValidator(self),
            ControlValidator(self),
        )

    def validate(self, report):
        """Валидация отчёта"""
        try:
            for validator in self.validators:
                if not validator.validate(report):
                    self._errors_handle(validator)
                    break
        except Exception:
            self.errors.append(
                {
                    "code": "0.0",
                    "name": "Непредвиденная ошибка",
                    "description": "Не удалось выполнить проверку",
                    "level": 0,
                }
            )
            print("Unexpected Error", traceback.format_exc())
        finally:
            return self.errors

    def _errors_handle(self, validator):
        """Форматирование ошибок"""
        for error in validator.errors:
            self.errors.append(
                {
                    "code": f"{validator.code}.{error.code}",
                    "name": validator.name,
                    "description": error.description,
                    "level": error.level,
                }
            )
