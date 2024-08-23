import re

from ..exceptions import SpecNotInDictError, SpecValueError
from .base import BaseFormatInspector

vld_pattern = re.compile(r"(\w+)=#\d+,\d+,(\w+)")


class SpecInspector(BaseFormatInspector):
    def check(self, row, specs, spec_key):
        if self.vld_type == "4":
            self._check_spec_unrelated(row, spec_key)
        elif self.vld_type == "5":
            self._check_spec_related(row, spec_key, specs)

    # ---

    def _check_spec_unrelated(self, row, spec_key):
        """Проверка на вхождение в приложение к справочнику"""
        if row.get_spec(spec_key) not in self.catalogs[self.vld_param]:
            raise SpecNotInDictError()

    def _check_spec_related(self, row, spec_key, specs):
        """Проверка на вхождение в справочник и связь с главной спецификой"""
        ctx_dic, ctx_col = vld_pattern.match(self.vld_param).groups()

        cur_spec = row.get_spec(spec_key)
        ctx_spec = row.get_spec(self.__get_spec_by_col(specs, ctx_col))

        try:
            if ctx_spec not in self.catalogs[self.dic_name][cur_spec][ctx_dic]:
                raise SpecValueError()
        except KeyError:
            raise SpecValueError()

    def __get_spec_by_col(self, specs, col_code):
        """Получение ключа специфики по коду колонки"""
        return next(key for key, col in specs.items() if col == col_code)
