"""
Bluesky measurement plans for the BPD 2022 project demonstration: trajectory scans

setup AD for multiple frames/acquisition
create plan: start AD, start XY get streaming (PVA) images

Prepare control system for workflow 4.

* Area detector images published by PVA
  * Do not write HDF file(s)
* Fine motors (ao records) are replaced by SoftPositioners that update readbacks at constant velocity.
* Measurement plan streams images while moving fine positioners.
* Analysis must examine image and metadata (for fine position), then recommend next action.

Future:
Move X & Y on non-linear path:
- grid trajectory
- lissajous trajectory

**Example**::

    RE(
        trajectory_plan(
            -500, 500,
            -500, 500,
            20.0,
            update_period=0.05,
            t_exposure=0.001,
            md=dict(purpose="development", proposal_id="bdp2022")
        )
    )
    run = cat[-1]

    # Is there one PVA image for each cam image?
    from matplotlib.pyplot import plot
    cam_image_number=run.adsimdet_cam_array_counter_monitor.read()["adsimdet_cam_array_counter"].data
    pva_image_number=run.adsimdet_pva_array_counter_monitor.read()["adsimdet_pva_array_counter"].data
    p1, = plot(cam_image_number-cam_image_number[0], pva_image_number-pva_image_number[0], linestyle="", marker=".")
    p1.axes.set_xlabel("cam image counter, relative")
    p1.axes.set_ylabel("pva image counter, relative")
    p1.axes.set_title("Any flat spots?  Gaps? Dropped images?")

    # How do X&Y vary with image number?
    x=run.fastxy_x_monitor.read()["fastxy_x"]
    y=run.fastxy_y_monitor.read()["fastxy_y"]
    pva=run.adsimdet_pva_array_counter_monitor.read()["adsimdet_pva_array_counter"]
    t0 = min(x.time[0], y.time[0], pva.time[0])
    p1, = plot(pva.time-t0, pva.data-pva.data[0], linestyle="", color="black", marker=".")
    p1.axes.set_title("co-linear?")
    twin1 = p1.axes.twinx()
    twin1.plot(x.time-t0, x.data, linestyle="", color="green", marker=".")
    twin1.plot(y.time-t0, y.data, linestyle="", color="red", marker=".")
    p1.axes.set_xlabel("elapsed time, s")
    p1.axes.set_ylabel("image counter, relative")
    twin1.axes.set_ylabel("X (g) & Y (r) position")

    run.metadata
"""

__all__ = []

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from .. import iconfig
from ..devices import adsimdet
from ..devices import image_file_created
from ..devices import incident_beam
from ..devices import samplexy
from ..devices import shutter
from ..devices.simulated_pzt_stage import MAXIMUM_VELOCITY
from ..qserver_framework import RE
from bluesky import plan_stubs as bps
from bluesky import preprocessors as bpp
import math
import numpy as np


def sublists(liszt, n):
    """Yield successive n-sized sublists from liszt."""
    for i in range(0, len(liszt), n):
        yield liszt[i : i + n]


def is_odd(n):
    return n % 2 == 1


def create_random_grid(
    x0, x1, y0, y1, n=25, snake=True, corners=True, sort_x_1st=True
):
    """
    Create a sorted list of random X,Y positions within a region of interest.

    Sort the list:

    - sort on first positioner (default: X)
    - if n>8, sort by sections (of size sqrt(n))
      - sort each section on second positioner (default: Y) according to snake term
    """

    def sort_by_x(xy):
        return xy[0]

    def sort_by_y(xy):
        return xy[1]

    sorters = (sort_by_x, sort_by_y) if sort_x_1st else (sort_by_y, sort_by_x)

    coords = []
    nr = n
    if corners and n >= 4:  # include the corners
        coords += [
            (x0, y0),
            (x0, y1),
            (x1, y1),
            (x1, y0),
        ]
        nr -= 4
    coords += list(
        zip(
            x0 + (x1 - x0) * np.random.rand(nr),
            y0 + (y1 - y0) * np.random.rand(nr)
        )
    )
    coords = sorted(coords, key=sorters[0])

    if n > 8:
        # sort by sections
        num_in_section = int(math.sqrt(n))
        arr = []
        for row, chunk in enumerate(sublists(coords, num_in_section)):
            arr += sorted(chunk, key=sorters[1], reverse=(snake and is_odd(row)))
        coords = arr

    return list(coords)


