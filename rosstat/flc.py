from io import BufferedIOBase, BytesIO
from os.path import isfile

from lxml import etree

from .report import Report
from .schema import Schema

parser = etree.XMLParser(
    collect_ids=False,
    load_dtd=False,
    dtd_validation=False,
    remove_blank_text=True,
    remove_pis=True,
    remove_comments=True,
    resolve_entities=False,
)


def _get_xml_etree(source):
    if isinstance(source, (etree._ElementTree, etree._Element)):
        return source
    elif isinstance(source, str) and isfile(source):
        return etree.parse(source, parser=parser)
    elif isinstance(source, bytes):
        return etree.parse(BytesIO(source), parser=parser)
    elif isinstance(source, BufferedIOBase):
        return etree.parse(source, parser=parser)

    raise TypeError(
        f"Expected ElementTree, Element, bytes, file name/path, "
        f"or file-like object, got {source!r}"
    )


def parse_report(source):
    xml_etree = _get_xml_etree(source)
    return Report(xml_etree)


def parse_schema(source, alerts=False):
    xml_etree = _get_xml_etree(source)
    return Schema(xml_etree, alerts=alerts)
