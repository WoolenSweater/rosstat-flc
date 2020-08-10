# РосСтат ФЛК

Форматно-логический контроль отчетности РосСтата.

Документация описывающая формат отчетности и контроли - [Приказ РосСтата от 28.10.2010 №372](http://www.consultant.ru/document/cons_doc_LAW_115689/)

**Ранние наработки. Не для использования в продакшене!**

## Зависимости
* [PLY](https://github.com/dabeaz/ply)
* [lxml](https://github.com/lxml/lxml)

## Использование
```python
from lxml import etree
from validator.controls import parser
from validator.schema import Schema
from validator.report import Report


dataframe = {1: {4: {101: None, 102: 3, 105: 4}}}
control = '({[1][4][102]}-1-isnull({[1][4][101]},0))*50/coalesce({[1][4][105]},2)|<=|10'

checker = parser.parse(control)
results = checker.check(dataframe, precision=2)

for result in results:
    for failed_control in result.controls:
        print(failed_control)

# [1][4][101, 102, 105] 25.0 <= [][][] 10.0

sch = Schema(etree.parse('xml_schema.xml'))
rep = Report(etree.parse('xml_report.xml'))

for result in sch.validate(rep):
    print(result)

# 30 XML Подраздел 2 стр. 201-202 гр.3 = "1" или "2", при хотя бы одной из стр. 105,106,108,109 гр.3 = 1 - Контроль не пройден, [][][] 1.0 <= [2][201, 202][3] 0.0
# 60 XML Подраздел 2 стр. 203 гр. 3 = "1" или "2", или "3", или "4", или "5", или "6", при хотя бы одной из стр. 105,106,108,109 гр.3 = 1 - Контроль не пройден, [][][] 1.0 <= [2][203][3] 0.0
```