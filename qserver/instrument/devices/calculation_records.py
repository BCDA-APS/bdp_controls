"""
calculations
"""

__all__ = """
    incident_beam_calc
    ad_x_calc
    ad_y_calc
""".split()

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from .. import iconfig
from apstools.synApps import SwaitRecord
from ophyd import EpicsSignal


PV = iconfig.get("PV_CA_INCIDENT_BEAM_SIMULATOR_CALC")
incident_beam_calc = SwaitRecord(PV, name="incident_beam_calc")

PV = iconfig.get("PV_CA_ADSIM_X_CALC")
ad_x_calc = SwaitRecord(PV, name="ad_x_calc")

PV = iconfig.get("PV_CA_ADSIM_Y_CALC")
ad_y_calc = SwaitRecord(PV, name="ad_y_calc")

# Normally, do not do _any_ actions (like these) in the instrument
# package since that might affect other simultaneous use.  In this
# case, the actions are probably OK.  Most users forget they even exist.
# These steps enable all the userCalcN and userCalcoutN records to process.
if iconfig.get("ENABLE_CALCS", False):
    PV = iconfig.get("IOC_PREFIX_GP")

    # assumes all calcs are in same IOC (same prefix)
    # using the naming style of synApps xxx IOC
    enable = EpicsSignal(f"{PV}userCalcEnable", name="enable")
    enable.wait_for_connection()
    enable.put(1)
