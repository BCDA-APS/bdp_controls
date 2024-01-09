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
elif iconfig.get("BDP_DEMO") == "M9":
    from .m9_demo_plans import m9_push_images
elif iconfig.get("BDP_DEMO") == "M14":
    from .m14_demo_plans import m14_simulated_xrf
elif iconfig.get("BDP_DEMO") in "M15 M16 M17 M18 M19".split():
    from .m15_demo_plans import m15_simulated_isn
    from .m16_demo_plans import m16_simulated_isn
    from .m17_demo_plans import m17_simulated_rsmap
    from .m18_demo_plans import m18_simulated_midas_ff
    from .m18_demo_gsasii import m18_simulated_gsasii
    from .m18_demo_gsasii import stop_gsasii_consumer_processing
    from .m19_demo_cohere import listruns
    from .m19_demo_cohere import m19_simulated_cohere
    from .m19_demo_cohere import wf_shell_tester_plan
    from .m19_demo_cohere import dm_add_experiment
    from .m19_demo_cohere import dm_delete_experiment
    from .m19_demo_cohere import dm_show_last_processing_job
    from .m19_demo_cohere import dm_show_experiments
    from .m19_demo_cohere import m19_0a_user_setup
    from .m19_demo_cohere import m19_0b_show_setup
    from .m19_demo_cohere import m19_1_create_dm_experiment
    from .m19_demo_cohere import m19_7_remove_dm_experiment
else:
    from .m6_demo_plans import *

del iconfig
