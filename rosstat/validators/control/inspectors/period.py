import re

from ..exceptions import PeriodExprError

rebuild_pattern = re.compile(r"(\d+)")


class PeriodInspector:
    def __init__(self, control):
        self.clause = control.period

    def __repr__(self):
        return f"<PeriodInspector clause={self.clause}>"

    def check(self, report):
        if self.clause:
            return self.eval(self._rebuild_clause(report))
        return True

    def _rebuild_clause(self, report):
        """Перестроение выражения проверки периода"""
        return rebuild_pattern.sub(
            lambda match: str(int(match.group(0))),
            self.clause.lower()
            .replace("=", "==")
            .replace("<>", "!=")
            .replace("&np", report.period_code),
        )

    def eval(self, expr):
        """Вычисление выражения"""
        try:
            return eval(expr)
        except SyntaxError:
            raise PeriodExprError()
