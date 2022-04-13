"""
EPICS area_detector ADSimDetector
"""

__all__ = """
    adsimdet
    change_ad_simulated_image_parameters
    dither_ad_peak_position
    dither_ad_off
    dither_ad_on
""".split()

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from .. import iconfig
from .samplexy_stage import samplexy
from .calculation_records import incident_beam_calc
from .calculation_records import ad_x_calc, ad_y_calc
from ophyd import ADComponent
from ophyd import DetectorBase
from ophyd import EpicsSignal
from ophyd import EpicsSignalWithRBV
from ophyd import SimDetectorCam
from ophyd import SingleTrigger
from ophyd.areadetector.filestore_mixins import FileStoreHDF5IterativeWrite
from ophyd.areadetector.plugins import HDF5Plugin_V34
from ophyd.areadetector.plugins import ImagePlugin_V34
from ophyd.areadetector.plugins import PvaPlugin_V34
import numpy as np
import pathlib



AD_IOC_MOUNT_PATH = pathlib.Path(iconfig["ADIOC_IMAGE_ROOT"])
BLUESKY_MOUNT_PATH = pathlib.Path(iconfig["BLUESKY_IMAGE_ROOT"])
IMAGE_SUBDIR = iconfig["AD_IMAGE_SUBDIR"]

# MUST end with a `/` (which pathlib will not provide)
WRITE_PATH_TEMPLATE = f"{AD_IOC_MOUNT_PATH / IMAGE_SUBDIR}/"
READ_PATH_TEMPLATE = f"{BLUESKY_MOUNT_PATH / IMAGE_SUBDIR}/"


class MyFixedCam(SimDetectorCam):
    pool_max_buffers = None
    offset = ADComponent(EpicsSignalWithRBV, "Offset")
    wait_for_plugins = ADComponent(
        EpicsSignal, "WaitForPlugins", kind="omitted", string=True
    )


class MyHDF5Plugin(FileStoreHDF5IterativeWrite, HDF5Plugin_V34):
    """
    Add data acquisition methods to HDF5Plugin.

    * ``stage()`` - prepare device PVs befor data acquisition
    * ``unstage()`` - restore device PVs after data acquisition
    * ``generate_datum()`` - coordinate image storage metadata
    """

    xml_file_name = ADComponent(
        EpicsSignalWithRBV, "XMLFileName", string=True, kind="config"
    )

    # fixes one problem, MUST end with path delimiter
    @property
    def write_path_template(self):
        rootp = self.reg_root
        delimiter = "/"
        if self.path_semantics == 'posix':
            ret = pathlib.PurePosixPath(self._write_path_template)
        elif self.path_semantics == 'windows':
            ret = pathlib.PureWindowsPath(self._write_path_template)
            delimiter = "\\"
        elif self.path_semantics is None:
            # We are forced to guess which path semantics to use.
            # Guess that the AD driver is running on the same OS as this client.
            ret = pathlib.PurePath(self._write_path_template)
        else:
            # This should never happen, but just for the sake of future-proofing...
            raise ValueError(f"Cannot handle path_semantics={self.path_semantics}")

        if self._read_path_template is None and rootp not in ret.parents:
            if not ret.is_absolute():
                ret = rootp / ret
            else:
                raise ValueError(
                    ('root: {!r} in not consistent with '
                     'read_path_template: {!r}').format(rootp, ret))

        return f"{ret}{delimiter}"  # THIS is the fix, MUST end with delimiter

    @write_path_template.setter
    def write_path_template(self, val):
        self._write_path_template = val


class MySimDetector(SingleTrigger, DetectorBase):
    """ADSimDetector"""

    cam = ADComponent(MyFixedCam, "cam1:")
    image = ADComponent(ImagePlugin_V34, "image1:")
    hdf1 = ADComponent(
        MyHDF5Plugin,
        "HDF1:",
        write_path_template=WRITE_PATH_TEMPLATE,
        read_path_template=READ_PATH_TEMPLATE,
    )
    pva = ADComponent(PvaPlugin_V34, "Pva1:")


