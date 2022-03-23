"""
Plans for the BPD 2022 project demonstration
"""

__all__ = """
    set_acquire_time
    take_image
""".split()

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


def set_acquire_time(atime, aperiod=None):
    """
    Set the acquire time & period of the area detector.

    Parameters:

    atime float:
        ``AcquireTime is`` the time to acquire the image (seconds).
    aperiod float or ``None``:
        ``AcquirePeriod is`` the time between image frames (seconds).
        Should be ``AcquireTime < AcquirePeriod`` in most cases.
        When ``aperiod`` is ``None``, then it will be set slightly
        longer than ``atime``.
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


def take_image(coarse=None, fine=None, md=None):
    """
    Take one image with the area detector.

    1. Move the stages as directed.  No move if ``None``.
    2. Gather metadata
    3. Open the shutter
    4. Take the image
    5. Close the shutter

    Parameters:

    coarse (x, y) or ``None``:
        Pair (tuple or list) of *new* x, y positions.
        If ``None``, samplexy.coarse will not be moved.
    fine (x, y) or ``None``:
        Pair (tuple or list) of *new* x, y positions.
        If ``None``, samplexy.fine will not be moved.
    md dict:
        Dictionary of any additional metadata to add to this image.

    View:

    To view acquired image (from databroker catalog) in IPython console::

        cat[-1].primary.read()["adsimdet_image"][0][0].plot.pcolormesh()
    """
    if coarse is not None:
        yield from move_coarse_positioner(coarse)
    if fine is not None:
        yield from move_fine_positioner(fine)

    _md = dict(
        plan_name = "take_image",
        incident_beam = incident_beam.get(),
        coarse_x = samplexy.coarse.x.position,
        coarse_y = samplexy.coarse.y.position,
        fine_x = samplexy.fine.x.get(),
        fine_y = samplexy.fine.y.get(),
    )
    _md.update(md or {})

    yield from open_shutter()
    uid = yield from bp.count([adsimdet], md=_md)
    yield from close_shutter()

    try:
        # write the image file name to a PV
        r = cat[uid].primary._get_resources()[0]
        hfile = pathlib.Path(r["root"]) / r["resource_path"]
        logger.info("Image file '%s' (exists: %s)", hfile, hfile.exists())
        yield from bps.mv(image_file_created, str(hfile))
    except Exception as exc:
        # avoid crashing the plan just for this information
        logger.warning("Exception involving name of image file: %s", exc)

    return uid
