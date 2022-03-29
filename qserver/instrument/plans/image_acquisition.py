"""
Bluesky measurement plans for the BPD 2022 project demonstration
"""

__all__ = ["take_image", "prime_hdf_plugin"]

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from .. import iconfig
from ..devices import adsimdet
from ..devices import image_file_created
from ..devices import incident_beam
from ..devices import samplexy
from ..devices import shutter
from .move_positioners import move_coarse_positioner
from .move_positioners import move_fine_positioner
from .shutter_controls import close_shutter
from .shutter_controls import open_shutter
from bluesky import plan_stubs as bps
from bluesky import plans as bp
import databroker
import datetime
import pathlib


APERIOD_EXTRA = 0.001
cat = databroker.catalog[iconfig["DATABROKER_CATALOG"]]


def update_cross_reference_file(run_uid, image_name):
    """
    Remember which bluesky run contains image file (base name).

    For example, given an image file named:
    ``/path/to/2022/03/29/a4700b27-2666-44cf-a86f_000.h5``,
    associate ``a4700b27-2666-44cf-a86f_000`` with the
    ``run_uid`` provided.

    Append the data to a YAML-formatted text file.
    """
    path = pathlib.Path(iconfig["IMAGE_RUN_XREF_FILE"])
    write_header = not path.exists()

    with open(str(path.absolute()), "a") as f:
        if write_header:
            logger.info(
                "Creating cross-reference file: %s",
                str(path.absolute())
            )
            f.write(
                f"# file: {path}\n"
                f"# created: {datetime.datetime.now()}\n"
                "# purpose: cross-reference bluesky run uid and HDF5 file name\n"
                "\n"
            )
        f.write(
            f"{run_uid}: {image_name.stem}\n"
            f"{image_name.stem}: {run_uid}\n"
        )


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
        aperiod = atime + APERIOD_EXTRA

    adsimdet.cam.stage_sigs["acquire_time"] = atime
    adsimdet.cam.stage_sigs["acquire_period"] = aperiod

    logger.info("area detector (%s) acquire time: %f", adsimdet.name, atime)
    logger.info("area detector (%s) acquire period: %f", adsimdet.name, aperiod)

    _md = dict(
        plan_name = "take_image",
        incident_beam = incident_beam.get(),
        incident_beam_units = "simulation",
        coarse_x = samplexy.coarse.x.position,
        coarse_y = samplexy.coarse.y.position,
        coarse_x_units = samplexy.coarse.x.egu,
        coarse_y_units = samplexy.coarse.y.egu,
        fine_x = samplexy.fine.x.get(),
        fine_y = samplexy.fine.y.get(),
        acquire_time = atime,
        acquire_period = aperiod,
        shutter = shutter.state,
    )
    _md.update(md or {})

    uid = yield from bp.count([adsimdet], md=_md)
    print(f"DIAGNOSTIC: {uid = }")

    try:
        # write the image file name to a PV
        run = cat[uid]
        print(f"DIAGNOSTIC: {run = }")
        r = run.primary._get_resources()[0]
        print(f"DIAGNOSTIC: {r = }")
        hdffile = pathlib.Path(r["root"]) / r["resource_path"]
        print(f"DIAGNOSTIC: {hdffile = },  {hdffile.exists()=}")
        logger.info("Image file '%s' (exists: %s)", hdffile, hdffile.exists())
        yield from bps.mv(image_file_created, str(hdffile))
        update_cross_reference_file(uid, hdffile)
    except Exception as exc:
        # avoid crashing the plan just for this information
        print(f"Exception involving name of image file: {exc}")
        logger.warning("Exception involving name of image file: %s", exc)

    return uid


def prime_hdf_plugin():
    """Prime HDF file plugin by pushing one frame to it."""
    adsimdet.hdf1.warmup()
    yield from bps.null()
