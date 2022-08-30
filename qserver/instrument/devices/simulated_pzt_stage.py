"""
Simulated Piezo X,Y Stage with Velocity-Controlled Readbacks.

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

# __all__ = ["fastxy"]

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from .. import iconfig
from apstools.devices import PVPositionerSoftDoneWithStop
from apstools.synApps import SwaitRecord
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
MAXIMUM_VELOCITY = 10_000


class LimitedVelocitySignal(Signal):
    """Override the default limits of (0,0)."""

    @property
    def limits(self):
        """The control limits (low, high), such that low <= value <= high."""
        return (MINIMUM_VELOCITY, MAXIMUM_VELOCITY)

    def check_value(self, value):
        """Check if the value is within the setpoint PV's control limits."""
        super().check_value(value)

        if value is None:
            raise ValueError('Cannot write None to epics PVs')

        low_limit, high_limit = self.limits
        if low_limit >= high_limit:
            return

        if not (low_limit <= value <= high_limit):
            raise LimitError(
                f"{self.name}: value {value}"
                f" outside of range {low_limit} .. {high_limit}"
            )


class SimulatedConstantVelocityPositioner(PVPositionerSoftDoneWithStop):
    # the readback must be writable in this simulator
    readback = FormattedComponent(
        EpicsSignal, "{prefix}{_readback_pv}", kind="hinted", auto_monitor=True
    )
    velocity = Component(
        LimitedVelocitySignal, value=DEFAULT_VELOCITY, kind="config"
    )
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


class SwaitPositioner(PVPositionerSoftDoneWithStop):
    # the readback must be writable in this simulator
    readback = FormattedComponent(
        EpicsSignal, "{prefix}{_readback_pv}", kind="hinted", auto_monitor=True
    )

    def __init__(self, *args, swait=None, **kwargs):
        if not isinstance(swait, SwaitRecord):
            raise KeyError(f"'swait' must be instance of SwaitRecord")
        self.swait_configure(swait, kwargs["setpoint_pv"], kwargs["readback_pv"])
        super().__init__(*args, **kwargs)

    def swait_configure(self, swait, sp_pv, rb_pv):
        print(f"Resetting {swait.name}")
        swait.reset()
        STEP_FACTOR = 0.3  # 1.0 is one-step

        swait.description.put("SwaitPositioner")
        swait.precision.put("5")
        swait.channels.A.input_pv.put(sp_pv)
        swait.channels.B.input_pv.put(
            swait.calculated_value.pvname
        )
        swait.channels.C.input_value.put(STEP_FACTOR)
        swait.output_execute_option.put("Every Time")
        swait.output_link_pv.put(rb_pv)

        print(f"Setting calculation: {swait.name}")

        swait.calculation.put("B+C*(A-B)")
        swait.scanning_rate.put(".1 second")
        print(f"Done configuring {swait.name}")


if iconfig.get("BDP_DEMO") == "M4":
    swait_x = SwaitRecord(iconfig["PV_CA_FINE_X_SWAIT"], name="swait_x")
    swait_y = SwaitRecord(iconfig["PV_CA_FINE_Y_SWAIT"], name="swait_y")

    class SimulatedPiezoXyStageWithReadback(Device):
        """
        Simulated Piezo X,Y Stage with Velocity-Controlled Readbacks.

            fastxy = SimulatedPiezoXyStageWithReadback("", name="fastxy")

        """
        x = Component(
            SwaitPositioner,
            "",
            readback_pv=iconfig["PV_CA_FAST_UPDATE_X_RBV"],
            setpoint_pv=iconfig["PV_CA_FAST_UPDATE_X_VAL"],
            swait=swait_x,
            tolerance=0.0002,
            kind="hinted",
        )
        y = Component(
            SwaitPositioner,
            "",
            readback_pv=iconfig["PV_CA_FAST_UPDATE_Y_RBV"],
            setpoint_pv=iconfig["PV_CA_FAST_UPDATE_Y_VAL"],
            swait=swait_y,
            tolerance=0.0002,
            kind="hinted",
        )

        @property
        def inposition(self):
            return self.x.inposition and self.y.inposition

else:
    class SimulatedPiezoXyStageWithReadback(Device):
        """
        Simulated Piezo X,Y Stage with Velocity-Controlled Readbacks.

            fastxy = SimulatedPiezoXyStageWithReadback("", name="fastxy")

        """
        x = Component(
            SimulatedConstantVelocityPositioner,
            "",
            readback_pv=iconfig["PV_CA_FAST_UPDATE_X_RBV"],
            setpoint_pv=iconfig["PV_CA_FAST_UPDATE_X_VAL"],
            tolerance=0.0002,
            kind="hinted",
        )
        y = Component(
            SimulatedConstantVelocityPositioner,
            "",
            readback_pv=iconfig["PV_CA_FAST_UPDATE_Y_RBV"],
            setpoint_pv=iconfig["PV_CA_FAST_UPDATE_Y_VAL"],
            tolerance=0.0002,
            kind="hinted",
        )

        @property
        def inposition(self):
            return self.x.inposition and self.y.inposition
