class ReqsChecker:
    @staticmethod
    def _check_section(report, code):
        return report.get_section(code)

    @staticmethod
    def _check_rows(section, code):
        if section.has_rows(code):
            return section.get_rows(code)

    @staticmethod
    def _check_columns(rows, code):
        return all(row.get_column(code) for row in rows)

    checkers = {
        0: _check_section,
        1: _check_rows,
        2: _check_columns
    }

    @classmethod
    def has_value(cls, level, coords):
        for idx, code in enumerate(coords):
            if not (level := cls.checkers[idx](level, code)):
                return False
        return True
