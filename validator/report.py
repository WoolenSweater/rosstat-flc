class Report:
    def __init__(self, xml_tree):
        self.xml = xml_tree
        self._title = self._read_title()
        self._data = self._read_data()

    def __repr__(self):
        return '<Report title={title}\ndata={data}>'.format(**self.__dict__)

    @property
    def title(self):
        return self._title

    @property
    def data(self):
        return self._data

    def _read_title(self):
        title = {}
        for item in self.xml.xpath('/report/title/item'):
            title[item.attrib['name']] = item.attrib['value']
        return title

    def _read_data(self):
        data = {}
        for section in self.xml.xpath('/report/sections/section'):
            section_code = int(section.attrib['code'])
            data[section_code] = {}

            for row in section.xpath('./row'):
                row_code = int(row.attrib['code'])
                data[section_code][row_code] = {}
                data[section_code][row_code].update(self._read_row_specs(row))

                for col in row.xpath('./col'):
                    col_code = int(col.attrib['code'])
                    data[section_code][row_code][col_code] = col.text
        return data

    def _read_row_specs(self, row):
        specs = {}
        for idx in range(1, 4):
            spec_name = f's{idx}'
            if row.attrib.get(spec_name):
                specs[spec_name] = row.attrib[spec_name]
        return specs
