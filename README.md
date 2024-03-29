# РосСтат ФЛК

![PyPI - License](https://img.shields.io/pypi/l/rosstat-flc)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rosstat-flc)

---

Инструмент для форматно-логического контроля отчетности, отправляемой в РосСтат.

Документация описывающая формат отчетности и контроли - [Приказ РосСтата от 28.10.2010 №372](http://www.consultant.ru/document/cons_doc_LAW_115689/)

Список изменений - [CHANGELOG](CHANGELOG.md)

## Установка
```bash
pip install rosstat-flc
```

## Зависимости
* [PLY](https://github.com/dabeaz/ply)
* [lxml](https://github.com/lxml/lxml)

## Использование
```python
from rosstat.flc import parse_schema, parse_report

# На вход передаются ElementTree, Element, bytes, file name/path, или file-like объекты

schema = parse_schema('schema.xml')
report = parse_report('report.xml', skip_warns=True)

for result in schema.validate(report):
    print(result)

# {'code': '4.30', 'name': 'Проверка контролей', 'description': 'XML Подраздел 2 стр. 201-202 гр.3 = "1" или "2", при хотя бы одной из стр. 105,106,108,109 гр.3 = 1; слева 1.0 <= справа 0.0 разница 1.0', 'level': 1}
# {'code': '4.60', 'name': 'Проверка контролей', 'description': 'XML Подраздел 2 стр. 203 гр. 3 = "1" или "2", или "3", или "4", или "5", или "6", при хотя бы одной из стр. 105,106,108,109 гр.3 = 1; слева 1.0 <= справа 0.0 разница 1.0', 'level': 1}
```

Результат проверки всегда список. При успешной проверке список будет пустой.

Если на одном из этапов проверки будут выявлены ошибки, проверка будет прервана и вернутся все ошибки обнаруженные на этом этапе.

С блоками проверок их порядком и описанием ошибок можно ознакомиться [здесь](docs/docs.md).

Флаг `skip_warns` определяет будут ли выводится предупреждения о пропуске контролей с проверками за прошлый период (эти проверки невозможно реализовать не имея доступа к ранее сформированному отчёту).

Поле `level` в результатах означает уровень проверки. 1 - ошибка, 0 - предупреждение.
