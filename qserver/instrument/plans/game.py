"""
Make a simulation for remote feedback to adjust.
"""

__all__ = ["game_configure", ]

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)


from ..devices import ad_x_calc
from ..devices import ad_y_calc
from ..devices import adsimdet
from ..devices import samplexy
from bluesky import plan_stubs as bps
import random


def game_configure(coarse_gain=10, fine_gain=0.1, noise=2.5):
    """Configure for the game."""
    yield from bps.null()  # MUST yield something
    for calc in (ad_x_calc, ad_y_calc):
        calc.reset()
        axis = "x" if calc == ad_x_calc else "y"
        coarse = getattr(samplexy.coarse, axis.lower())
        fine = getattr(samplexy.fine, axis.lower())
        yield from bps.mv(
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
