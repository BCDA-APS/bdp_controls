"""
APS only: connect with facility information
"""

__all__ = [
    "aps",
]

from ..session_logs import logger

logger.info(__file__)

from ..framework import sd
from ..utils import configuration_dict
import apstools.devices


aps = apstools.devices.ApsMachineParametersDevice(name="aps")

if configuration_dict.get("APS_IN_BASELINE", False):
    sd.baseline.append(aps)
