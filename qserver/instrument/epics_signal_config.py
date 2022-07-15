"""
Set default timeouts for EPICS and define an EPICS-based scan_id.
"""

__all__ = """
    epics_scan_id_source
    scan_id_epics
""".split()

import logging
logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

from . import iconfig
from ophyd.signal import EpicsSignal
from ophyd.signal import EpicsSignalBase


# set default timeout for all EpicsSignal connections & communications
# always first, before ANY ophyd EPICS-based signals are created
TIMEOUT = 60
if not EpicsSignalBase._EpicsSignalBase__any_instantiated:
    EpicsSignalBase.set_defaults(
        auto_monitor=True,
        timeout=iconfig.get("PV_TIMEOUT", TIMEOUT),
        write_timeout=iconfig.get("PV_WRITE_TIMEOUT", TIMEOUT),
        connection_timeout=iconfig.get("PV_CONNECTION_TIMEOUT", TIMEOUT),
    )

pvname = iconfig.get("PV_CA_RUN_ENGINE_SCAN_ID")
if pvname is None:
    scan_id_epics = None
else:
    scan_id_epics = EpicsSignal(pvname, name="scan_id_epics")


def epics_scan_id_source(*args, **kwargs):
    """
    Callback function for RunEngine.  Returns *next* scan_id to be used.

    * Get current scan_id from PV.
    * Apply lower limit of zero.
    * Increment.
    * Set PV with new value.
    * Return new value.
    """
    if scan_id_epics is None:
        raise RuntimeError(
            "epics_scan_id_source() called when"
            " 'PV_CA_RUN_ENGINE_SCAN_ID' is"
             "undefined in 'iconfig.yml' file."
        )
    new_scan_id = max(scan_id_epics.get(), 0) + 1
    scan_id_epics.put(new_scan_id)
    return new_scan_id
