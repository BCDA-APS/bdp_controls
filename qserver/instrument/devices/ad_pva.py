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
from apstools.devices import AD_EpicsFileNameTIFFPlugin
from ophyd import EpicsSignalRO
from ophyd import EpicsSignalWithRBV
from ophyd.areadetector import ADComponent
from ophyd.areadetector import CamBase
from ophyd.areadetector import DetectorBase
from ophyd.areadetector.plugins import PvaPlugin_V34 as PvaPlugin
# from ophyd.areadetector.plugins import TIFFPlugin_V34 as TIFFPlugin


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
    tiff1 = ADComponent(
        AD_EpicsFileNameTIFFPlugin,  # EPICS-controlled file names
        "TIFF1:",
        write_path_template=iconfig["BDP_DATA_DIR"],
    )


IOC = iconfig["IOC_PREFIX_ADPVA"]
adpvadet = PvaDetector(IOC, name="adpvadet")

adpvadet.cam.stage_sigs["acquire"] = 0
adpvadet.cam.stage_sigs["array_callbacks"] = 1  # Enable
adpvadet.cam.stage_sigs["array_counter"] = 0
adpvadet.cam.stage_sigs["input_pv"] = iconfig["PV_PVA_IMAGE"]

adpvadet.pva1.stage_sigs["enable"] = "Enable"

adpvadet.tiff1.stage_sigs["enable"] = "Enable"
adpvadet.tiff1.stage_sigs["auto_increment"] = "Yes"
adpvadet.tiff1.stage_sigs["auto_save"] = "Yes"
adpvadet.tiff1.stage_sigs["file_number"] = 1
adpvadet.tiff1.stage_sigs["queue_size"] = 500
adpvadet.tiff1.stage_sigs["lazy_open"] = 1
# adpvadet.tiff1.stage_sigs["write_file"] = "Write"
adpvadet.tiff1.stage_sigs["capture"] = adpvadet.tiff1.stage_sigs.pop("capture")

adpvadet.read_attrs.append("pva1")
adpvadet.read_attrs.append("tiff1")
