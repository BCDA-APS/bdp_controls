"""
EpicsSignal: receives file name, sends image via PVAccess
"""

__all__ = """
    img2pva
    image_file_list
""".split()

print(__file__)

from .. import iconfig
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
PV_CA_IMAGE_FILE_NAME = iconfig["PV_CA_IMAGE_FILE_NAME"]
PV_PVA_IMAGE = iconfig["PV_PVA_IMAGE"]
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


img2pva = ImageFileToPvaSignal(
    PV_CA_IMAGE_FILE_NAME, 
    name="image_file_name", 
    string=True,
    pva_name=PV_PVA_IMAGE,
)
