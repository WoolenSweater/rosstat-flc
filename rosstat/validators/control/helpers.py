from enum import Enum


class Formula(Enum):
    CONDITION = 0
    RULE = 1


class Control:
    def __init__(self, control):
        self.id = control.get("id")
        self.name = control.get("name")

        self.rule = control.get("rule")
        self.condition = control.get("condition")
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
