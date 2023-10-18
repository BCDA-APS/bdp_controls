"""
MIDAS (HEXM) demo for BDP Project Milestone M18

DATA

Files used for this demo are located at:
    /gdata/bdp/BDP/park_mar22_midas

PROCEDURE

- Before starting the `queueserver` process:
  - define `export BDP_DEMO=M18` in the bash shell
- Bluesky simulates data acquisition (using existing data folders)
  - for the demo: do not overwrite original source data
  - raw data:
    - data file source directory as stated above
    - call DM workflow once per "data acquisition"
- DM workflow `midas-ff` initiates data processing
  - ... other parameters
- (???) can be used to visualize the reconstruction results
"""

plan_name = "m18_simulated_midas_ff"
__all__ = [plan_name, ]

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

TITLE = __doc__.strip().split("\n")[0].strip()
DM_WORKFLOW_NAME = "midas-ff"
DM_EXPERIMENT_NAME = "park_mar22_midas"
DEFAULT_SIMULATED_ACQUISITION_TIME = 5 * SECOND
WAIT_FOR_PREVIOUS_WORKFLOWS = False
VOYAGER_PATH = pathlib.Path("/gdata/bdp")
TEST_DATA_PATH = VOYAGER_PATH / "BDP" / DM_EXPERIMENT_NAME / "data"
TEST_FILE_PATH = TEST_DATA_PATH / "park_ss_ff_0MPa_000315.edf.ge5"
DM_WORKFLOW_PATH = VOYAGER_PATH / "BDP" / DM_WORKFLOW_NAME
PS_TEMPLATE_FILE_PATH = DM_WORKFLOW_PATH / "ps_template.txt"

DEFAULT_RUN_METADATA = {
    "title": TITLE,
    "description": "Simulate data acquisition and start DM workflow.",
}

def data_measurement(data_file, acquisition_time):
    logger.info("Simulated data collection for %s s.", acquisition_time)
    yield from bps.sleep(acquisition_time)
    print(f"Collected: {data_file=}")


def m18_simulated_midas_ff(
    dataDir=str(TEST_DATA_PATH),
    workflow=DM_WORKFLOW_NAME,
    acquisition_time=DEFAULT_SIMULATED_ACQUISITION_TIME,
    # lots of workflow kwargs for MIDAS ----------------------------------------
    filePath=str(TEST_FILE_PATH),
    experimentName=DM_EXPERIMENT_NAME,
    nCpus=96,
    darkFileName="dark_before_000245.edf.ge5",
    nFilesPerLayer=1,
    nFramesPerLayer=1440,
    wavelength=0.172979,
    headerSize=8396800,
    imageTransformations="0",
    beamCurrent="1",
    saturationIntensity="12000",
    omegaStep="-0.25",
    omegaFirstFrame="180",
    pixelSize="200",
    nPixelsY=2048,
    nPixelsZ=2048,
    omegaRange= "-180 -106 -76 74 105 180",
    boxSize= "-1000000 1000000 -1000000 1000000 -1000000 1000000 -1000000 1000000 -1000000 1000000 -1000000 1000000",
    ps_template_file_path=str(PS_TEMPLATE_FILE_PATH),
    # workflow kwargs ----------------------------------------
    dm_waiting_time=DEFAULT_WAITING_TIME,
    dm_wait=True,
    dm_concise=False,
    md=DEFAULT_RUN_METADATA,
):
    """
    Simulate diffration data collection and processing with MIDAS.
    """
    dataDir = pathlib.Path(dataDir)
    _md = dict(
        title=TITLE,
        description="Simulate data acquisition and start DM workflow",
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
        f"In {plan_name}() plan."
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

    def report_dm_workflow_output():
        stage_id = "06-DONE"

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
            TEST_FILE_PATH,
        ]:
            yield f

    @bpp.run_decorator(md=_md)
    def collect_one(data_file, dm_workflow):
        yield from data_measurement(data_file, acquisition_time)
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
            filePath=filePath,
            experimentName=experimentName,
            nCpus=nCpus,
            darkFileName=darkFileName,
            nFilesPerLayer=nFilesPerLayer,
            nFramesPerLayer=nFramesPerLayer,
            wavelength=wavelength,
            headerSize=headerSize,
            imageTransformations=imageTransformations,
            beamCurrent=beamCurrent,
            saturationIntensity=saturationIntensity,
            omegaStep=omegaStep,
            omegaFirstFrame=omegaFirstFrame,
            pixelSize=pixelSize,
            nPixelsY=nPixelsY,
            nPixelsZ=nPixelsZ,
            omegaRange=omegaRange,
            boxSize=boxSize,
            ps_template_file_path=ps_template_file_path,
        )
        # FIXME: workflow arguments
        yield from write_stream([dm_workflow], "dm_workflow")

    def collect_full_series():
        logger.info(f"Bluesky plan {plan_name}() starting.")
        for i, data_file in enumerate(get_data_file(), start=1):
            _md["data_file"] = data_file.name
            dm_workflow = DM_WorkflowConnector(name=f"dmwf_{i}", labels=["DM"])
            try:
                yield from collect_one(data_file, dm_workflow)
                print(f"Completed {str(data_file)}")
            except TimeoutError as exc_:
                logger.error("Data File: %s, error: %s", str(data_file), exc_)
            logger.info("Bluesky plan workflow complete. %s", dm_workflow)
        logger.info(f"Bluesky plan {plan_name}() series complete.")

        yield from wait_workflows()  # TODO: add kwarg ``wait=True`` ?  It's an option.
        for wf in wf_cache.values():
            wf._update_processing_data()
        print_cache_summary()
        report_dm_workflow_output()

    yield from collect_full_series()
