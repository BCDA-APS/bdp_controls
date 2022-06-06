"""
Bluesky measurement plans for the BPD 2022 project demonstration: trajectory scans
"""

__all__ = []

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from .. import iconfig
from ..devices import adsimdet
from ..devices import fastxy
from ..devices import image_file_created
from ..devices import incident_beam
from ..devices import shutter
from ..qserver_framework import RE

# TODO: setup AD for multiple frames/acquisition
# create plan: start AD, start XY get streaming (PVA) images
