"""
Make a simulation for remote feedback to adjust.
"""

__all__ = ["new_sample", ]

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)


from ..devices import ad_x_calc
from ..devices import ad_y_calc
from ..devices import adsimdet
from ..devices import samplexy
from ..qserver_framework import RE
from bluesky import plan_stubs as bps
import random


def new_sample(coarse_gain=10, fine_gain=0.1, noise=2.5):
    """Configure for the game."""
    yield from bps.null()  # MUST yield something
    for calc in (ad_x_calc, ad_y_calc):
        calc.reset()
        axis = "x" if calc == ad_x_calc else "y"
        coarse = getattr(samplexy.coarse, axis.lower())
        fine = getattr(samplexy.fine, axis.lower())
        yield from bps.mv(
            adsimdet.cam.peak_width.peak_width_x, int(20 + random.random()*60),
            adsimdet.cam.peak_width.peak_width_y, int(20 + random.random()*60),
            calc.channels.A.input_value, 100 + random.random()*800,
            calc.channels.B.input_pv, coarse.user_readback.pvname,
            calc.channels.C.input_value, coarse_gain,
            calc.channels.D.input_pv, fine.pvname,
            calc.channels.E.input_value, fine_gain,
            calc.channels.F.input_value, noise,
            calc.calculation, "A+B*C+D*E+F*(2*RNDM-1)",
            calc.output_link_pv, f"{adsimdet.cam.prefix}PeakStart{axis.upper()}",
            calc.scanning_rate, ".1 second",
        )
    sample_name = (
        "simulated_sample"
        f"_{round(ad_x_calc.channels.A.input_value.get())}"
        f"_{round(ad_y_calc.channels.A.input_value.get())}"
    )
    RE.md["sample"] = sample_name
