"""
GSAS-II demo for BDP Project Milestone M18.

DATA

- This demo communicates with DM worfklow process via PVA PV hosted here.
- No files used for this demo.

PROCEDURE

- Before starting the `queueserver` process:
  - define `export BDP_DEMO=M18` in the bash shell
- Bluesky:
  - start PVA server with PV: "pvapy:GSASII"
  - start a DM workflow
  - iterate through series of data files
    - assign uniqueID to each file
    - update pv with uniqueID and file name (!)
    - short (1 s) delay
  - once series is finished
    - wait a short time (5-10s)
    - send STOP command on control channel
  - wait for workflow to finish

GENERAL DM WORKFLOW HINTS

To check on details for a specific workflow job (by its ID),
try this command::

    ~/DM/bin/dm-list-processing-jobs \
        --display-keys=ALL \
        --display-format=pprint \
        id:WORKFLOW_UUID

Or the most recent job::

    ~/DM/bin/dm-get-last-processing-job   --display-format=pprint

Note that these commands might fail with an ImportError if run from
a conda environment.  Check that `CONDA_SHLVL=1`: `conda deactivate`
until you get that.
"""

plan_name = "m18_simulated_gsasii"
__all__ = [
    plan_name,
    "stop_gsasii_consumer_processing"
]

import datetime
import logging
import pathlib

logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)


import pvaccess as pva
from apstools.plans import run_blocking_function
from apstools.plans import write_stream
from apstools.utils import unix
from bluesky import plan_stubs as bps
from bluesky import preprocessors as bpp
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
)

DEFAULT_WAITING_TIME = 2 * MINUTE  # bluesky will raise TimeoutError if DM is not done

DM_WORKFLOW_NAME = "gsasii"
DM_FINAL_STAGE = get_workflow_last_stage(DM_WORKFLOW_NAME)

TITLE = __doc__.strip().split("\n")[0].strip()
# DESCRIPTION = "Simulate data acquisition and start DM workflow"
DESCRIPTION = "GSAS-II Sequential Peak Fitting"
DEFAULT_RUN_METADATA = {"title": TITLE, "description": DESCRIPTION}
DEFAULT_SIMULATED_ACQUISITION_TIME = 5 * SECOND

CONSUMER_CONTROL_PV = "consumer:1:control"


class ImageDevice(Device):
    uniqueID = Component(Signal, value=-1)
    data_file = Component(Signal, value="")

image_device = ImageDevice(name="image_device")

# start the PVA IOC
pv = pva.PvObject({"uniqueId": pva.UINT, "datafile": pva.STRING})
server = pva.PvaServer(iconfig["PV_PVA_M18_GSASII"], pv)
server.start()


def run_workflow_command(shell_command, raises=False):
    path = WF_BASE / DM_WORKFLOW_NAME / shell_command
    if not path.exists():
        raise FileNotFoundError(f"Workflow executable {path} not found.")
    yield from run_blocking_function(unix, str(path), raises=False)


def stop_gsasii_consumer_processing():
    """(plan) Tell the GSAS-II consumer process to stop its processing."""

    yield from run_workflow_command("5-stop_consumer.py")

    # FIXME:
    # stop_dict = pva.PvObject({"command": pva.STRING}, {"command": "stop"})

    # # stop application
    # logger.info("Sending STOP command to remote GSAS-II computing process.")
    # print("Sending STOP command to remote GSAS-II computing process.")
    # control_channel = pva.Channel(CONSUMER_CONTROL_PV)
    # yield from bps.sleep(0.2)
    # if control_channel.isConnected():
    #     print(f"Connected with control pv {CONSUMER_CONTROL_PV=}")
    #     control_channel.put(stop_dict)

    #     # get last command status
    #     response = control_channel.get()
    #     print(f"STOP command sent.  {response=}")
    # else:
    #     print(f"Did not connect with control pv {CONSUMER_CONTROL_PV=}")
    #     logger.warning("Did not connect with control pv %s", CONSUMER_CONTROL_PV)


def file_series(start=435, end=496):
    for n in range(start, end):
        print(f"file_series: {n=}")
        yield pathlib.Path(f"{n}.gda")


def data_measurement_plan(acquisition_time, uniqueId, dataFile):
    """
    Perform (or simulate) the data measurement.

    Override the standard simulator.  Post file name via PV Access.
    """
    pv.set({"uniqueId": uniqueId, "datafile": dataFile})
    server.update(pv)
    image_device.uniqueID.put(uniqueId)
    image_device.data_file.put(dataFile)
    print(f"Simulated data collection for {acquisition_time} s.")
    logger.info("Simulated data collection for %s s.", acquisition_time)
    yield from bps.sleep(acquisition_time)
    print(f"'Collected': {pv=}")


def m18_simulated_gsasii(
    # user kwargs ----------------------------------------
    workflow=DM_WORKFLOW_NAME,
    acquisition_time=DEFAULT_SIMULATED_ACQUISITION_TIME,
    title=TITLE,
    description=DESCRIPTION,
    n_start=435,
    n_end=496,  # up to, but not including
    measurement_delay_s=1 * SECOND,
    initial_delay_s=1 * SECOND,
    final_delay_s=10 * SECOND,
    # internal kwargs ----------------------------------------
    dm_waiting_time=DEFAULT_WAITING_TIME,
    dm_wait=False,
    dm_concise=False,
    md=DEFAULT_RUN_METADATA,
):
    _md = build_run_metadata_dict(
        md,
        owner=DM_STATION_NAME,
        workflow=workflow,
        # dataDir=str(dataDir),
        concise=dm_concise,
    )
    wf_cache = WorkflowCache()

    @bpp.run_decorator(md=_md)
    def collection(dm_workflow):
        for unique_id, data_file in enumerate(file_series(n_start, n_end), start=0):
            logger.info("Data file: %s", data_file.name)
            yield from bps.sleep(measurement_delay_s)
            yield from data_measurement_plan(acquisition_time, unique_id, data_file.name)
            yield from write_stream([image_device], "primary")

        yield from write_stream([dm_workflow], "dm_workflow")
    
    logger.info(f"Start DM workflow: {workflow=}")
    dm_workflow = DM_WorkflowConnector(name=f"dmwf_gsasii", labels=["DM"])
    print(f"{dm_workflow=}")
    wf_cache.define_workflow("GSAS-II-process", dm_workflow)
    print("dm_workflow() defined")

    yield from bps.mv(dm_workflow.concise_reporting, dm_concise)
    yield from dm_workflow.run_as_plan(
        workflow,
        wait=dm_wait,
        timeout=dm_waiting_time,
        # all kwargs after this line are DM argsDict content
        filePath=f"ignored-using-PVA",
    )

    # For the M18 demo on 2023-11-07
    # TODO: Implement via PVA here
    yield from bps.sleep(initial_delay_s)
    yield from run_workflow_command("2-configure_consumer.py")
    print("Pause 8s for user to start c2dv from command line ...")
    yield from bps.sleep(8)
    # For demo, start from command line.
    # yield from run_workflow_command("3-start_viewer.sh")

    print("collection starting")
    yield from collection(dm_workflow)

    print(f"collection completed, waiting {final_delay_s:.1f}s more")
    yield from bps.sleep(final_delay_s)

    print("Sending STOP to remote process.")
    yield from stop_gsasii_consumer_processing()

    print(f"Wait for workflows: {dm_wait=}")
    yield from wf_cache.wait_workflows(wait=dm_wait)

    wf_cache._update_processing_data()
    wf_cache.print_cache_summary()
    wf_cache.report_dm_workflow_output(DM_FINAL_STAGE)
