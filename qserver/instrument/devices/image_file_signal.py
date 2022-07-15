"""
EpicsSignal: receives file name, sends image via PVAccess
"""

from .blueskyImageServer import BlueskyImageServer
from apstools.utils import run_in_thread
from ophyd import EpicsSignal
import datetime
import logging
import pathlib
import random
import time


logger = logging.getLogger(__name__)
M6_GALLERY = pathlib.Path.home() / "voyager" / "BDP" / "M6-gallery"
PV_CA_IMAGE_FILE_NAME = "bdpapi:ImageFileName"
PV_PVA_IMAGE = "bluesky:image"
WAIT_BUSY_LOOP = 1.0 / 5_000  # at most, 5k frames per second


def image_file_list(num=4, sort=True):
    """Return randomized list of 'num' image file names, sort is optional."""
    # fmt: off
    all_files = [
        str(item)
        for item in M6_GALLERY.iterdir()
        if str(item).endswith(".tif")
    ]
    if sort:
        all_files = sorted(all_files)

    subset = [
        all_files[random.randint(0, len(all_files)-1)]
        for i in range(min(num, len(all_files)-1))
    ]
    if sort:
        subset = sorted(subset)
    return subset
    # fmt: on


class ImageFileToPvaSignal(EpicsSignal):
    """
    EpicsSignal: receives file name, sends image via PVAccess
    """

    pva_name = PV_PVA_IMAGE
    pva_server = None

    def __init__(self, *args, pva_name=None, **kwargs):
        self._busy = True
        super().__init__(*args, **kwargs)
        if pva_name is not None:
            self.pva_name = pva_name
        self.start_pva_server()
        self.subscribe(self.cb_ca_monitor_event)
        self._busy = False

    def cb_ca_monitor_event(self, *args, **kwargs):
        """Called from EPICS CA monitor update."""
        if kwargs["old_value"] == kwargs["value"]:
            logger.debug("Ignore update with same value.")
            return
        if not isinstance(kwargs["old_value"], str):
            logger.debug("Ignore non-str update.")
            return
        logger.debug(f"cb_readback({args}, {kwargs})")
        logger.debug(f"self._busy: {self._busy}")

        self.publish_image_as_pva(kwargs["value"])

    @run_in_thread
    def publish_image_as_pva(self, fname=None):
        """Take image file name, read the image, publish as PVAccess."""
        if self.pva_server is None:
            raise RuntimeError("PVA server is not running.")
        if not self.connected:
            logger.debug("Not connected.  Will not post image to PVA.")
            return

        self.wait_server()

        self._busy = True
        fname = pathlib.Path(fname or self.get())
        if not fname.exists():
            logger.debug(f"{fname} not found.")
            return

        logger.debug(f"pushing {fname} image to PVA {self.pva_name}")
        self.pva_server.updateImage(f"{str(fname)}")
        self._busy = False

    def start_pva_server(self):
        if self.pva_server is not None:
            raise RuntimeError("PVA server already running.")

        logger.debug("starting PVA server ...")
        self.pva_server = BlueskyImageServer(self.pva_name)
        self.pva_server.start()

    def stop_pva_server(self):
        if self.pva_server is not None:
            logger.debug("stopping PVA server ...")
            self.pva_server.stop()
            self.pva_server = None

    @property
    def busy(self):
        return self._busy

    def wait_server(self, earliest=0):
        yield from bps.null()
        while (time.time() < earliest) or self.busy:
            # print(f"waiting: {datetime.datetime.now()} {time.time()<earliest} {self.busy}")
            yield from bps.sleep(SHORT_WAIT)

    # def wait_when_busy(self):
    #     """Loop until this signal is not busy."""
    #     if self.busy:
    #         t0 = time.time()
    #         while self.busy:
    #             time.sleep(WAIT_BUSY_LOOP)
    #         logger.debug(f"waited {1000 * (time.time() - t0):.3f} ms")


def demo2():
    img2pva = ImageFileToPvaSignal(
        PV_CA_IMAGE_FILE_NAME, name="image_file_name", string=True
    )
    img2pva.wait_for_connection()

    logger.debug(f"image files: {IMAGE_FILES}")

    for fname in IMAGE_FILES:
        img2pva.wait_server()
        print(f"image file name={fname}")
        t0 = time.time()
        img2pva.put(fname)
        logger.debug("dt=%.3f ms", 1000 * (time.time() - t0))


def demo1():
    img2pva = ImageFileToPvaSignal(
        PV_CA_IMAGE_FILE_NAME, name="image_file_name", string=True
    )
    img2pva.wait_for_connection()
    img2pva.start_pva_server()

    time.sleep(10)  # allow clients time to (re)connect
    print("PVA server started now. Look for {PV_PVA_IMAGE}")

    t0 = time.time()
    for fname in IMAGE_FILES:
        img2pva.put(fname)
        print(f"image file name={img2pva.get()}")
        img2pva.publish_image_as_pva()

    dt = time.time() - t0
    mean = dt / len(IMAGE_FILES)
    print(f"average time per image: {mean*1_000:.4f}ms")

    # leave server running for a bit longer
    time.sleep(10)

    img2pva.stop_pva_server()
    print("demo over")


if __name__ == "__main__":
    # demo1()
    demo2()
