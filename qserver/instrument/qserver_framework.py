"""
Define RE for bluesky-queueserver
"""

__all__ = """
    cat
    RE
    sd
""".split()

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from . import iconfig
from .epics_signal_config import epics_scan_id_source
from .epics_signal_config import scan_id_epics
from .dm_setup import BDP_WORKFLOW_OWNER

import apstools
import bluesky
import bluesky_queueserver
import databroker
import epics
import getpass
import h5py
import matplotlib
import numpy
import ophyd
import os
import pyRestTable
import socket
import spec2nexus


HOSTNAME = socket.gethostname() or "localhost"
USERNAME = getpass.getuser() or "queueserver user"

# useful diagnostic to record with all data
versions = dict(
    apstools=apstools.__version__,
    bluesky=bluesky.__version__,
    bluesky_queueserver=bluesky_queueserver.__version__,
    databroker=databroker.__version__,
    epics=epics.__version__,
    h5py=h5py.__version__,
    matplotlib=matplotlib.__version__,
    numpy=numpy.__version__,
    ophyd=ophyd.__version__,
    pyRestTable=pyRestTable.__version__,
    spec2nexus=spec2nexus.__version__,
)

cat = databroker.catalog[iconfig["DATABROKER_CATALOG"]]
if scan_id_epics is None:
    RE = bluesky.RunEngine({})
else:
    RE = bluesky.RunEngine({}, scan_id_source=epics_scan_id_source)
    logger.info(r"RE 'scan_id' uses EPICS PV: {scan_id_epics.pvname}")
RE.subscribe(cat.v1.insert)

RE.md["databroker_catalog"] = cat.name
RE.md["login_id"] = USERNAME + "@" + HOSTNAME
RE.md.update(iconfig.get("RUNENGINE_METADATA", {}))
RE.md["versions"] = versions
RE.md["pid"] = os.getpid()
if scan_id_epics is not None:
    RE.md["scan_id"] = scan_id_epics.get()

# Set up SupplementalData.
sd = bluesky.SupplementalData()
RE.preprocessors.append(sd)
