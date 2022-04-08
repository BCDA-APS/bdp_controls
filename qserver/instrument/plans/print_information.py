"""
Print information about the instrument.
"""

__all__ = """
    information
    print_positioners
    print_image_file_name
""".split()

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)


from .. import iconfig
from ..devices import image_file_created
from ..devices import incident_beam
from ..devices import samplexy
from ..devices import shutter
from bluesky import plan_stubs as bps
import datetime
import pathlib
import pyRestTable


def _positions():
    """Return a dictionary with positioners and values."""
    info = {}
    for o in (samplexy.coarse.x, samplexy.coarse.y):
        info[f"{o.name}"] = o.position
    for o in (samplexy.fine.x, samplexy.fine.y):
        info[f"{o.name}"] = o.get()
    return info


def information():
    """Print the full information table."""
    yield from bps.null()  # MUST yield something

    table = pyRestTable.Table()

    info = {}
    info["instrument_name"] = iconfig["RUNENGINE_METADATA"]["instrument_name"]
    info["catalog"] = iconfig["DATABROKER_CATALOG"]
    info["beam"] = incident_beam.get()
    info["shutter"] = shutter.state
    info.update(_positions())
    for o in (samplexy.coarse.x, samplexy.coarse.y):
        info[f"{o.name}_pv"] = o.prefix
        info[f"{o.name}_units"] = o.egu
        info[f"{o.name}_setpoint"] = o.user_setpoint.get()
        info[f"{o.name}_velocity"] = o.velocity.get()
        info[f"{o.name}_limit_high"] = o.high_limit_travel.get()
        info[f"{o.name}_limit_low"] = o.low_limit_travel.get()
    for o in (samplexy.fine.x, samplexy.fine.y):
        info[f"{o.name}_pv"] = o.pvname
        info[f"{o.name}_units"] = o.metadata["units"]
        info[f"{o.name}_limit_high"] = o.limits[1]
        info[f"{o.name}_limit_low"] = o.limits[0]
    p = pathlib.Path(image_file_created.get())
    info["last_image_file_created"] = f"{p}"
    info["last_image_file_created_exists"] = p.exists()

    table.labels = "key value".split()
    for k, v in info.items():
        table.addRow((k, v))

    print(f"Instrument Configuration: {datetime.datetime.now()}")
    print(table)


def print_image_file_name():
    """Print the name of the last image file that was created."""
    yield from bps.null()  # MUST yield something
    print(f"image_file {image_file_created.get()}")


def print_positioners():
    """Print the positioners' table."""
    yield from bps.null()  # MUST yield something

    table = pyRestTable.Table()

    info = _positions()

    table.labels = "key value".split()
    for k, v in info.items():
        table.addRow((k, v))

    print(f"Positioners: {datetime.datetime.now()}")
    print(table)
