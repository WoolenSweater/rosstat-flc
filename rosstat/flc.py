from os.path import isfile
from io import BytesIO, BufferedIOBase
from lxml import etree
from .report import Report
from .schema import Schema


def _get_xml_etree(source):
    if isinstance(source, (etree._ElementTree, etree._Element)):
        return source
    elif isinstance(source, str) and isfile(source):
        return etree.parse(source)
    elif isinstance(source, bytes):
        return etree.parse(BytesIO(source))
    elif isinstance(source, BufferedIOBase):
        return etree.parse(source)

    raise TypeError(f'Expected ElementTree, Element, bytes, file name/path, '
                    f'or file-like object, got {source!r}')


def parse_report(source):
    xml_etree = _get_xml_etree(source)
    return Report(xml_etree)


def parse_schema(source, skip_warns=False):
    xml_etree = _get_xml_etree(source)
    return Schema(xml_etree, skip_warns=skip_warns)
