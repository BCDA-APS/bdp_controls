"""
plans that support metadata
"""

__all__ = """
    add_metadata
    remove_metadata_key
    show_metadata
""".split()

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)


from ..qserver_framework import RE
from bluesky import plan_stubs as bps
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

