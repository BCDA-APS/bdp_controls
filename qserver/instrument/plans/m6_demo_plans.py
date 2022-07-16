"""
Make a simulation for remote feedback to adjust.
"""

__all__ = ["push_images", ]

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from ..devices import adpvadet
from ..devices import img2pva
from ..devices import image_file_list
from bluesky import plan_stubs as bps
import datetime
import time


def set_next_deadline(deadline, interval):
    while deadline <= time.time():  # until time is in the future
        deadline += interval
    return deadline


def push_images(num_images=4, frame_rate=10, md={}):

    _md = dict(
        purpose="push TIFF files to PVaccess PV",
        num_images=num_images,
        frame_rate=frame_rate,
        datetime=str(datetime.datetime.now()),
    )
    _md.update(md)

    adpvadet.cam.stage_sigs["num_images"] = num_images
    frame_interval = 1.0 / frame_rate

    yield from bps.open_run(md=_md)

    adpvadet.stage()
    yield from bps.mv(adpvadet.cam.acquire, 1)

    frame_deadline = time.time()
    for item in image_file_list(num_images):
        yield from img2pva.wait_server(frame_deadline)
        yield from bps.mv(img2pva, item)
        yield from img2pva.wait_server()
        yield from bps.create()
        yield from bps.read(adpvadet.cam.array_counter)
        yield from bps.save()

        frame_deadline = set_next_deadline(frame_deadline, frame_interval)
    yield from img2pva.wait_server()

    yield from bps.mv(adpvadet.cam.acquire, 0)
    adpvadet.unstage()

    yield from bps.close_run()
