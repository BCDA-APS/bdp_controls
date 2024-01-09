"""
Cohere demo for BDP Project Milestone M19.

Simulate data collection and processing with cohere.
For ATOMIC, HEXM, and other beam lines.

- Before starting the `queueserver` process:
  - define `export BDP_DEMO=M19` in the bash shell

DEMO

-tba-  Run Cohere workflow

- Construct a workspace
    `~/DM/workflows/cohere/1-create_cohere_experiment.sh`

- 3 workflows, no parameters each (just a directory)
    (shell scripts 2, 3, & 4 called from DM workflow)
    preprocess
    reconstruct
    postprocess


- Data collection scan is a sweep of 3 angles (180 degrees).
- Example data is under `cohere-scripts/` below.

WORKFLOW KWARGS

    ~/DM/workflows/cohere/cohere/cohere-ui/cohere-scripts/create_experiment.py
    lines 142-150

```py
    parser.add_argument("working_dir", help="directory where the created experiment will be located")
    parser.add_argument("id", help="prefix to name of the experiment/data reconstruction")
    parser.add_argument("scan", help="a range of scans to prepare data from")
    parser.add_argument("beamline", help="beamline")
    parser.add_argument("data_dir", help="raw data directory")
    parser.add_argument("darkfield_filename", help="dark field file name")
    parser.add_argument("whitefield_filename", help="white field file name")
    parser.add_argument("specfile", help="full name, including path of specfile")
    parser.add_argument("diffractometer", help="diffractometer")
```

PROCEDURE

Create DM experiment
Stuff it with new data
Finalize

NEW

Upload bluesky run metadata to APS DM.

workflow directory
~/DM/workflows/cohere/
"""

__all__ = ["m19_simulated_cohere"]

import logging
import pathlib
import ast
import yaml

from bluesky import plan_stubs as bps
from bluesky import plans as bp
from ophyd import Component, Device, Signal

from .._iconfig_dict import iconfig
from ..devices.data_management import DM_STATION_NAME, DM_WorkflowConnector
from .bdp_demo_support import (
    MINUTE,
    SECOND,
    WF_BASE,
    WorkflowCache,
    build_run_metadata_dict,
    data_measurement_plan,
    get_workflow_last_stage,
    run_workflow_command,
    share_bluesky_metadata_with_dm,
)
from dev_dm_api import bdptools

logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

EXPERIMENT_NAME = "cohere-test"
DEFAULT_WAITING_TIME = 2 * MINUTE  # bluesky will raise TimeoutError if DM is not done

DM_WORKFLOW_DIR_NAME = "example-01"  # for testing purposes
DM_FINAL_STAGE = get_workflow_last_stage(DM_WORKFLOW_DIR_NAME)

DM_WORKFLOW_DIR_NAME = "cohere"
# for wff in "preprocess reconstruct postprocess".split():
#     DM_FINAL_STAGE = get_workflow_last_stage(DM_WORKFLOW_DIR_NAME, f"workflow-{wff}.py")
#     print(f"{wff=} {DM_FINAL_STAGE=}")

TITLE = __doc__.strip().split("\n")[0].strip()
DESCRIPTION = (
    "Simulate data collection with bluesky and processing with cohere."
    "  For ATOMIC, HEXM, and other beam lines."
)
DEFAULT_RUN_METADATA = {"title": TITLE, "description": DESCRIPTION}
DEFAULT_SIMULATED_ACQUISITION_TIME = 5 * SECOND
PLAIN_DM_ENV = {"HOME": str(pathlib.Path.home())}


class M19Device(Device):
    m19 = Component(Signal, value=19)
    experiment_name = Component(Signal, value=EXPERIMENT_NAME)


m19config = M19Device("", name="m19config")
obuffer = {}  # buffer for workflow command output


def m19_0a_user_setup(experiment_name=EXPERIMENT_NAME):
    yield from bps.mv(m19config.experiment_name, experiment_name)


def m19_0b_show_setup():
    from apstools.utils import listdevice

    yield from bps.null()
    print(listdevice(m19config))


def wf_shell_tester_plan(experiment_name=EXPERIMENT_NAME):
    wfd = DM_WORKFLOW_DIR_NAME
    script = "99-tester.sh"
    args = [m19config.experiment_name.get(), ]  # ignore user input, for now
    yield from run_workflow_command(obuffer, wfd, script, *args, env=PLAIN_DM_ENV)


