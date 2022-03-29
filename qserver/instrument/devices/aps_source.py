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

# from ..iconfig_dict import iconfig
import apstools.devices


aps = apstools.devices.ApsMachineParametersDevice(name="aps")

# if iconfig.get("APS_IN_BASELINE", False):
#     from ..framework import sd
#     sd.baseline.append(aps)
