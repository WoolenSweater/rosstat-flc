def _build_periods():
    for ptype in {1, 2, 4, 12, 36, 56}:
        for pnum in range(1, min(ptype + 1, 54)):
            yield int(f"{ptype}{pnum:02}")


NORMAL_PERIODS = set(_build_periods())


class PeriodInspector:
    def __init__(self, schema):
        self.idp = schema.idp

        self.years = self.__get_years(schema.catalogs)
        self.periods = self.__get_periods(schema.catalogs)

    def __repr__(self):
        return (
            f"<PeriodInspector "
            f"idp={self.idp} "
            f"years={self.years} "
            f"periods={self.periods}>"
        )

    def __get_years(self, catalogs):
        """Получение годов из справочника"""
        years = catalogs.get("s_year") or catalogs.get("s_god")

        return years.get("ids")

    def __get_periods(self, catalogs):
        """Получение периодов и приведение их числу"""
        periods = catalogs.get("s_time") or catalogs.get("s_mes")

        return {int(period) for period in periods.get("ids")}

    # ---

    def recode_period(self, report):
        """Разбор формата периода"""
        if report.period_raw in NORMAL_PERIODS:
            report.period_num = report.period_raw % 100
            report.period_type = report.period_raw // 100
        else:
            report.period_num = report.period_raw
            report.period_type = self.idp

    def validate_idp(self, report):
        """Проверка типа периода"""
        return report.period_type == self.idp

    def validate_period(self, report):
        """Проверка номера периода"""
        return (
            report.period_raw in self.periods
            or report.period_num in self.periods
            or report.period_num <= len(self.periods)
        )
