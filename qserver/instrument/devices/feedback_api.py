"""
Support the feedback API
"""

__all__ = [
    "image_file_created",
]

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from .. import iconfig
from ophyd import EpicsSignal


PV = iconfig["HDF5_FILE_NAME_PV"]
image_file_created = EpicsSignal(
    PV, name="image_file_created", string=True
)
