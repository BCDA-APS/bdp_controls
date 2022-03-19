"""
calculations
"""

__all__ = """
    _incident_beam_calc
    _ad_x_calc
    _ad_y_calc
""".split()

from ..session_logs import logger

logger.info(__file__)

from ..utils import configuration_dict
from apstools.synApps import SwaitRecord
from apstools.synApps import UserCalcsDevice


PV = configuration_dict.get("INCIDENT_BEAM_SIMULATOR_CALC_PV")
_incident_beam_calc = SwaitRecord(PV, name="_incident_beam_calc")

PV = configuration_dict.get("ADSIM_X_CALC_PV")
_ad_x_calc = SwaitRecord(PV, name="_ad_x_calc")

PV = configuration_dict.get("ADSIM_Y_CALC_PV")
_ad_y_calc = SwaitRecord(PV, name="_ad_y_calc")

# # Normally, do not do _any_ actions (like these) in the instrument
# # package since that might affect other simultaneous use.  In this
# # case, the actions are probably OK.  Most users forget they even exist.
# # These steps enable all the userCalcN and userCalcoutN records to process.
if configuration_dict.get("ENABLE_CALCS", False):
    PV = configuration_dict.get("GP_IOC_PREFIX")

    # assumes all calcs are in same IOC (same prefix)
    # using the naming style of synApps xxx IOC
    calcs = UserCalcsDevice(PV, name="calcs")
    calcs.enable.put(1)
