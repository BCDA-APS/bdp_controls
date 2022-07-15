"""
EPICS area_detector ADpvaDriver
"""

__all__ = """
    adpvadet
""".split()

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)


from .. import iconfig
from ophyd.areadetector import ADComponent
from ophyd.areadetector import CamBase
from ophyd.areadetector import DetectorBase
from ophyd.areadetector import PvaPlugin_v34 as PvaPlugin
from ophyd import EpicsSignalWithRBV
from ophyd import EpicsSignalRO


class PvaDetectorCam(CamBase):
    """PvaDriver pulls new image frames via PVAccess."""
    # does not exist in ophyd.areadetector.cam
    _html_docs = ['pvaDriverDoc.html']
    input_pv = ADComponent(EpicsSignalWithRBV, "PvName", string=True)
    input_connection = ADComponent(EpicsSignalRO, "PvConnection_RBV", string=True)
    overrun_counter = ADComponent(EpicsSignalWithRBV, "OverrunCounter")


class PvaDetector(DetectorBase):
    """Pull image frames from PVA source, publish via PVA plugin"""
    cam = ADComponent(PvaDetectorCam, "cam1:")
    pva1 = ADComponent(PvaPlugin, "Pva1:")


IOC = iconfig["IOC_PREFIX_ADPVA"]
adpvadet = PvaDetector(IOC, name="adpvadet")
