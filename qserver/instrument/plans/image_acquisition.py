"""
Plans for the BPD 2022 project demonstration
"""

__all__ = ["take_image", ]

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from ..devices import adsimdet
from ..devices import image_file_created
from ..devices import incident_beam
from ..devices import samplexy
from ..iconfig_dict import iconfig
from .move_positioners import move_coarse_positioner
from .move_positioners import move_fine_positioner
from .shutter_controls import close_shutter
from .shutter_controls import open_shutter
from bluesky import plan_stubs as bps
from bluesky import plans as bp
import databroker
import pathlib


PTIME_EXTRA = 0.001
cat = databroker.catalog[iconfig["DATABROKER_CATALOG"]]


def take_image(atime, aperiod=None, md=None):
    """
    Take one image with the area detector.

    Hint:  If the shutter is not opened, the image will be background only.

    Parameters:

    atime float:
        ``AcquireTime is`` the time to acquire the image (seconds).
    aperiod float or ``None``:
        ``AcquirePeriod is`` the time between image frames (seconds).
        Should be ``AcquireTime < AcquirePeriod`` in most cases.
        When ``aperiod`` is ``None``, then it will be set slightly
        longer than ``atime``.
    md dict:
        Dictionary of any additional metadata to add to this image.

    View:

    To view acquired image (from databroker catalog) in IPython console::

        cat[-1].primary.read()["adsimdet_image"][0][0].plot.pcolormesh()
    """
    if atime <= 0:
        raise ValueError(
            f"Improper AcquireTime value, must be >0, received {atime}"
        )
    if aperiod is None or aperiod <= atime:
        aperiod = atime + PTIME_EXTRA

    adsimdet.cam.stage_sigs["acquire_time"] = atime
    adsimdet.cam.stage_sigs["acquire_period"] = aperiod

    logger.info("area detector (%s) acquire time: %f", adsimdet.name, atime)
    logger.info("area detector (%s) acquire period: %f", adsimdet.name, aperiod)

    _md = dict(
        plan_name = "take_image",
        incident_beam = incident_beam.get(),
        coarse_x = samplexy.coarse.x.position,
        coarse_y = samplexy.coarse.y.position,
        fine_x = samplexy.fine.x.get(),
        fine_y = samplexy.fine.y.get(),
        acquire_time = adsimdet.cam.acquire_time.get(),
        acquire_period = adsimdet.cam.acquire_period.get(),
    )
    _md.update(md or {})

    uid = yield from bp.count([adsimdet], md=_md)

    try:
        # write the image file name to a PV
        r = cat[uid].primary._get_resources()[0]
        hfile = pathlib.Path(r["root"]) / r["resource_path"]
        logger.info("Image file '%s' (exists: %s)", hfile, hfile.exists())
        yield from bps.mv(image_file_created, str(hfile))
    except Exception as exc:
        # avoid crashing the plan just for this information
        print(f"Exception involving name of image file: {exc}")
        logger.warning("Exception involving name of image file: %s", exc)

    return uid
