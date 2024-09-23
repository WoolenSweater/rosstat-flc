from ..exceptions import (
    ValueBadFormat,
    ValueLengthError,
    ValueNotInDictError,
    ValueNotInListError,
    ValueNotInRangeError,
    ValueNotNumberError,
)
from .base import BaseFormatInspector


class ValueInspector(BaseFormatInspector):
    @staticmethod
    def _is_num(value, limits):
        """Проверка длины целой и дробной частей числового значения поля"""
        try:
            float(value)
        except ValueError:
            raise ValueNotNumberError()

        for part, limit in zip(value.split("."), limits.split(",")):
            if len(part) > int(limit):
                raise ValueBadFormat()

    @staticmethod
    def _is_chars(value, limit):
        """Проверка длины символьного значения поля"""
        if len(value) > int(limit):
            raise ValueLengthError()

    # ---

    def check(self, col):
        if col.value is not None:
            self._check_format(col.value)
            self._check_value(col.value)

    def _check_format(self, value):
        """Разбор "формулы" проверки формата и проверка"""
        func, args = self.format.strip(" )").split("(")
        if func == "N":
            self._is_num(value, args)
        elif func == "C":
            self._is_chars(value, args)

    def _check_value(self, value):
        if self.vld_type == "1":
            self.__check_value_catalog(value)
        elif self.vld_type == "2":
            self.__check_value_range(value)
        elif self.vld_type == "3":
            self.__check_value_list(value)

    # ---

    def __check_value_catalog(self, value):
        """Проверка на вхождение в справочник"""
        if value not in self.catalogs[self.dic_name]:
            raise ValueNotInDictError()

    def __check_value_range(self, value):
        """Проверка на вхождение в диапазон"""
        start, end = self.vld_param.split("-")
        if not (float(start) <= float(value) <= float(end)):
            raise ValueNotInRangeError()

    def __check_value_list(self, value):
        """Проверка на вхождение в список"""
        if value not in self.vld_param.split(","):
            raise ValueNotInListError()
