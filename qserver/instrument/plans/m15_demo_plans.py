"""
ISN (tomocupy) demo for BDP Project Milestone M15

DATA

A single HDF5 file is used for this demo:

    ~/voyager/BDP/tomocupy-demo/data/Sm_c_3t_7p5x_pink_a_010.h5

PROCEDURE

- Before starting the `queueserver` process:
  - define `export BDP_DEMO=M15` in the bash shell
- Bluesky simulates data acquisition (using existing data folders)
  - for the demo: do not overwrite original source data
  - raw data:
    - use the one HDF5 file described above as workflow `filePath` parameter
    - call DM workflow once ALL data for a row is ready
- DM workflow `tomocupy` initiates data processing
  - The workflow has defaults for all other parameters
- ImageMagick's `display` (or `imagej` but is not on terrier) can be used to visualize the reconstruction results
  - `~/voyager/BDP/tomocupy-demo/analysis/*.tiff`
"""

__all__ = [
    "m15_simulated_isn",
]

import logging

logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

import datetime
import pathlib

import pyRestTable
from apstools.devices import make_dict_device
from apstools.plans import write_stream

# from bluesky import plans as bp
from bluesky import plan_stubs as bps
from bluesky import preprocessors as bpp

from .. import iconfig
from ..devices.data_management import DM_STATION_NAME, DM_WorkflowConnector

SECOND = 1
MINUTE = 60 * SECOND
DEFAULT_WAITING_TIME = 30 * MINUTE  # bluesky will raise TimeoutError if DM is not done

TITLE = "Simulate ISN data collection and processing with tomocupy"
DM_WORKFLOW_NAME = "tomocupy"
DEFAULT_SIMULATED_ACQUISITION_TIME = 5 * SECOND
WAIT_FOR_PREVIOUS_WORKFLOWS = False

VOYAGER = pathlib.Path().home() / "voyager" / "BDP"
TOMOCUPY_PATH = VOYAGER / "tomocupy-demo"
DATA_PATH = TOMOCUPY_PATH / "data"
TEST_FILE = DATA_PATH / "Sm_c_3t_7p5x_pink_a_010.h5"
DM_FILE_PATH = str(TEST_FILE)


def m15_simulated_isn(
    filePath=DM_FILE_PATH,
    workflow=DM_WORKFLOW_NAME,
    acquisition_time=DEFAULT_SIMULATED_ACQUISITION_TIME,
    dm_waiting_time=DEFAULT_WAITING_TIME,
    dm_wait=True,
    dm_concise=False,
    md={},
):
    """
    Simulate Tomo data collection and processing with tomocupy.
    """

    image_path = pathlib.Path(filePath)
    _md = dict(
        title=TITLE,
        description=("Simulate tomo acquisition for ISN and start DM workflow."),
        workflow=workflow,
        datetime=str(datetime.datetime.now()),
        data_management=dict(
            owner=DM_STATION_NAME,
            workflow=workflow,
            filePath=filePath,
            concise=dm_concise,
        ),
    )
    _md.update(md)

    logger.info(
        "In m15_simulated_isn() plan."
        f" {filePath=}"
        f" (exists: {image_path.exists()})"
        f" {acquisition_time=} s"
        f" {md=} s"
    )

    wf_cache = {}

    def print_cache_summary(title="Summary"):
        table = pyRestTable.Table()
        table.labels = "# process status runTime started id".split()
        for i, k in enumerate(wf_cache, start=1):
            v = wf_cache[k]
            job_id = v.job_id.get()
            started = datetime.datetime.fromtimestamp(v.start_time).isoformat(sep=" ")
            table.addRow(
                (
                    i,
                    k,
                    v.status.get(),
                    v.run_time.get(),
                    started,
                    job_id[:7],
                )
            )
        print(f"\n{title}\n{table}")

    def wait_workflows(period=10, wait=WAIT_FOR_PREVIOUS_WORKFLOWS):
        print(f"DEBUG: wait_workflows(): waiting={wait}")
        if wait:
            print(f"Waiting for all previous workflows ({len(wf_cache)}) to finish...")
            for workflow in wf_cache.values():
                # wait for each workflow to end
                while workflow.status.get() not in "done failed timeout".split():
                    print(f"Waiting for {workflow=}")
                    yield from bps.sleep(period)

    def report_tomocupy_output():
        stage_id = "03-TOMOCUPY"

        for wf in wf_cache.values():
            job = wf.getJob()
            stage = job.getWorkflowStage(stage_id)
            for process in stage.get("childProcesses", {}).values():
                for key in "stdOut stdErr".split():
                    value = str(process.get(key, "")).strip()
                    if len(value):
                        print(f"{stage_id}  {key}:\n{value}")
                        print("~" * 50)

    def get_data_file():
        for f in [
            TEST_FILE,
        ]:
            yield f

    def collect_full_series():
        logger.info("Bluesky plan m15_simulated_isn() starting.")
        for i, data_file in enumerate(get_data_file(), start=1):
            _md["data_file"] = data_file.name
            dm_workflow = DM_WorkflowConnector(name=f"dmwf_{i}", labels=["DM"])
            try:
                yield from collect_one(data_file, dm_workflow)
                print(f"Completed {str(data_file)}")
            except TimeoutError as exc_:
                logger.error("Data File: %s, error: %s", str(data_file), exc_)
            logger.info("Bluesky plan workflow complete. %s", dm_workflow)
        logger.info("Bluesky plan m15_simulated_isn() series complete.")

        yield from wait_workflows()  # TODO: add kwarg ``wait=True`` ?  It's an option.
        for wf in wf_cache.values():
            wf._update_processing_data()
        print_cache_summary()
        report_tomocupy_output()

    @bpp.run_decorator(md=_md)
    def collect_one(data_file, dm_workflow):
        logger.info("Simulated data collection for %s s.", acquisition_time)
        yield from bps.sleep(acquisition_time)
        print(f"Collected: {data_file=}")
        logger.info("Data file: %s", data_file.name)

        yield from wait_workflows()

        logger.info(f"Start DM workflow: {workflow=}")
        wf_cache[data_file.name] = dm_workflow
        yield from bps.mv(dm_workflow.concise_reporting, dm_concise)
        yield from dm_workflow.run_as_plan(
            workflow,
            wait=dm_wait,
            timeout=dm_waiting_time,
            # all kwargs after this line are DM argsDict content
            filePath=str(data_file),
        )
        yield from write_stream([dm_workflow], "dm_workflow")

    yield from collect_full_series()
