"""
Simulated sample positioning stage with coarse & fine motions for X & Y axes.
"""

__all__ = ["samplexy", ]

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from .. import iconfig
from .simulated_pzt_stage import SimulatedPiezoXyStageWithReadback
from ophyd import Component
from ophyd import Device
from ophyd import EpicsMotor
from ophyd import EpicsSignal
from ophyd import MotorBundle


class XyMotorStage(MotorBundle):
    x = Component(EpicsMotor, iconfig["PV_CA_XY_STAGE_X"])
    y = Component(EpicsMotor, iconfig["PV_CA_XY_STAGE_Y"])


class XyPiezoStage(Device):
    x = Component(EpicsSignal, iconfig["PV_CA_PZT_X"])
    y = Component(EpicsSignal, iconfig["PV_CA_PZT_Y"])


class CoarseFineStage(Device):
    coarse = Component(XyMotorStage, "")
    fine = Component(SimulatedPiezoXyStageWithReadback, "")


samplexy = CoarseFineStage("", name="samplexy")
