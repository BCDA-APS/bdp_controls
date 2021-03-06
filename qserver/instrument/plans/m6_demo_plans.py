"""
Make a simulation for remote feedback to adjust.
"""

__all__ = ["push_images", ]

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from .. import iconfig
from ..devices import adpvadet
from ..devices import gallery
from ..devices import image_file_list
from ..devices import img2pva
# from apstools.devices import AD_plugin_primed
# from apstools.devices import AD_prime_plugin2
from bluesky import plan_stubs as bps
from bluesky import preprocessors as bpp
import datetime
import time
import tqdm


def set_next_deadline(deadline, interval):
    while deadline <= time.time():  # until time is in the future
        deadline += interval
    return deadline


def push_images(num_images=4, frame_rate=10, run_time=300, md={}):
    _md = dict(
        purpose="push TIFF files to PVaccess PV",
        num_images=num_images,
        frame_rate=frame_rate,
        run_time=run_time,
        datetime=str(datetime.datetime.now()),
    )
    _md.update(md)

    # Problems priming, cannot force a new cam image.  Set Capture directly.
    # if not AD_plugin_primed(adpvadet.tiff1):
    #     print("Priming 'adpvadet.tiff1' plugin.")
    #     AD_prime_plugin2(adpvadet.tiff1)
    if "capture" in adpvadet.tiff1.stage_sigs:
        adpvadet.tiff1.stage_sigs.pop("capture")
    print(f"adpvadet.tiff1.stage_sigs={adpvadet.tiff1.stage_sigs}")

    adpvadet.cam.stage_sigs["num_images"] = 1_000_000  # num_images
    adpvadet.tiff1.stage_sigs["num_capture"] = 1_000_000  # num_images
    frame_interval = 1.0 / frame_rate

    # setup custom file names in TIFF plugin
    yield from bps.mv(
        adpvadet.tiff1.file_name, iconfig["BDP_DATA_FILE_NAME"],
        adpvadet.tiff1.file_path, iconfig["BDP_DATA_DIR"],
        adpvadet.tiff1.file_template, iconfig["BDP_DATA_FILE_TEMPLATE"],
    )

    @bpp.stage_decorator([adpvadet])
    @bpp.run_decorator(md=_md)
    def inner_plan():
        yield from bps.mv(adpvadet.tiff1.capture, 1)
        yield from bps.mv(adpvadet.cam.acquire, 1)

        t0 = time.time()
        frame_deadline = t0
        run_deadline = t0 + max(0, run_time)

        def detector_stopped():
            result = adpvadet.cam.acquire.get() not in (1, "Acquire")
            if result:
                logger.info(
                    "Stopping 'acquisition' early:"
                    f" {adpvadet.cam.acquire.pvname} stopped."
                )
            return result

        def has_runtime_expired():
            result = time.time() >= run_deadline
            if result:
                logger.info("Run time time complete.")
            return result

        def publish_single_frame(frame):
            yield from bps.null()
            # next call is not a bluesky plan
            img2pva.publish_frame_as_pva(frame)  # runs in thread

        progress_bar = tqdm.tqdm(desc=f"run time: {run_time} seconds.")
        while True:
            "Repeat until run time expires."
            if has_runtime_expired() or detector_stopped():
                break
            for frame in gallery.image_file_list(num_images):
                progress_bar.update()
                if has_runtime_expired() or detector_stopped():
                    break
                yield from img2pva.wait_server(frame_deadline)
                # yield from bps.mv(img2pva, item)
                yield from publish_single_frame(frame)
                yield from img2pva.wait_server()
                yield from bps.create()
                yield from bps.read(adpvadet.cam.array_counter)
                yield from bps.read(adpvadet.cam.array_rate)
                yield from bps.read(adpvadet.pva1.execution_time)
                yield from bps.read(adpvadet.tiff1.execution_time)
                yield from bps.save()

                frame_deadline = set_next_deadline(frame_deadline, frame_interval)
        yield from img2pva.wait_server()
        progress_bar.close()

        yield from bps.mv(adpvadet.tiff1.capture, 0)
        yield from bps.mv(adpvadet.cam.acquire, 0)

    return (yield from inner_plan())
