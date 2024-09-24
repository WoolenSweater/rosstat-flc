from enum import IntEnum

SPEC_KEYS = ("s1", "s2", "s3")


class SpecType(IntEnum):
    CMN = 0
    ROW = 1
    COL = 2


class FormulaType(IntEnum):
    CONDITION = 0
    RULE = 1


class Control:
    def __init__(self, control):
        self.id = control.get("id")
        self.name = control.get("name")

        self.rule = control.get("rule").strip()
        self.condition = control.get("condition").strip()
        self.period = control.get("periodClause")

        self.tip = int(control.get("tip", "1"))
        self.fault = float(control.get("fault", "0"))
        self.precision = int(control.get("precision", "2"))

    def __repr__(self):
        return (
            f"<Control "
            f"id={self.id} "
            f"name={self.name} "
            f"period={self.period} "
            f"condition={self.condition} "
            f"rule={self.rule} "
            f"tip={self.tip} "
            f"fault={self.fault} "
            f"precision={self.precision}>"
        )
