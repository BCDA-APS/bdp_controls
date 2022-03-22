"""
shutter
"""

__all__ = [
    "shutter",
]

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

# from ..iconfig_dict import iconfig
import apstools.devices

shutter = apstools.devices.SimulatedApsPssShutterWithStatus(
    name="shutter", labels=("shutters",)
)

# shutter simulator needs short recovery time after moving
shutter.delay_s = 0.05

# TODO: suspender?