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

    time_for_next_frame = time.time()
    for item in image_file_list(num_images):
        yield from img2pva.wait_server(time_for_next_frame)
        yield from bps.mv(img2pva, item)
        yield from img2pva.wait_server()
        yield from bps.create()
        yield from bps.read(adpvadet.cam.array_counter)
        yield from bps.save()

        while time_for_next_frame <= time.time():  # until time is in the future
            time_for_next_frame += frame_interval
    yield from img2pva.wait_server()

    yield from bps.mv(adpvadet.cam.acquire, 0)
    adpvadet.unstage()

    yield from bps.close_run()