def dm_add_experiment(experiment_name: str, typeName="BDP", kwargs={}):
    try:
        bdptools.dm_add_experiment(experiment_name, typeName=typeName, **kwargs)
    except Exception as exc:
        logger.error("dm_add_experiment(%r): %s", experiment_name, exc)
    experiment = bdptools.dm_get_experiments()[-1]
    print(yaml.dump(experiment))
    yield from bps.null()


def dm_delete_experiment(name_or_id: (int, str), use_caution=""):
    """DANGEROUS!  Can delete data forever.  Be very cautious!"""
    if use_caution == "I understand!":
        try:
            bdptools.dm_delete_experiment(name_or_id)
        except Exception as exc:
            logger.error("dm_delete_experiment(%r): %s", name_or_id, exc)
    else:
        print("Exercise great judgement before you delete a DM experiment!")
    yield from dm_show_experiments()


def dm_show_experiments(keys=bdptools.DEFAULT_DM_EXPERIMENT_KEYS, default_value="-na-"):
    """Show the experiments for the station."""
    try:
        table = bdptools.dm_get_experiments(
            table=True, keys=keys, default_value=default_value
            )
        print(table)
    except Exception as exc:
        logger.error("dm_show_experiments(): %s", exc)
    yield from bps.null()


def dm_show_last_processing_job(verbose=False):  # TODO: refactor with DM API
    """Show the last APS DM processing job.  Hacky."""
    # TODO: refactor with DM's API and move to bdp_demo_support module.
    wfd = DM_WORKFLOW_DIR_NAME
    script = "90-dm_last_processing_job.sh"
    args = []
    yield from run_workflow_command(obuffer, wfd, script, *args, env=PLAIN_DM_ENV)
    buf = ast.literal_eval(obuffer["stdout"].decode('utf-8'))
    if not verbose:
        buf.pop("workflow")
    print("Last APS DM processing job information:")
    print(yaml.dump(buf))


# def create_cohere_experiment(experiment_name=EXPERIMENT_NAME):
#     # ./2-create_cohere_experiment.sh ${EXPERIMENT_NAME}
#     script_file = "2-create_cohere_experiment.sh"
#     # --working_dir "${EXPERIMENT_ANALYSIS_DIR}" \
#     # --id scan \
#     # --scan 54 \
#     # --beamline aps_34idc \
#     # --data_dir "${EXPERIMENT_DATA_DIR}/AD34idcTIM2_example" \
#     # --darkfield_filename "${EXPERIMENT_DATA_DIR}/dark.tif" \
#     # --whitefield_filename "${EXPERIMENT_DATA_DIR}/whitefield.tif" \
#     # --specfile "${EXPERIMENT_DATA_DIR}/example.spec" \
#     # --diffractometer 34idc
#     yield from bps.null()


# def simulate_acquisition(experiment_name="experiment_name"):
#     # ./3-simulate_acquisition.sh ${EXPERIMENT_NAME}
#     script_file = "3-simulate_acquisition.sh"
#     yield from bps.null()


def data_measurement_plan(acquisition_time, uniqueId, **kwargs):
    """
    Perform (or simulate) the data measurement.
    """
    message = (
        f"Simulated data collection for {acquisition_time} s."
        f"  {uniqueId=}  {kwargs=}"
    )
    print(message)
    logger.info(message)
    yield from bps.sleep(acquisition_time)


def m19_simulated_cohere(
    signal_value=1,
    # parser.add_argument("working_dir", help="directory where the created experiment will be located")
    # parser.add_argument("id", help="prefix to name of the experiment/data reconstruction")
    # parser.add_argument("scan", help="a range of scans to prepare data from")
    # parser.add_argument("beamline", help="beamline")
    # parser.add_argument("data_dir", help="raw data directory")
    # parser.add_argument("darkfield_filename", help="dark field file name")
    # parser.add_argument("whitefield_filename", help="white field file name")
    # parser.add_argument("specfile", help="full name, including path of specfile")
    # parser.add_argument("diffractometer", help="diffractometer")
    md=DEFAULT_RUN_METADATA,
):
    """
    Simulate data collection and processing with cohere.
    For ATOMIC, HEXM, and other beam lines.
    """
    m19config.stage_sigs["m19"] = signal_value
    uid = yield from bp.count([m19config], md=md)
    share_bluesky_metadata_with_dm(uid=uid)


def listruns(num=5):
    """Print a table of the most recent runs to the console."""
    from apstools.utils import listruns

    yield from bps.null()
    print(listruns(num=num))
