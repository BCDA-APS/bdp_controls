"""
APS only: connect with facility information
"""

__all__ = [
    "aps",
]

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from .. import iconfig
import apstools.devices

try:
    aps = apstools.devices.ApsMachineParametersDevice(name="aps")
    aps.wait_for_connection(timeout=5)
except Exception as exc:
    aps = None
    iconfig["APS_IN_BASELINE"] = False
    logger.warning("Could not create 'aps' object: %s", exc)
