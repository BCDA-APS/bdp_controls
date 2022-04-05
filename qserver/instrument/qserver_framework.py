"""
Define RE for bluesky-queueserver
"""

__all__ = ["RE", ]

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from . import iconfig
import apstools
import bluesky
import bluesky_queueserver
import databroker
import datetime
import epics
import getpass
import h5py
import intake
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
RE = bluesky.RunEngine({})
RE.subscribe(cat.v1.insert)

RE.md["databroker_catalog"] = cat.name
RE.md["login_id"] = USERNAME + "@" + HOSTNAME
RE.md.update(iconfig.get("RUNENGINE_METADATA", {}))
RE.md["versions"] = versions
RE.md["pid"] = os.getpid()