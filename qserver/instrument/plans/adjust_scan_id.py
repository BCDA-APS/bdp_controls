"""
Control the shutter.
"""

__all__ = ["set_scan_id", ]

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)


from ..epics_signal_config import scan_id_epics
from ..qserver_framework import RE
from bluesky import plan_stubs as bps


def set_scan_id(new_id=0):
    """(Re)Set the scan_id.  default: 0"""
    RE.md["scan_id"] = max(0, new_id)
    if scan_id_epics is None:
        # MUST yield something
        yield from bps.null()
    else:
        yield from bps.mv(scan_id_epics, RE.md["scan_id"])
