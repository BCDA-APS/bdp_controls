"""
Simulated sample positioning stage with coarse & fine motions for X & Y axes.
"""

__all__ = ["samplexy", ]

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from ..iconfig_dict import iconfig
from ophyd import Component
from ophyd import Device
from ophyd import EpicsMotor
from ophyd import EpicsSignal
from ophyd import MotorBundle


class XyMotorStage(MotorBundle):
    x = Component(EpicsMotor, iconfig["XY_STAGE_X_PV"])
    y = Component(EpicsMotor, iconfig["XY_STAGE_Y_PV"])


class XyPiezoStage(Device):
    x = Component(EpicsSignal, iconfig["PZT_X_PV"])
    y = Component(EpicsSignal, iconfig["PZT_Y_PV"])


class CoarseFineStage(Device):
    coarse = Component(XyMotorStage, "")
    fine = Component(XyPiezoStage, "")


samplexy = CoarseFineStage("", name="samplexy")
