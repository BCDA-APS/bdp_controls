"""
A flyer to stream a set of images by PVA
"""

__all__ = [
    "m9_flyer",
]

import logging

logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from .. import iconfig
from apstools.devices import ActionsFlyerBase
from apstools.utils import run_in_thread
from ophyd import Component
from ophyd import EpicsSignal
# from ophyd import Signal
import configparser
import numpy as np
import pandas
import pathlib
import pvaccess as pva
import time


DATA_PATH = pathlib.Path("/gdata/bdp") / "henke"
IMAGES_FILE = DATA_PATH / "fly001_uint16.npy"
POSITIONS_FILE = DATA_PATH / "fly001_pos.csv"
CONFIG_FILE = DATA_PATH / "ptychodus.ini"
PVA_TYPE_KEY_MAP = {
    np.dtype("uint8"): "ubyteValue",
    np.dtype("int8"): "byteValue",
    np.dtype("uint16"): "ushortValue",
    np.dtype("int16"): "shortValue",
    np.dtype("uint32"): "uintValue",
    np.dtype("int32"): "intValue",
    np.dtype("uint64"): "ulongValue",
    np.dtype("int64"): "longValue",
    np.dtype("float32"): "floatValue",
    np.dtype("float64"): "doubleValue",
}
DEMO_TITLE = f"{iconfig['BDP_DEMO']} demo"


def getTimestamp(t=None):
    s = t or time.time()
    ns = int((s - int(s)) * 1_000_000_000)
    s = int(s)
    return pva.PvTimeStamp(s, ns)


class PositionerCache:
    """Cache positioner values and timestamps before updating PVA."""

    schema = dict(
        uniqueId=pva.ULONG,
        nUpdates=pva.UINT,
        t=[pva.PvTimeStamp()],
        values=[pva.DOUBLE],
    )

    def __init__(self):
        self.reset()
        self.uniqueId = 0

    def __len__(self):
        return len(self.values)

    def add(self, value, timestamp):
        self.values.append(value)
        self.timestamps.append(timestamp)

    def reset(self):
        self.values = []
        self.timestamps = []

    @property
    def pv_object(self):
        self.uniqueId += 1
        dd = dict(
                uniqueId=self.uniqueId,
                nUpdates=len(self.values),
                t=self.timestamps,
                values=np.array(self.values),
            )
        # print(f"{dd=}")
        pv_object = pva.PvObject(self.schema, dd)

        self.reset()
        return pv_object