# TODO: refactor to use create_random_grid() for set of waypoints at fixed velocities
def trajectory_plan(
    x0, x1, y0, y1,
    duration=1, update_period=0.01, t_exposure=0.001,
    md=None
):
    """
    Collect images continuously while moving x&y on a linear path.

    Parameters

    x0 float:
        Starting X position.
    x1 float:
        Ending X position.
    y0 float:
        Starting Y position.
    y1 float:
        Ending Y position.
    duration float:
        Time for complete trajectory.
    update_period float:
        Update period (s) for the readback values of the xy stage.
    t_exposure float:
        Area detector image exposure time (s).

    """
    det = adsimdet  # local name
    xy = samplexy.fine

    # If not constrained, then plan will raise LimitError if out of limits.
    vx = abs(x1 - x0) / duration
    vy = abs(y1 - y0) / duration
    # print(f"(DEBUG) {vx=}  {vy=}")

    # metadata
    _md = {
        "detector_name": det.name,
        "x_name": xy.x.name,
        "y_name": xy.y.name,
        "x_start": x0,
        "x_end": x1,
        "y_start": y0,
        "y_end": y1,
        "duration": duration,
        "exposure_time": t_exposure,
        "update_period": update_period,
        "image mode": "Continuous",
        "velocity_x": vx,
        "velocity_y": vy,
    }
    _md.update(md or {})  # add any user metadata

    originals = {}

    def save_original_configurations():
        # backup original device configurations
        originals["xy"] = dict(xy.stage_sigs)
        originals["det_read_attrs"] = det.read_attrs
        originals["det"] = dict(det.stage_sigs)
        originals["det.cam"] = dict(det.cam.stage_sigs)

    def restore_original_configurations():
        xy.stage_sigs = dict(originals["xy"])
        det.cam.stage_sigs = dict(originals["det.cam"])
        det.stage_sigs = dict(originals["det"])
        det.read_attrs = originals["det_read_attrs"]

    def setup_staging():
        det.read_attrs = []
        # det.stage_sigs["cam.image_mode"] = 2  # "Continuous"
        det.cam.stage_sigs["acquire_time"] = t_exposure
        det.cam.stage_sigs["acquire_period"] = update_period
        det.cam.stage_sigs["image_mode"] = "Continuous"
        det.cam.stage_sigs["trigger_mode"] = "Internal"
        det.cam.stage_sigs["num_exposures"] = 1

        xy.stage_sigs["x.rb_update_period"] = update_period
        xy.stage_sigs["y.rb_update_period"] = update_period
        if vx != 0:
            xy.stage_sigs["x.velocity"] = vx
        if vy != 0:
            xy.stage_sigs["y.velocity"] = vy

        # print("(DEBUG) Stage prep complete")
        print(f"(DEBUG) {det.stage_sigs=}")
        print(f"(DEBUG) {det.cam.stage_sigs=}")
        # print(f"(DEBUG) {det.hdf1.stage_sigs=}")
        # print(f"(DEBUG) {det.pva.stage_sigs=}")

        det.hdf1.kind = "omitted"
        det.hdf1.disable_on_stage()
        det.pva.enable_on_stage()

    # describe the trajectory scan
    monitored_signals = [
        xy.x.readback, xy.y.readback,
        det.cam.array_counter, det.pva.array_counter,
    ]
    @bpp.stage_decorator([det, xy])
    @bpp.monitor_during_decorator(monitored_signals)
    @bpp.run_decorator(md=_md)
    def execute_the_trajectory_scan():
        # print("(DEBUG) execute_the_trajectory_scan() starting")
        print(f"(DEBUG) {det.cam.image_mode.get()=}")
        # print(f"(DEBUG) {det.hdf1.enable.get()=}")
        # print(f"(DEBUG) {det.pva.enable.get()=}")
        # print(f"(DEBUG) {xy.read()=}")

        # start
        yield from bps.mv(det.cam.acquire, 1)
        # print("images started")

        yield from bps.abs_set(xy.x, x1, group="motion")
        yield from bps.abs_set(xy.y, y1, group="motion")
        # print("motion started")

        # wait for motion to end, then stop AD
        yield from bps.wait(group="motion")
        yield from bps.mv(det.cam.acquire, 0)

    # before we start ...
    yield from bps.mv(
        det.cam.acquire, 0,
        xy.x.velocity, MAXIMUM_VELOCITY,
        xy.y.velocity, MAXIMUM_VELOCITY,
        det.hdf1.enable, "Disable",  # _before_ staging
        det.pva.enable, "Enable",
    )
    yield from bps.mv(
        xy.x, x0,
        xy.y, y0,
    )
    yield from bps.sleep(0.02)  # one 60Hz clock cycle, rounded up

    # proceed through these control steps
    save_original_configurations()
    setup_staging()
    uids = (yield from execute_the_trajectory_scan())
    restore_original_configurations()

    return uids

