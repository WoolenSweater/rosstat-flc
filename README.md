# Rosstat FLC 2 [Beta]

![PyPI - License](https://img.shields.io/pypi/l/rosstat-flc)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rosstat-flc)

---

Инструмент для форматно-логического контроля отчетности, отправляемой в Росстат (ФСГС).

Документация, описывающая формат отчётности, структуру элементов шаблона и язык описания контролей - [Приказ Росстата от 28.10.2010 №372](http://www.consultant.ru/document/cons_doc_LAW_115689/)

Список изменений - [CHANGELOG](CHANGELOG.md)

## Установка
```bash
poetry add git+https://github.com/WoolenSweater/rosstat-flc.git#2.0.0
```

## Зависимости
* [lark](https://github.com/lark-parser/lark)
* [lxml](https://github.com/lxml/lxml)
* [numpy](https://github.com/numpy/numpy)
* [multidict](https://github.com/aio-libs/multidict)

## Использование
```python
from rosstat.flc import parse_schema, parse_report

# На вход передаются ElementTree, Element, bytes, file name/path, или file-like объекты

schema = parse_schema('schema.xml')
report = parse_report('report.xml', alerts=True)

for result in schema.validate(report):
    print(result)

# {'code': '4.30', 'name': 'Проверка контролей', 'description': 'XML Подраздел 2 стр. 201-202 гр.3 = "1" или "2", при хотя бы одной из стр. 105,106,108,109 гр.3 = 1; слева 1.0 <= справа 0.0 разница 1.0', 'level': 1}
# {'code': '4.60', 'name': 'Проверка контролей', 'description': 'XML Подраздел 2 стр. 203 гр. 3 = "1" или "2", или "3", или "4", или "5", или "6", при хотя бы одной из стр. 105,106,108,109 гр.3 = 1; слева 1.0 <= справа 0.0 разница 1.0', 'level': 1}
```

Результат проверки всегда список. При успешной проверке список будет пустой.

Если на одном из этапов проверки будут выявлены ошибки, проверка будет прервана и вернутся все ошибки обнаруженные на этом этапе.

С блоками проверок их порядком и описанием ошибок можно ознакомиться [здесь](docs/docs.md).

Флаг `alerts` определяет будут ли выводится предупреждения о пропуске контролей с проверками за прошлый период (эти проверки невозможно реализовать не имея доступа к ранее сформированному отчёту).

Поле `level` в результатах означает уровень проверки. 1 - ошибка, 0 - предупреждение.
