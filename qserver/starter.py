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
    table = pyRestTable.Table()
    table.labels = "key value".split()
    for k, v in sorted(iconfig.items()):
        table.addRow((k, v))
    print("instrument configuration (iconfig):")
    print(table)

    table = pyRestTable.Table()
    table.labels = "device/object connected? prefix/pvname".split()
    for _obj in devices:
        _obj.wait_for_connection()
        p = ""
        for aname in "pvname prefix".split():
            if hasattr(_obj, aname):
                p = getattr(_obj, aname)
        table.addRow((_obj.name, _obj.connected, p))
    print("Devices and signals:")
    print(table)


startup_report()
