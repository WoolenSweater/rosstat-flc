# РосСтат ФЛК

Форматно-логический контроль отчетности РосСтата.

Документация описывающая формат отчетности и контроли - [Приказ РосСтата от 28.10.2010 №372](http://www.consultant.ru/document/cons_doc_LAW_115689/)

**Ранние наработки. Не для использования в продакшене!**

## Зависимости
* [PLY](https://github.com/dabeaz/ply)

## Использование
```python
from parser import parser

dataframe = {1: {4: {101: None, 102: 3, 105: 4}}}
control = '({[1][4][102]}-1-isnull({[1][4][101]},0))*50/coalesce({[1][4][105]},2)|<=|10'

checker = parser.parse(control)
results = checker.check(dataframe, ctrl_name='(3 - 1 - 0) * 50 / 4 <= 10')

for result in results:
    for failed_control in result.controls:
        print(failed_control)

# Условие "(3 - 1 - 0) * 50 / 4 <= 10" не выполнено, [1][4][101, 102, 105] 25.0 <= [][][] 10.0
```