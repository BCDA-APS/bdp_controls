"""
Stream a set of images by PVA using a flyer.
"""

__all__ = [
    "m9_push_images",
]

import logging

logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from .. import iconfig
from ..devices import m9_flyer
from bluesky import plans as bp
from bluesky import plan_stubs as bps
import datetime


def m9_push_images(num_images=12_000, frame_rate=1_000, md={}):
    _md = dict(
        purpose="publish image frames via PVaccess",
        num_images=num_images,
        frame_rate=frame_rate,
        datetime=str(datetime.datetime.now()),
    )
    _md.update(md)

    yield from bps.mv(
        m9_flyer.frame_rate, frame_rate,
        m9_flyer.num_images, num_images,
    )
    yield from bp.fly([m9_flyer], md=_md)
