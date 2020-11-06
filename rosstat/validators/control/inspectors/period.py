import re
from .exceptions import PeriodExprError

in_pattern = re.compile(r'^\(&npin\(([\d,]+)\)\)$')
cp_pattern = re.compile(r'^&np([=<>]+)(\d+)$')


class PeriodInspector:
    def __init__(self, control):
        self.period_clause = control.attrib.get('periodClause', '').strip()

    def __repr__(self):
        return '<PeriodInspector clause={period_clause}>'.format(
            **self.__dict__)

    def _normolize_period_clause(self):
        '''Нормализация правила'''
        self.period_clause = self.period_clause.replace(' ', '').lower()
        self.period_clause = self.period_clause.replace('and', ' and ')
        self.period_clause = self.period_clause.replace('or', ' or ')

    def check(self, report):
        if not self.period_clause:
            return True

        self._normolize_period_clause()

        if 'in' in self.period_clause:
            return self._check_in(report)
        else:
            return self._check_logic(report)

    def _eval_regex(self, pattern, string):
        '''Разбор формулы проверки периода с помощью регулярки'''
        result = pattern.match(string)
        if result is None:
            raise PeriodExprError()
        return result

    def _check_in(self, report):
        '''Проверка на вхождение в список'''
        clause_parts = self._eval_regex(in_pattern, self.period_clause)

        clause = '{0} in ({1},)'.format(report.period_code,
                                        clause_parts.group(1))
        return eval(clause)

    def _check_logic(self, report):
        '''Проверка комплексного логического условия'''
        clause_parts = []
        for cluase_part in self.period_clause.strip('()').split():
            if cluase_part in ('or', 'and'):
                clause_parts.append(cluase_part)
                continue

            op, num = self._eval_regex(cp_pattern, cluase_part).group(1, 2)
            op = '==' if op == '=' else op
            clause_parts.append(f'{report.period_code} {op} {num}')

        clause = ' '.join(clause_parts)
        return eval(clause)
