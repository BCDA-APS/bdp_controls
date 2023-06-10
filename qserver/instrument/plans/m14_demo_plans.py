"""
XRF demo for BDP Project Milestone M14

See the tutorial for an example dataset.
https://github.com/AdvancedPhotonSource/uProbeX/blob/master/docs/tutorial01.md

**Under construction!**

DATA

To run Bluesky on ``terrier`` (which cannot see ``invid:/local``), create a
``.tar`` file of the data we need and copy that where ``terrier`` can access it.
Includes this content from ``invid.aps.anl.gov:/local/data/XRF-demo``:

    ./*.txt
    ./mda/*
    ./flyXRF/2xfm_0007*.nc

```bash
ssh -X invid
mkdir /local/jemian
cd /local/data
tar czf /local/jemian/XRF-demo.tar.gz ./XRF-demo/
```

- (original) raw datasets:
  - on ``invid.aps.anl.gov:/local/data/XRF-demo``
  - ``./mda/2xfm_*.mda`` files have scaler info
  - ``./flyXRF/2xfm_*.nc`` files have spectra data
  - example, ``./mda/2xfm_0007.mda`` goes with
    -> ``./flyXRF/2xfm_0007_2xfm3_0.nc`` - ``./flyXRF/2xfm_0007_2xfm3_60.nc``

PROCEDURE

- Bluesky simulates data acquisition (using existing data folders)
  - for the demo: do not overwrite original source data
  - raw data:
    - working folder: run & PI in the name
    - `flyXRF` subfolder: netCDF files for the data rows
    - `mda` subfolder: MDA file for each row
    - `overwrite` file - ask Arthur about this
    - call DM workflow once ALL data for a row is ready
- DM workflow initiates data processing
  - Sinisa will create this workflow
- uProbeX GUI for XRF-Maps visualizes results
"""

__all__ = [
    "m14_simulated_xrf",
]

import logging

logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

import datetime
import pathlib

from apstools.devices import make_dict_device
from apstools.plans import write_stream
# from bluesky import plans as bp
from bluesky import plan_stubs as bps
from bluesky import preprocessors as bpp
import pyRestTable

from .. import iconfig
from ..devices.data_management import DM_WorkflowConnector, DM_STATION_NAME

SECOND = 1
MINUTE = 60 * SECOND

TITLE = "Simulate XRF data collection and processing"
VOYAGER = pathlib.Path().home() / "voyager"
XRF_PATH = VOYAGER / "BDP" / "XRF-demo"
MDA_PATH = XRF_PATH / "mda"
MDA_FILE_PREFIX = "2xfm"
DM_WORKFLOW_NAME = "xrf"
DEFAULT_FLY_SCAN_TIME = MINUTE
DM_FILE_PATH = str(XRF_PATH)
WAIT_FOR_PREVIOUS_WORKFLOWS = True
MAX_NUMBER_OF_MDA_FILES = 3


def m14_simulated_xrf(
    sample=MDA_FILE_PREFIX,
    filePath=DM_FILE_PATH,
    workflow=DM_WORKFLOW_NAME,
    fly_scan_time=DEFAULT_FLY_SCAN_TIME,
    dm_timeout=3 * MINUTE,
    dm_wait=True,
    dm_concise=False,
    md={},
):
    """
    Simulate XRF data collection and processing.

    See: https://github.com/APS-1ID-MPE/hexm-bluesky/blob/9fbe4efc2b6849a21dffd0c83f4b12bfb953fcdc/instrument/plans/bdp_plans.py#L31
    """
    # TODO: start DM workflow for each "line" of collected data (needs params)

    image_path = pathlib.Path(filePath)
    _md = dict(
        title=TITLE,
        description=(
            "Simulate fly scan acquisition of a set"
            " of image files and start DM workflow."
        ),
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
        "In m14_simulated_xrf() plan."
        f"  {filePath=}"
        f" (exists: {image_path.exists()})"
        f" {fly_scan_time=} s"
        f" {md=} s"
    )

    def get_mda_file(max_num=999_999):
        for index_, child in enumerate(sorted(MDA_PATH.iterdir())):
            if (
                child.is_file()
                and child.name.startswith(f"{sample}_")
                and child.suffix == ".mda"
                and index_ < max_num
            ):
                yield child

    wf_cache = {}

    def print_cache_summary(title="Summary"):
        table = pyRestTable.Table()
        table.labels = "# MDA status id".split()
        for i, k in enumerate(wf_cache, start=1):
            v = wf_cache[k]
            table.addRow((i, k, v.status.get(), v.job_id.get()))
        print(f"\n{title}\n{table}")

    def wait_workflows(period=10):
        print("DEBUG: wait_workflows()")
        if WAIT_FOR_PREVIOUS_WORKFLOWS:
            print("Waiting for all previous workflows to finish...")
            for workflow in wf_cache.values():
                # wait for each workflow to end
                while workflow.status.get() not in "done failed timeout".split():
                    print(f"Waiting for {workflow=}")
                    yield from bps.sleep(period)

    def collect_full_series():
        logger.info("Bluesky plan m14_simulated_xrf() starting.")
        for i, mda_file in enumerate(get_mda_file(max_num=MAX_NUMBER_OF_MDA_FILES)):
            _md["MDA_file"] = str(mda_file)
            # TODO: numFilesExpected=something,
            # time acq started
            # time acq ended
            dm_workflow = DM_WorkflowConnector(name=f"dmwf_{i}", labels=["DM"])
            try:
                yield from collect_one(mda_file, dm_workflow)
            except TimeoutError as exc_:
                logger.error("MDA: %s, error: %s", str(mda_file), exc_)
        logger.info("Bluesky plan m14_simulated_xrf() complete. %s", dm_workflow)

        yield from wait_workflows()
        print_cache_summary()

    @bpp.run_decorator(md=_md)
    def collect_one(mda_file, dm_workflow):
        logger.info("Simulated data collection for %s s.", fly_scan_time)
        yield from bps.sleep(fly_scan_time)
        print(f"Collected: {mda_file=}")
        logger.info("Data file: %s", mda_file.name)

        yield from wait_workflows()

        logger.info(f"Start DM workflow: {workflow=}")
        wf_cache[mda_file.name] = dm_workflow
        yield from bps.mv(dm_workflow.concise_reporting, dm_concise)
        yield from dm_workflow.run_as_plan(
            workflow,
            wait=dm_wait,  # TODO:
            timeout=dm_timeout,
            # all kwargs after this line are DM argsDict content
            filePath=str(mda_file),
            outputDataDir=str(XRF_PATH / "output"),
        )
        yield from write_stream([dm_workflow], "dm_workflow")

    yield from collect_full_series()