class BlueskyImageServer(pva.PvaServer):

    def __init__(self):
        extraFieldsTypeDict = {}
        print(f"{extraFieldsTypeDict=}")
        super().__init__()

        self.cache_x = PositionerCache()
        self.cache_y = PositionerCache()

        self.addRecord(iconfig["PV_PVA_M9_IMAGE"], pva.NtNdArray(extraFieldsTypeDict))
        self.addRecord(iconfig["PV_PVA_M9_X"], pva.PvObject(self.cache_x.schema), None)
        self.addRecord(iconfig["PV_PVA_M9_Y"], pva.PvObject(self.cache_y.schema), None)

    def build_pva_frame(self, frame, unique_id, total_frames, ts=None):
        """Build the PVA object for one frame."""
        # see blueskyImageServer.BlueskyImageServer.updateFrame() for example
        rows, cols = frame.shape
        size = rows * cols * frame.itemsize
        dims = [
            pva.PvDimension(cols, 0, cols, 1, False),
            pva.PvDimension(rows, 0, rows, 1, False),
        ]

        ts = ts or getTimestamp()
        pvaTypeKey = PVA_TYPE_KEY_MAP.get(frame.dtype)
        attributes = [
            pva.NtAttribute("ColorMode", pva.PvInt(0)),
            pva.NtAttribute("ImageGoal", pva.PvString(DEMO_TITLE)),
            # pva.NtAttribute("pos_x", pva.PvDouble(x)),
            # pva.NtAttribute("pos_y", pva.PvDouble(y)),
            pva.NtAttribute("TotalFrames", pva.PvInt(total_frames)),
        ]

        pva_frame = pva.NtNdArray({})
        pva_frame["uniqueId"] = unique_id
        pva_frame["dimension"] = dims
        pva_frame["compressedSize"] = size
        pva_frame["uncompressedSize"] = size
        pva_frame["timeStamp"] = ts
        pva_frame["dataTimeStamp"] = ts
        pva_frame["descriptor"] = "Bluesky Image"
        pva_frame["value"] = {pvaTypeKey: frame.flatten()}
        pva_frame["attribute"] = attributes

        return pva_frame

    def m9_demo(self, rate, n_frames, positions, frames, position_chunks=10):
        """Serve 'n' frames at 'rate' frames/second."""
        # only use the first n available position,frame sets
        n = max(0, min(n_frames, len(frames), len(positions)))
        logger.debug("Serving the first %s frames.", n)
        period = 1.0 / rate
        logger.debug("Period between frames: %s s", period)

        t0 = time.time()
        for i, obj in enumerate(zip(positions[:n], frames[:n])):
            deadline = t0 + i * period
            while time.time() < deadline:  # control the frame rate
                time.sleep(period/20)
            yx, frame = obj
            y, x = yx
            ts = getTimestamp()
            self.update(  # post the frame every time
                iconfig["PV_PVA_M9_IMAGE"], self.build_pva_frame(frame, i, n, ts=ts)
            )
            self.cache_x.add(x, ts)
            self.cache_y.add(y, ts)

            # post the positions in chunks
            if len(self.cache_x) >= position_chunks:
                self.update(iconfig["PV_PVA_M9_X"], self.cache_x.pv_object)
            if len(self.cache_y) >= position_chunks:
                self.update(iconfig["PV_PVA_M9_Y"], self.cache_y.pv_object)

        # post any remaining positions in the caches
        if len(self.cache_x) > 0:
            self.update(iconfig["PV_PVA_M9_X"], self.cache_x.pv_object)
        if len(self.cache_y) > 0:
            self.update(iconfig["PV_PVA_M9_Y"], self.cache_y.pv_object)


class M9_Flyer(ActionsFlyerBase):
    reconstruct = Component(
        EpicsSignal, iconfig["PV_CA_M9_RECONSTRUCT"], kind="omitted"
    )
    frame_rate = Component(EpicsSignal, iconfig["PV_CA_M9_FRAME_RATE"], kind="config")
    num_images = Component(EpicsSignal, iconfig["PV_CA_M9_NUM_IMAGES"], kind="config")
    position_chunk_size = Component(EpicsSignal, iconfig["PV_CA_M9_N_POS_CHUNKS"], kind="config")

    frame_server = BlueskyImageServer()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.frame_server.start()
        self.load_configuration()
        self.load_image_data()
        self.load_positions_data()

    def load_configuration(self):
        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_FILE)
        logger.info(
            "Configuration: file='%s', len=%s", CONFIG_FILE.name, len(self.config)
        )

    def load_image_data(self):
        self.frames = np.load(IMAGES_FILE, mmap_mode="r")
        logger.info("Images: file='%s', shape=%s", IMAGES_FILE.name, self.frames.shape)

    def load_positions_data(self):
        self.positions = pandas.read_csv(POSITIONS_FILE).to_numpy()
        # note: y, x
        logger.info(
            "Positions: file='%s', shape=%s", POSITIONS_FILE.name, self.positions.shape
        )

    def actions_thread(self):
        """
        Run the flyer in a thread.  Not a bluesky plan.

        Any acquired data should be saved internally and yielded from
        :meth:`~collect`.  (Remember to modify :meth:`~describe_collect` for
        any changes in the structure of data yielded by :meth:`~collect`!)
        """

        @run_in_thread
        def _action():
            logging.debug("in actions_thread()")

            self.reconstruct.put(0)  # disable reconstruction

            # This is where we call the external code
            self.frame_server.m9_demo(
                self.frame_rate.get(),
                self.num_images.get(),
                self.positions,
                self.frames,
                position_chunks=self.position_chunk_size.get()
            )

            self.reconstruct.put(1)  # enable (trigger) reconstruction

            self.status_actions_thread.set_finished()
            logging.debug("actions_thread() marked 'finished'")

        _action()


m9_flyer = M9_Flyer("", name="m9_flyer")
