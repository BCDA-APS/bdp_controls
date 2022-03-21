"""
Coarse (EPICS motor) stage
"""

__all__ = ["coarse_xy", ]

from ..session_logs import logger

logger.info(__file__)

from ..utils import configuration_dict
from ophyd import Component, EpicsMotor, MotorBundle


X_PV = configuration_dict.get("XY_STAGE_X_PV")
Y_PV = configuration_dict.get("XY_STAGE_Y_PV")


class XYstage_Coarse(MotorBundle):
    x = Component(EpicsMotor, X_PV, labels=("motor",))
    y = Component(EpicsMotor, Y_PV, labels=("motor",))


coarse_xy = XYstage_Coarse("", name="coarse_xy", labels=("stage",))
