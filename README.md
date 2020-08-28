# РосСтат ФЛК [WIP]

Форматно-логический контроль отчетности РосСтата.

Документация описывающая формат отчетности и контроли - [Приказ РосСтата от 28.10.2010 №372](http://www.consultant.ru/document/cons_doc_LAW_115689/)

**Ранние наработки. Не для использования в продакшене! [CHANGELOG](CHANGELOG.md)**

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

schema = parse_schema('xml_schema.xml')
report = parse_report('xml_report.xml')

for result in schema.validate(report):
    print(result)

# 30 XML Подраздел 2 стр. 201-202 гр.3 = "1" или "2", при хотя бы одной из стр. 105,106,108,109 гр.3 = 1; слева 1.0 <= справа 0.0 разница 1.0; обязательность да
# 60 XML Подраздел 2 стр. 203 гр. 3 = "1" или "2", или "3", или "4", или "5", или "6", при хотя бы одной из стр. 105,106,108,109 гр.3 = 1; слева 1.0 <= справа 0.0 разница 1.0; обязательность да
```