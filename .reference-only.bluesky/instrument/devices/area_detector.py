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

from ..session_logs import logger

logger.info(__file__)

from ..utils import configuration_dict
from .calculation_records import _incident_beam_calc
from .calculation_records import _ad_x_calc, _ad_y_calc
from ophyd import ADComponent
from ophyd import DetectorBase
from ophyd import EpicsSignalWithRBV
from ophyd import SimDetectorCam
from ophyd import SingleTrigger
from ophyd.areadetector.filestore_mixins import FileStoreHDF5IterativeWrite
from ophyd.areadetector.plugins import HDF5Plugin_V34
from ophyd.areadetector.plugins import ImagePlugin_V34
import numpy as np
import pathlib


IOC = configuration_dict.get("ADSIM_IOC_PREFIX", "ad:")

IMAGE_DIR = "adsimdet/%Y/%m/%d"
AD_IOC_MOUNT_PATH = pathlib.Path("/tmp")
BLUESKY_MOUNT_PATH = pathlib.Path("/tmp/docker_ioc/iocad/tmp")

# MUST end with a `/`
WRITE_PATH_TEMPLATE = f"{AD_IOC_MOUNT_PATH / IMAGE_DIR}/"
READ_PATH_TEMPLATE = f"{BLUESKY_MOUNT_PATH / IMAGE_DIR}/"


class MyFixedCam(SimDetectorCam):
    pool_max_buffers = None
    offset = ADComponent(EpicsSignalWithRBV, "Offset")


class MyHDF5Plugin(FileStoreHDF5IterativeWrite, HDF5Plugin_V34):
    """
    Add data acquisition methods to HDF5Plugin.

    * ``stage()`` - prepare device PVs befor data acquisition
    * ``unstage()`` - restore device PVs after data acquisition
    * ``generate_datum()`` - coordinate image storage metadata
    """


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
    # TODO: enable PVA plugin


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
    _ad_x_calc.scanning_rate.put(0)
    _ad_y_calc.scanning_rate.put(0)


def dither_ad_on(select=6):
    # select: 6 = 1 Hz (1 second), 9 = 10 Hz (.1 second)
    _ad_x_calc.scanning_rate.put(select)
    _ad_y_calc.scanning_rate.put(select)


def dither_ad_peak_position(magnitude=40):
    """
    Dither the peak position using swait records.
    """
    peak = adsimdet.cam.peak_start
    formula = f"min(B,max(C,A+{magnitude}*(RNDM-0.5)))"

    x = _ad_x_calc
    x.description.put("adsimdet peak X dither")
    x.calculation.put(formula)
    x.channels.A.input_pv.put(peak.peak_start_x.pvname)
    x.channels.B.input_value.put(900)  # upper limit
    x.channels.C.input_value.put(100)  # lower limit
    x.output_link_pv.put(peak.peak_start_x.setpoint_pvname)

    y = _ad_y_calc
    y.description.put("adsimdet peak Y dither")
    y.calculation.put(formula)
    y.channels.A.input_pv.put(peak.peak_start_y.pvname)
    y.channels.B.input_value.put(900)  # upper limit
    y.channels.C.input_value.put(100)  # lower limit
    y.output_link_pv.put(peak.peak_start_y.setpoint_pvname)

    # add incident_beam PV to set cam.gain
    # hint: configure it to write its output to cam.gain field
    _incident_beam_calc.output_link_pv.put(adsimdet.cam.gain._write_pv.pvname)

    dither_ad_on()


adsimdet = MySimDetector(IOC, name="adsimdet", labels=("area_detector",))
adsimdet.wait_for_connection(timeout=15)

adsimdet.read_attrs.append("hdf1")

adsimdet.hdf1.create_directory.put(-5)

adsimdet.cam.stage_sigs["image_mode"] = "Single"
adsimdet.cam.stage_sigs["num_images"] = 1
adsimdet.cam.stage_sigs["acquire_time"] = 0.1
adsimdet.cam.stage_sigs["acquire_period"] = 0.105
adsimdet.hdf1.stage_sigs["lazy_open"] = 1
adsimdet.hdf1.stage_sigs["compression"] = "None"
adsimdet.hdf1.stage_sigs["file_template"] = "%s%s_%3.3d.h5"

if configuration_dict.get("ENABLE_AREA_DETECTOR_IMAGE_PLUGIN", False):
    adsimdet.image.enable.put(1)

# WORKAROUND
# Even with `lazy_open=1`, ophyd checks if the area
# detector HDF5 plugin has been primed.  We might
# need to prime it.  Here's ophyd's test:
WARMUP_OK = configuration_dict.get("ALLOW_AREA_DETECTOR_WARMUP", "ad:")
if WARMUP_OK and (np.array(adsimdet.hdf1.array_size.get()).sum() == 0):
    logger.info(f"Priming {adsimdet.hdf1.name} ...")
    adsimdet.hdf1.warmup()
    logger.info(f"Enabling {adsimdet.image.name} plugin ...")
    adsimdet.image.enable.put("Enable")

# peak new peak parameters
change_ad_simulated_image_parameters()
# have EPICS dither the peak position
dither_ad_peak_position()
