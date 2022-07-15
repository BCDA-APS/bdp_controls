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
from ..qserver_framework import RE
from .metadata_support import create_layout_file
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


def take_image(atime, aperiod=None, nframes=1, compression="None", md=None):
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
    nframes int:
        Number of image frames per acquisition.
        default: 1
    compression str:
        Name of compression algorithm for HDF5 files.
        default: "None"
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

    if compression not in adsimdet.hdf1.compression.enum_strs:
        raise ValueError(
            f"Compression value '{compression}' not recognized."
            "  Must be one of these: "
            f"{', '.join(adsimdet.hdf1.compression.enum_strs)}"
        )

    nframes = max(1, nframes)

    adsimdet.cam.stage_sigs["acquire_time"] = atime
    adsimdet.cam.stage_sigs["acquire_period"] = aperiod
    adsimdet.cam.stage_sigs["image_mode"] = "Multiple" if nframes > 1 else "Single"
    adsimdet.cam.stage_sigs["num_images"] = nframes
    adsimdet.hdf1.stage_sigs["num_capture"] = nframes

    logger.info("area detector (%s) acquire time: %f", adsimdet.name, atime)
    logger.info("area detector (%s) acquire period: %f", adsimdet.name, aperiod)
    logger.info("area detector (%s) frames/image: %d", adsimdet.name, nframes)
    logger.info("area detector (%s) HDF5 compression: %s", adsimdet.name, compression)

    _md = dict(
        plan_name = "take_image",
        incident_beam = incident_beam.get(),
        incident_beam_units = "simulation",
        coarse_x = samplexy.coarse.x.position,
        coarse_y = samplexy.coarse.y.position,
        coarse_x_units = samplexy.coarse.x.egu,
        coarse_y_units = samplexy.coarse.y.egu,
        fine_x = samplexy.fine.x.position,
        fine_y = samplexy.fine.y.position,
        acquire_time = atime,
        acquire_period = aperiod,
        frames_per_image = nframes,
        HDF5_compression = compression,
        shutter = shutter.state,
    )
    _md.update(md or {})

    yield from bps.mv(
        # FIXME: provokes a write timeout on file_template
        # adsimdet.hdf1.lazy_open, 1,

        adsimdet.hdf1.create_directory, -5,
        adsimdet.hdf1.file_write_mode, "Stream",
        adsimdet.hdf1.compression, compression,
    )

    # FIXME: first get() returns only the "%"  -- Why?
    """
    TimeoutError: Attempted to set EpicsSignalWithRBV(read_pv='bdpad:HDF1:FileTemplate_RBV', name='adsimdet_hdf1_file_template', parent='adsimdet_hdf1', value='%', timestamp=1649372489.9390404, auto_monitor=True, string=True, write_pv='bdpad:HDF1:FileTemplate', limits=False, put_complete=False) to value '%s%s_%3.3d.h5' and timed out after 10 seconds. Current value is '%'.

    In [4]: adsimdet.hdf1.file_template.get()
    Out[4]: '%'

    In [5]: adsimdet.hdf1.file_template.get?

    In [6]: adsimdet.hdf1.file_template.get(use_monitor=False)
    Out[6]: '%s%s_%3.3d.h5'
    """
    # Force ophyd to request a new value from the IOC
    adsimdet.hdf1.file_template.get(use_monitor=False)

    # write RunEngine and run metadata to HDF5 file
    # via the HDF5 layout file.
    try:
        layout_file = "layout.xml"
        re_md = RE.md.copy()
        re_md.update(_md)
        AD_IOC_MOUNT_PATH = pathlib.Path(iconfig["ADIOC_IMAGE_ROOT"])
        BLUESKY_MOUNT_PATH = pathlib.Path(iconfig["BLUESKY_IMAGE_ROOT"])
        create_layout_file(f"{BLUESKY_MOUNT_PATH / layout_file}", re_md)
        yield from bps.mv(
            adsimdet.hdf1.xml_file_name, f"{AD_IOC_MOUNT_PATH / layout_file}"
        )
    except Exception as exc:
        logger.warning(
            f"Problem creating {layout_file}: {exc}"
        )

    uid = yield from bp.count([adsimdet], md=_md)
    # print(f"DIAGNOSTIC: {uid = }")

    try:
        # write the image file name to a PV
        run = cat[uid]
        # print(f"DIAGNOSTIC: {run = }")
        r = run.primary._get_resources()[0]
        # print(f"DIAGNOSTIC: {r = }")
        path = pathlib.Path(r["root"]) / r["resource_path"]
        fname = pathlib.Path(adsimdet.hdf1.full_file_name.get())
        hdffile = path.parent / fname.name
        print(f"DIAGNOSTIC: {hdffile},  exists={hdffile.exists()}")
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
