"""
Simulated Fast X,Y Stage: fastxy

Simulates a piezo stage with X, Y with positioners.  Each has a setpoint,
readback, and velocity control.  Readback will update in a thread during
each move at constant velocity and time intervals.

``rb_update_period`` (float):
    Period (s) at which the readback is updated during motion.
    Empirically, shortest value is 0.004.  Any shorter compromises
    the position updates.  Default: 0.05

``velocity`` (float):
    Maximum speed (position/s) at which the readback is advanced during
    motion.  Ranges from 0.000_1 (creepy slow) to 100 (almost instantaneous).
    Default: 1.0
"""

__all__ = ["fastxy"]

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from .. import iconfig
from apstools.devices import PVPositionerSoftDoneWithStop
from apstools.utils import run_in_thread
from ophyd import Component
from ophyd import Device
from ophyd import EpicsSignal
from ophyd import FormattedComponent
from ophyd import Signal
import numpy as np
import time


DEFAULT_UPDATE_PERIOD = 0.05
DEFAULT_VELOCITY = 1
DELAY_AFTER_CAPUT = 0.000_1
LOOP_SLEEP = 0.000_1
MINIMUM_VELOCITY = 0.000_1
MAXIMUM_VELOCITY = 100


class SimulatedConstantVelocityPositioner(PVPositionerSoftDoneWithStop):
    # the readback must be writable in this simulator
    readback = FormattedComponent(
        EpicsSignal, "{prefix}{_readback_pv}", kind="hinted", auto_monitor=True
    )
    velocity = Component(Signal, value=DEFAULT_VELOCITY, kind="config")
    rb_update_period = Component(
        Signal, value=DEFAULT_UPDATE_PERIOD, kind="config"
    )

    def _setup_move(self, position):
        """Move and do not wait until motion is complete (asynchronous)"""
        super()._setup_move(position)

        self._stop_motion_profile = False
        self.motion_simulator(position)

    @run_in_thread
    def motion_simulator(self, position):
        # Enable the desired simulator (or write a new one).
        # self.move_immediately_to_end(position)
        self.change_readback_by_linear_steps(position)

    def move_immediately_to_end(self, end):
        self.readback.put(end)

    def change_readback_by_linear_steps(self, end):
        start = self.readback.get(use_monitor=False)
        velocity = min(
            MAXIMUM_VELOCITY, max(MINIMUM_VELOCITY, abs(self.velocity.get()))
        )
        motion_time = abs(end - start) / velocity
        period = abs(self.rb_update_period.get())
        n_updates = 1 + int(motion_time / period)

        times = np.linspace(0, motion_time, n_updates, endpoint=True)
        positions = np.linspace(start, end, n_updates, endpoint=True)

        # absolute times!
        self.update_readback_at_timed_waypoints(
            zip(time.time() + times, positions)
        )

    def update_readback_at_timed_waypoints(self, waypoints):
        for t, rbv in waypoints:
            while time.time() < t:
                if self._stop_motion_profile:  # emergency stop
                    return
                time.sleep(LOOP_SLEEP)

            if self._stop_motion_profile:  # emergency stop
                return

            self.readback.put(rbv, wait=True)
            time.sleep(DELAY_AFTER_CAPUT)

    def stop(self, *, success=False):
        """
        Hold the current readback when stop() is called and not :meth:`inposition`.
        """
        self._stop_motion_profile = True
        super().stop(success=success)


class FastUpdateXyStage(Device):
    x = Component(
        SimulatedConstantVelocityPositioner, 
        "",
        readback_pv=iconfig["FAST_UPDATE_X_RBV"],
        setpoint_pv=iconfig["FAST_UPDATE_X_VAL"],
        tolerance=0.0002,
        kind="hinted",
    )
    y = Component(
        SimulatedConstantVelocityPositioner, 
        "",
        readback_pv=iconfig["FAST_UPDATE_Y_RBV"],
        setpoint_pv=iconfig["FAST_UPDATE_Y_VAL"],
        tolerance=0.0002,
        kind="hinted",
    )


fastxy = FastUpdateXyStage("", name="fastxy")
