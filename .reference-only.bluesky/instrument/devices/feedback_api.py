"""
Support the feedback API
"""

__all__ = [
    "image_file_name_as_written",
]

from ..session_logs import logger

logger.info(__file__)

from ..utils import configuration_dict
from ophyd import EpicsSignal


PV = configuration_dict["HDF5_FILE_NAME_PV"]
image_file_name_as_written = EpicsSignal(
    PV, name="image_file_just_written", string=True
)
