"""
Bluesky measurement & support plans.
"""

from .._iconfig_dict import iconfig

from bluesky.plan_stubs import sleep
from .adjust_scan_id import *
if iconfig.get("BDP_DEMO") == "M4":
    from .game import *
    from .image_acquisition import *
    from .metadata_support import *
    from .move_positioners import *
    from .print_information import *
    from .shutter_controls import *
    from .trajectories import *
else:
    from .m6_demo_plans import *

del iconfig
