"""
Ophyd Devices for Bluesky measurements.
"""

print(__file__)

from .._iconfig_dict import iconfig

print(f"{__name__} {iconfig.get('BDP_DEMO')=}")
# define the devices
if iconfig.get("BDP_DEMO") in "M15 M16 M17 M18 M19".split():
    from .aps_source import *
    from .calculation_records import *
    from .data_management import *
    from .feedback_api import *
    from .ioc_stats import *
    from .samplexy_stage import *
    from .simulated_beam import *
    from .simulated_shutter import *

# area detectors come after previous devices are defined

if iconfig.get("BDP_DEMO") == "M4":
    # M4 demo
    from .ad_sim import *
elif iconfig.get("BDP_DEMO") == "M9":
    from .m9_devices import m9_flyer
elif iconfig.get("BDP_DEMO") == "M6":
    from .image_file_signal import *
    from .ad_pva import *

del iconfig
