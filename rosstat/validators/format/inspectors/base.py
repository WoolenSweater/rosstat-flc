class BaseFormatInspector:
    def __init__(self, catalogs, params):
        self.catalogs = catalogs

        self.format = params.get("format")

        self.vld_type = params.get("vldType")
        self.vld_param = params.get("vld")
        self.dic_name = params.get("dic")

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} "
            f"vld_type={self.vld_type} "
            f"vld_param={self.vld_param} "
            f"dic_name={self.dic_name} "
            f"format={self.format}>"
        )
