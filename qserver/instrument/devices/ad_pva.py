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
from ophyd.areadetector.plugins import PvaPlugin_V34 as PvaPlugin
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

# adpvadet.stage_sigs["array_callbacks"] = 1  # Enable
adpvadet.cam.stage_sigs["array_callbacks"] = 1  # Enable
adpvadet.cam.stage_sigs["array_counter"] = 0
adpvadet.cam.stage_sigs["input_pv"] = iconfig["PV_PVA_IMAGE"]
adpvadet.pva1.stage_sigs["enable"] = "Enable"
adpvadet.read_attrs.append("pva1")

"""
def acquire(n=10):
    import time
    adpvadet.stage()
    adpvadet.cam.acquire.put(1)
    for item in image_file_list(n):
        img2pva.put(item)
        time.sleep(0.05)  # wait 50 ms (!) for PVA to push the image
    adpvadet.cam.acquire.put(0)
    adpvadet.unstage()
"""
