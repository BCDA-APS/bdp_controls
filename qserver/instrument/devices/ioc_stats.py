"""
IOC statistics: synApps iocStats
"""

# fmt: off
__all__ = [
    "gp_stats",
    # "ad_stats", 
]
# fmt: on

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from .. import iconfig
from ophyd import Component, Device, EpicsSignalRO


class IocInfoDevice(Device):

    iso8601 = Component(EpicsSignalRO, "iso8601")
    uptime = Component(EpicsSignalRO, "UPTIME")


gp_stats = IocInfoDevice(iconfig["IOC_PREFIX_GP"], name="gp_stats")

# Too bad, this ADSimDetector does not have iocStats
# ad_stats = IocInfoDevice("ad:", name="ad_stats")
