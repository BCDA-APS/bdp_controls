"""
Plans to move the positioners
"""

__all__ = """
    move_coarse_positioner
    move_fine_positioner
    set_fine_positioner_velocities
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
    yield from _move_named_positioner(samplexy.coarse, x, y)


def move_fine_positioner(x, y):
    """Move the fine stage, only to new positions."""
    yield from _move_named_positioner(samplexy.fine, x, y)


def _move_named_positioner(xy_stage, x, y):
    """Move the fine stage, only to new positions."""
    args = []
    if round(xy_stage.x.position, DIGITS) != round(x, DIGITS):
        args += [xy_stage.x, x]
    if round(xy_stage.y.position, DIGITS) != round(y, DIGITS):
        args += [xy_stage.y, y]
    if len(args) > 0:
        # only move if necessary
        yield from bps.mv(*args)

    # MUST yield something
    yield from bps.null()


def set_fine_positioner_velocities(vx, vy):
    """Set velocities on the fine stage positioners."""
    if hasattr(samplexy.fine.x, "velocity") and hasattr(samplexy.fine.y, "velocity"):
        yield from bps.mv(
            samplexy.fine.x.velocity, vx,
            samplexy.fine.y.velocity, vy,
        )
    # else quietly ignore
