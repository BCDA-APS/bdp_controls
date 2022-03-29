"""
Load devices and plans for bluesky queueserver.
"""

import pathlib, sys

sys.path.append(
    str(pathlib.Path(__file__).absolute().parent)
)

from instrument import iconfig
from instrument.qserver import *
from ophyd import Device, Signal
import inspect
import pyRestTable


def startup_report():
    """Show instrument data on startup"""
    table = pyRestTable.Table()
    table.labels = "key value".split()
    for k, v in sorted(iconfig.items()):
        table.addRow((k, v))
    if len(table.rows) > 0:
        print("")
        print("Instrument configuration (iconfig):")
        print(table)

    glo = globals().copy()

    table = pyRestTable.Table()
    table.labels = "device/object pvprefix/pvname connected?".split()
    for k, v in sorted(glo.items()):
        if isinstance(v, (Device, Signal)) and not k.startswith("_"):
            v.wait_for_connection()
            p = ""
            for aname in "pvname prefix".split():
                if hasattr(v, aname):
                    p = getattr(v, aname)
            table.addRow((v.name, p, v.connected))
    if len(table.rows) > 0:
        print("Table of Devices and signals:")
        print(table)

    plans = [
        k
        for k, v in sorted(glo.items()) 
        if inspect.isgeneratorfunction(v)
    ]
    if len(plans) > 0:
        print("List of Plans:")
        for k in plans:
            print(f"* {k}{inspect.signature(glo[k])}")
        print("")


startup_report()
