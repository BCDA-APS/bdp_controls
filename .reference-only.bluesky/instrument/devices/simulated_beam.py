"""
incident beam

nominal: peak +/- random noise, only when shutter is open
"""

__all__ = [
    "incident_beam",
    "setup_beam_parameters_calc",
]

from ..session_logs import logger

logger.info(__file__)

from .calculation_records import _incident_beam_calc as calc
from apstools.synApps import SwaitRecord
from .simulated_shutter import shutter
import math
from ophyd import EpicsSignalRO


PEAK_VALUE = 200
NOISE_VALUE = "shot"


def cb_shutter(*args, value=0, **kwargs):
    # When simulated (Python-only) shutter changes, update EPICS calc
    if value == "close":
        value = 0
    elif value == "open":
        value = 1
    calc.channels.A.input_value.put(value)


def setup_beam_parameters_calc(peak=100, noise=0.05):
    """
    Setup the swait record to simulate an incident intensity.

    BLOCKING calls, not a bluesky plan
    """
    calc.reset()
    calc.description.put("incident beam simulator")

    # A: shutter (1 or 0)
    cb_shutter(shutter.state)
    # calc.channels.A.input_value.put(shutter.pss_state.get(as_string=False))

    # B: peak (float)
    calc.channels.B.input_value.put(peak)

    # C: noise (float, "shot")
    if isinstance(noise, str):  # and noise == "shot":
        noise = 1/math.sqrt(peak)
    calc.channels.C.input_value.put(noise)

    # CALC: shutter & peak +/- noise
    calc.calculation.put("A*B*(1+C*(RNDM-0.5))")

    calc.scanning_rate.put(".1 second")


incident_beam = EpicsSignalRO(
    calc.prefix, name="incident_beam", labels=("simulator", )
)
setup_beam_parameters_calc(peak=PEAK_VALUE, noise=NOISE_VALUE)

shutter.pss_state.subscribe(cb_shutter)
