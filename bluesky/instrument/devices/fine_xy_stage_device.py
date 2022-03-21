"""
Fine motion stage
"""

__all__ = ["fine_xy", ]

from ..session_logs import logger

logger.info(__file__)

from ..utils import configuration_dict
from ophyd import Component, Device, EpicsSignal


X_PV = configuration_dict.get("PZT_X_PV")
Y_PV = configuration_dict.get("PZT_Y_PV")


class XYstage_Fine(Device):
    x = Component(EpicsSignal, X_PV, labels=("piezo",))
    y = Component(EpicsSignal, Y_PV, labels=("piezo",))


fine_xy = XYstage_Fine("", name="fine_xy", labels=("stage",))
