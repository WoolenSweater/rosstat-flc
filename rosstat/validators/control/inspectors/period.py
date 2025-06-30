import re

from ..exceptions import PeriodExprError

rebuild_pattern = re.compile(r"(0+\d+)|\((\d+)\)")


class PeriodInspector:
    def __init__(self, control):
        self.clause = control.period

    def __repr__(self):
        return f"<PeriodInspector clause={self.clause}>"

    def replacer(self, match):
        match match.groups():
            case str() as num, None:
                return str(int(num))
            case None, str() as num:
                return f"({int(num)},)"

    def check(self, report):
        if self.clause:
            return self.eval(self._rebuild_clause(report))
        return True

    def _rebuild_clause(self, report):
        """Перестроение выражения проверки периода"""
        return rebuild_pattern.sub(
            self.replacer,
            self.clause.lower()
            .replace("=", "==")
            .replace("<>", "!=")
            .replace("&np", str(int(report.period_num))),
        )

    def eval(self, expr):
        """Вычисление выражения"""
        try:
            return eval(expr)
        except SyntaxError:
            raise PeriodExprError()
