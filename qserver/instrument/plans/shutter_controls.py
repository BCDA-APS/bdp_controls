"""
Control the shutter.
"""

__all__ = """
    close_shutter
    open_shutter
""".split()

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)


from ..devices import shutter
from bluesky import plan_stubs as bps


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
