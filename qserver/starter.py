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

print(f"{iconfig = }")

table = pyRestTable.Table()
table.labels = "device/object connected?".split()
for obj in devices:
    obj.wait_for_connection()
    table.addRow((obj.name, obj.connected))
    # print(f"{obj.name}.connected = {obj.connected}")
print(table)