def change_ad_simulated_image_parameters():
    """
    Make the image be a "peak" (simulate a diffraction spot).

    Randomly-placed, random max, random noise

    Not a bluesky plan (uses blocking calls).
    """
    cam = adsimdet.cam
    cam.reset.put(1)
    cam.sim_mode.put(1)  # Peaks
    cam.gain.put(100 + 100 * np.random.random())
    cam.offset.put(10 * np.random.random())
    cam.noise.put(20 * np.random.random())
    cam.peak_start.peak_start_x.put(200 + 500 * np.random.random())
    cam.peak_start.peak_start_y.put(200 + 500 * np.random.random())
    cam.peak_width.peak_width_x.put(10 + 100 * np.random.random())
    cam.peak_width.peak_width_y.put(10 + 100 * np.random.random())
    cam.peak_variation.put(0.5 + 20 * np.random.random())


def dither_ad_off():
    # select: 0 = off (Passive)
    ad_x_calc.scanning_rate.put(0)
    ad_y_calc.scanning_rate.put(0)


def dither_ad_on(select=6):
    # select: 6 = 1 Hz (1 second), 9 = 10 Hz (.1 second)
    ad_x_calc.scanning_rate.put(select)
    ad_y_calc.scanning_rate.put(select)


def dither_ad_peak_position(magnitude=40):
    """
    Dither the peak position using swait records.
    """
    peak = adsimdet.cam.peak_start
    formula = f"min(B,max(C,A+{magnitude}*(RNDM-0.5)))"

    x = ad_x_calc
    x.description.put("adsimdet peak X dither")
    x.calculation.put(formula)
    x.channels.A.input_pv.put(peak.peak_start_x.pvname)
    x.channels.B.input_value.put(900)  # upper limit
    x.channels.C.input_value.put(100)  # lower limit
    x.output_link_pv.put(peak.peak_start_x.setpoint_pvname)

    y = ad_y_calc
    y.description.put("adsimdet peak Y dither")
    y.calculation.put(formula)
    y.channels.A.input_pv.put(peak.peak_start_y.pvname)
    y.channels.B.input_value.put(900)  # upper limit
    y.channels.C.input_value.put(100)  # lower limit
    y.output_link_pv.put(peak.peak_start_y.setpoint_pvname)

    # add incident_beam PV to set cam.gain
    # hint: configure it to write its output to cam.gain field
    incident_beam_calc.output_link_pv.put(adsimdet.cam.gain._write_pv.pvname)

    dither_ad_on()


