"""
Plans for the BPD project demonstration
"""

__all__ = """
    close_shutter
    move_coarse_positioner
    move_fine_positioner
    open_shutter
    take_image
""".split()

from ..session_logs import logger

logger.info(__file__)

from ..devices import coarse_xy
from ..devices import fine_xy
from ..devices import adsimdet
from ..devices import incident_beam
from ..devices import shutter
from bluesky import plans as bp
from bluesky import plan_stubs as bps


DIGITS = 5  # for rounding precision

def open_shutter():
    """Open the (simulated) shutter."""
    if shutter.state != "open":
        yield from bps.mv(shutter, "open")
    else:
        # MUST yield something
        yield from bps.null()


def close_shutter():
    """Close the (simulated) shutter."""
    if shutter.state != "close":
        yield from bps.mv(shutter, "close")
    else:
        # MUST yield something
        yield from bps.null()


def move_coarse_positioner(x, y):
    """Move the coarse_xy positioner, only to new positions."""
    args = []
    xy_stage = coarse_xy
    if round(xy_stage.x.position, DIGITS) != round(x, DIGITS):
        args += [xy_stage.x, x]
    if round(xy_stage.y.position, DIGITS) != round(y, DIGITS):
        args += [xy_stage.y, y]
    if len(args) > 0:
        # only move if necessary
        yield from bps.mv(*args)
    else:
        # MUST yield something
        yield from bps.null()


def move_fine_positioner(x, y):
    """Move the fine_xy positioner, only to new positions."""
    args = []
    xy_stage = fine_xy
    if round(xy_stage.x.get(), DIGITS) != round(x, DIGITS):
        args += [xy_stage.x, x]
    if round(xy_stage.y.get(), DIGITS) != round(y, DIGITS):
        args += [xy_stage.y, y]
    if len(args) > 0:
        # only move if necessary
        yield from bps.mv(*args)
    else:
        # MUST yield something
        yield from bps.null()


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
        If ``None``, coarse_xy will not be moved.
    fine (x, y) or ``None``:
        Pair (tuple or list) of *new* x, y positions.
        If ``None``, fine_xy will not be moved.
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
        coarse_x = coarse_xy.x.position,
        coarse_y = coarse_xy.y.position,
        fine_x = fine_xy.x.get(),
        fine_y = fine_xy.y.get(),
    )
    _md.update(md or {})

    yield from open_shutter()
    yield from bp.count([adsimdet], md=_md)
    yield from close_shutter()
