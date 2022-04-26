"""
plans that support metadata
"""

__all__ = """
    add_metadata
    add_metadata_kv
    remove_metadata_key
    show_metadata
""".split()

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)


from ..qserver_framework import RE
from bluesky import plan_stubs as bps
import lxml.etree
import pathlib
import pyRestTable


def _make_table(data):
    table = pyRestTable.Table()
    table.labels = "key value".split()
    for k, v in sorted(data.items()):
        if isinstance(v, dict):
            table.addRow((k, _make_table(v)))
        else:
            table.addRow((k, v))
    return table


def add_metadata(**md):
    """
    Add the keyword arguments to the RunEngine metadata.
    """
    yield from bps.null()
    RE.md.update(md)


def add_metadata_kv(key, value):
    """
    Add the keyword arguments to the RunEngine metadata.
    """
    yield from bps.null()
    RE.md[key] = value


def remove_metadata_key(key):
    """
    Remove the key from the RunEngine metadata.
    """
    yield from bps.null()
    if key in RE.md:
        RE.md.pop(key)


def show_metadata():
    """
    Print a table (to the console) with the current RunEngine metadata.
    """
    yield from bps.null()
    if len(RE.md) > 0:
        print(_make_table(RE.md))


def _xml_group(parent, name, nxclass=None):
    """(internal) Make XML group or subgroup."""
    if parent is None:
        g = lxml.etree.Element(name)
    else:
        g = lxml.etree.SubElement(parent, "group")
        g.attrib["name"] = name
    if nxclass is not None:
        g.append(
            _xml_element(
                "attribute",
                name="NX_class",
                value=nxclass,
                type="string",
                source="constant"
            )
        )
    return g


def _xml_element(ename, **kwargs):
    """(internal) Make XML Element."""
    e = lxml.etree.Element(ename)
    for k, v in kwargs.items():
        e.attrib[k] = v
    return e


def create_layout_file(filename, md):
    """(not a plan) Create the HDF5 layout file."""
    root = _xml_group(None, "hdf5_layout")
    entry = _xml_group(root, "entry", "NXentry")
    entry.append(
        _xml_element("attribute", name="default", value="data", type="string", source="constant")
    )
    instrument = _xml_group(entry, "instrument", "NXinstrument")
    detector = _xml_group(instrument, "detector", "NXdetector")
    ds = _xml_element("dataset", name="data", source="detector", det_default="true")
    ds.append(
        _xml_element("attribute", name="target", value="/entry/instrument/detector/data", type="string", source="constant")
    )
    detector.append(ds)
    NDAttributes = _xml_group(detector, "NDAttributes")
    NDAttributes.append(
        _xml_element("dataset", name="ColorMode", ndattribute="ColorMode", source="ndattribute")
    )
    NDAttributes = _xml_group(instrument, "NDAttributes", "NXcollection")
    NDAttributes.attrib["ndattr_default"] = "true"

    metadata = _xml_group(instrument, "BlueskyMetadata", "NXcollection")
    for k, v in md.items():
        if isinstance(v, bool):
            dtype = "int"
            v = {False: 0, True: 1}[v]
        elif isinstance(v, float):
            dtype = "float"
        elif isinstance(v, int):
            dtype = "int"
        elif isinstance(v, str):
            dtype = "string"
        else:
            continue
        # logger.info("RE.md['%s'] = %s (%s)", k, v, dtype)
        metadata.append(
            _xml_element("attribute", name=k, value=f"{v}", type=dtype, source="constant")
        )
    performance = _xml_group(instrument, "performance")
    performance.append(
        _xml_element("dataset", name="timestamp", value="ndattribute")
    )
    data = _xml_group(entry, "data", "NXdata")
    data.append(
        _xml_element("attribute", name="signal", value="data", type="string", source="constant")
    )
    data.append(
        _xml_element("hardlink", name="data", target="/entry/instrument/detector/data")
    )

    path = pathlib.Path(filename)
    tree = lxml.etree.ElementTree(root)
    tree.write(f"{path}", pretty_print=True, xml_declaration=True)
