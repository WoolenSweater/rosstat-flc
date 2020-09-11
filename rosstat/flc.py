from lxml import etree
from .report import Report
from .validator.schema import Schema


def _get_xml_etree(source):
    if isinstance(source, str):
        return etree.parse(source)
    return source


def parse_report(source):
    xml_etree = _get_xml_etree(source)
    return Report(xml_etree)


def parse_schema(source, skip_warns=False):
    xml_etree = _get_xml_etree(source)
    return Schema(xml_etree, skip_warns=skip_warns)
