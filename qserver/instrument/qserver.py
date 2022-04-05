"""
Define devices and plans for bluesky-queueserver
"""

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from . import iconfig
from .qserver_framework import *
from .devices import *
from .plans import *


if iconfig.get("APS_IN_BASELINE", False):
    sd.baseline.append(aps)