def _xml_attributes():
    """
    Define the content of the attributes XML file.

    Primarily, this is the list of PVs to bundle with
    every image frame.
    """
    xml = [
        '<?xml version="1.0" standalone="no" ?>',
        '<Attributes',
        '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
        '    xsi:schemaLocation="http://epics.aps.anl.gov/areaDetector/attributes ../attributes.xsd"',
        '    >',
    ]

    specifications = [
        # attr   source   datatype    description
        ["Manufacturer", "MANUFACTURER", "STRING", "Camera manufacturer"],
        ["Model", "MODEL", "STRING", "Camera model"],
        ["MaxSizeX", "MAX_SIZE_X", "INT", "Detector X size"],
        ["MaxSizeY", "MAX_SIZE_Y", "INT", "Detector Y size"],
        ["ImageCounter", "ARRAY_COUNTER", "INT", "Image counter"],
        ["DriverFileName", "FULL_FILE_NAME", "STRING", "Driver full file name"],
        ["FileName", "FILE_NAME", "STRING", "Driver file name"],
        ["AttributesFile", "ND_ATTRIBUTES_FILE", "STRING", "Attributes file name"],
        ["ADCoreVersion", "ADCORE_VERSION", "STRING", "ADCore version number"],
    ]
    for attr, source, datatype, description in specifications:
        xml.append(
            '  <Attribute'
            ' type="PARAM"'
            f' source="{source}"'
            f' name="{attr}"'
            f' description="{description}"'
            f' datatype="{datatype}"'
            ' />'
        )

    specifications = []
    if iconfig["APS_IN_BASELINE"]:
        specifications += [
            # attr      PV      description     dbrtype
            ["aps_current", "S:SRcurrentAI", "DBR_NATIVE"],
            ["aps_fill_number", "S:FillNumber", "DBR_NATIVE"],
            ["aps_orbit_correction", "S:OrbitCorrection:CC", "DBR_NATIVE"],
            ["aps_global_feedback", "SRFB:GBL:LoopStatusBI", "DBR_STRING"],
            # ["aps_global_feedback_h", "SRFB:GBL:HLoopStatusBI", "DBR_STRING"],
            # ["aps_global_feedback_v", "SRFB:GBL:VLoopStatusBI", "DBR_STRING"],
            # ["aps_operator_messages_operators", "OPS:message1", "DBR_STRING"],
            # ["aps_operator_messages_floor_coordinator", "OPS:message2", "DBR_STRING"],
            ["aps_operator_messages_fill_pattern", "OPS:message3", "DBR_STRING"],
            # ["aps_operator_messages_last_problem_message", "OPS:message4", "DBR_STRING"],
            # ["aps_operator_messages_last_trip_message", "OPS:message5", "DBR_STRING"],
            ["aps_operator_messages_message6", "OPS:message6", "DBR_STRING"],
            # ["aps_operator_messages_message7", "OPS:message7", "DBR_STRING"],
            # ["aps_operator_messages_message8", "OPS:message8", "DBR_STRING"],
        ]
    for axis in "x y".split():
        m = getattr(samplexy.coarse, axis)
        specifications.append([f"{m.name}", f"{getattr(m, 'user_readback').pvname}", "DBR_NATIVE"])
        specifications.append([f"{m.name}_setpoint", f"{getattr(m, 'user_setpoint').pvname}", "DBR_NATIVE"])
        m = getattr(samplexy.fine, axis)
        specifications.append([f"{m.name}", f"{m.pvname}", "DBR_NATIVE"])
    for attr, pv, dbrtype in specifications:
        xml.append(
            '  <Attribute'
            ' type="EPICS_PV"'
            f' source="{pv}"'
            f' name="{attr}"'
            f' description="{attr}"'
            f' dbrtype="{dbrtype}"'  #  dbrtype="DBR_NATIVE"
            ' />'
        )

    xml.append('</Attributes>')
    return '\n'.join(xml)


def setup_attributes_file():
    path = BLUESKY_MOUNT_PATH
    if path.exists():
        # afile = IMAGE_DIR / "attributes.xml"
        afile = "attributes.xml"
        with open(f"{path / afile}", "w") as f:
            f.write(_xml_attributes())
        if (path / afile).exists():
            adsimdet.cam.nd_attributes_file.put(
                f"{AD_IOC_MOUNT_PATH / afile}"
            )


adsimdet = MySimDetector(iconfig["ADSIM_IOC_PREFIX"], name="adsimdet")
adsimdet.wait_for_connection(timeout=iconfig["PV_CONNECTION_TIMEOUT"])

adsimdet.read_attrs.append("hdf1")
adsimdet.read_attrs.append("pva")

adsimdet.hdf1.create_directory.put(-5)

adsimdet.cam.stage_sigs["image_mode"] = "Single"
adsimdet.cam.stage_sigs["num_images"] = 1
adsimdet.cam.stage_sigs["acquire_time"] = 0.1
adsimdet.cam.stage_sigs["acquire_period"] = 0.105
adsimdet.cam.stage_sigs["wait_for_plugins"] = "Yes"
adsimdet.hdf1.stage_sigs["file_template"] = "%s%s_%3.3d.h5"

if iconfig.get("ENABLE_AREA_DETECTOR_IMAGE_PLUGIN", False):
    adsimdet.image.enable.put(1)

# WORKAROUND
# Even with `lazy_open=1`, ophyd checks if the area
# detector HDF5 plugin has been primed.  We might
# need to prime it.  Here's ophyd's test:
WARMUP_OK = iconfig.get("ALLOW_AREA_DETECTOR_WARMUP", False)
if WARMUP_OK and (np.array(adsimdet.hdf1.array_size.get()).sum() == 0):
    logger.info(f"Priming {adsimdet.hdf1.name} ...")
    adsimdet.hdf1.warmup()
    logger.info(f"Enabling {adsimdet.image.name} plugin ...")
    adsimdet.image.enable.put("Enable")

# peak new peak parameters
change_ad_simulated_image_parameters()
# have EPICS dither the peak position
dither_ad_peak_position()

setup_attributes_file()
