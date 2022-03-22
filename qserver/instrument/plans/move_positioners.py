"""
Plans to move the positioners
"""

__all__ = """
    move_coarse_positioner
    move_fine_positioner
""".split()

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from ..devices import samplexy
from bluesky import plan_stubs as bps


DIGITS = 5  # for rounding precision


def move_coarse_positioner(x, y):
    """Move the coarse stage, only to new positions."""
    args = []
    xy_stage = samplexy.coarse
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
    """Move the fine stage, only to new positions."""
    args = []
    xy_stage = samplexy.fine
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
