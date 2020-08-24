import re
from ..exceptions import ValidationError

in_pattern = re.compile(r'^\(&NP\s?in\s?\(([\d, ]+)\)\)$', re.I)
sp_pattern = re.compile(r'^\(&NP\s?([><=]+)\s?(\d+)\)$', re.I)
lg_pattern = re.compile(r'^\(&NP\s?([><=]+)\s?(\d+)\s?(and|or)\s?'
                        r'&NP\s?([><=]+)\s?(\d+)\)$', re.I)


class PeriodClause:
    def __init__(self, control, _id):
        self.id = _id
        self.period_clause = control.attrib.get('periodClause', '').strip()

    def __repr__(self):
        return '<PeriodClause clause={period_clause}>'.format(**self.__dict__)

    def check(self, report):
        if not self.period_clause:
            return True

        if 'in' in self.period_clause:
            return self._check_in(report)
        elif 'or' in self.period_clause or 'and' in self.period_clause:
            return self._check_logic(report)
        else:
            return self._check_simple(report)

    def _eval_regex(self, pattern, string):
        result = pattern.match(string)
        if result is None:
            raise ValidationError(f'ошибка разбора формулы проверки '
                                  f'периодичности {self.id}')
        return result

    def _check_in(self, report):
        clause_parts = self._eval_regex(in_pattern, self.period_clause)

        clause = '{0} in ({1})'.format(
            report.period_code, clause_parts.group(1))
        return eval(clause)

    def _check_logic(self, report):
        clause_parts = self._eval_regex(lg_pattern, self.period_clause)

        l_op = '==' if clause_parts.group(1) == '=' else l_op
        r_op = '==' if clause_parts.group(4) == '=' else r_op

        clause = '{0} {1} {3} {4} {0} {2} {5}'.format(
            report.period_code, l_op, r_op, *clause_parts.group(2, 3, 5))
        return eval(clause)

    def _check_simple(self, report):
        clause_parts = self._eval_regex(sp_pattern, self.period_clause)

        op = '==' if clause_parts.group(1) == '=' else op

        clause = '{0} {1} {2}'.format(
            report.period_code, op, clause_parts.group(2))
        return eval(clause)
