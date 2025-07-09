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

    checkers = (_check_section, _check_rows, _check_columns)

    @classmethod
    def has_value(cls, level, coords):
        for checker, code in zip(cls.checkers, coords):
            if not (level := checker(level, code)):
                return False
        return True
