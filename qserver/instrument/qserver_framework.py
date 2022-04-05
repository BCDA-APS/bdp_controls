
"""
Define devices and plans for bluesky-queueserver
"""

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from . import iconfig
import bluesky
import databroker

cat = databroker.catalog[iconfig["DATABROKER_CATALOG"]]
RE = bluesky.RunEngine({})
RE.subscribe(cat.v1.insert)
