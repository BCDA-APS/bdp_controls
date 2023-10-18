"""
rsMap3D demo for BDP Project Milestone M17

DATA

Files used for this demo are located at:
    /gdata/bdp/BDP/rsmap3D-demo/data/

PROCEDURE

- Before starting the `queueserver` process:
  - define `export BDP_DEMO=M17` in the bash shell
- Bluesky simulates data acquisition (using existing data folders)
  - for the demo: do not overwrite original source data
  - raw data:
    - use the one HDF5 file described above as workflow `filePath` parameter
    - call DM workflow once ALL data for a row is ready
- DM workflow `rsmap3D` initiates data processing
  - The workflow has defaults for all other parameters
- Paraview can be used to visualize the reconstruction results

"""

__all__ = [
    "m17_simulated_rsmap",
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

TITLE = "Simulate diffraction data collection and processing with rsmap3D"
DM_WORKFLOW_NAME = "rsmap3D"
DEFAULT_SIMULATED_ACQUISITION_TIME = 5 * SECOND
WAIT_FOR_PREVIOUS_WORKFLOWS = False
TEST_FILE = pathlib.Path('/gdata/bdp/BDP/rsmap3D-demo/data/PZT_STO')
DM_DATA_DIR = str(TEST_FILE)


def m17_simulated_rsmap(
    dataDir=DM_DATA_DIR,
    workflow=DM_WORKFLOW_NAME,
    acquisition_time=DEFAULT_SIMULATED_ACQUISITION_TIME,
    dm_waiting_time=DEFAULT_WAITING_TIME,
    dm_wait=True,
    dm_concise=False,
    md={},
):
    """
    Simulate diffration data collection and processing with rsmap3D.
    """
    dataDir = pathlib.Path(dataDir)
    _md = dict(
        title=TITLE,
        description=(
            "Simulate diffraction acquisition and start DM workflow."
        ),
        workflow=workflow,
        datetime=str(datetime.datetime.now()),
        data_management=dict(
            owner=DM_STATION_NAME,
            workflow=workflow,
            dataDir=str(dataDir),
            concise=dm_concise,
        ),
    )
    _md.update(md)

    logger.info(
        "In m17_simulated_rsmap() plan."
        f" {dataDir=}"
        f" (exists: {dataDir.exists()})"
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

    def report_rsmap3D_output():
        stage_id = "03-DONE"

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
        logger.info("Bluesky plan m17_simulated_rsmap() starting.")
        for i, data_file in enumerate(get_data_file(), start=1):
            _md["data_file"] = data_file.name
            dm_workflow = DM_WorkflowConnector(name=f"dmwf_{i}", labels=["DM"])
            try:
                yield from collect_one(data_file, dm_workflow)
                print(f"Completed {str(data_file)}")
            except TimeoutError as exc_:
                logger.error("Data File: %s, error: %s", str(data_file), exc_)
            logger.info("Bluesky plan workflow complete. %s", dm_workflow)
        logger.info("Bluesky plan m17_simulated_rsmap() series complete.")

        yield from wait_workflows()  # TODO: add kwarg ``wait=True`` ?  It's an option.
        for wf in wf_cache.values():
            wf._update_processing_data()
        print_cache_summary()
        report_rsmap3D_output()

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
            dataDir=str(data_file),
        )
        yield from write_stream([dm_workflow], "dm_workflow")
    yield from collect_full_series()
