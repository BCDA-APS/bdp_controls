"""
Define devices and plans for bluesky-queueserver
"""

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

# most of these imports *provision* the RE environment with devices and plans
from . import iconfig

import ophyd
ophyd.set_cl("caproto")
import os
print(f"environment EPICS_CA_ADDR_LIST={os.environ.get('EPICS_CA_ADDR_LIST')}")

# # DIAGNOSTIC use only
# for item in "ophyd ophyd.control_layer ophyd.event_dispatcher ophyd.objects".split():
#     logging.getLogger(f"{item}").setLevel(logging.DEBUG)

logging.getLogger("caproto").setLevel(logging.ERROR)  # silence non-errors from caproto

from .epics_signal_config import scan_id_epics
from .qserver_framework import *

from .devices import *
from .plans import *

from .utils import *
from ophyd import Device
from ophyd import Signal
import inspect
import pyRestTable


def print_devices_and_signals():
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


def print_plans():
    glo = globals().copy()
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


if iconfig.get("APS_IN_BASELINE", False):
    sd.baseline.append(aps)
