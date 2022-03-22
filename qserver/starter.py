"""
Load devices and plans for bluesky queueserver.
"""

import pathlib, sys
sys.path.append(
    str(pathlib.Path(__file__).absolute().parent)
)

from instrument import iconfig
from instrument.qserver import *
import pyRestTable

devices = (
    ad_x_calc,
    ad_y_calc,
    adsimdet,
    gp_stats,
    image_file_created,
    incident_beam_calc,
    incident_beam,
    samplexy,
    shutter,
)


def startup_report():
    print(f"{iconfig = }")

    table = pyRestTable.Table()
    table.labels = "device/object connected?".split()
    for _obj in devices:
        _obj.wait_for_connection()
        table.addRow((_obj.name, _obj.connected))
    print(table)


startup_report()
