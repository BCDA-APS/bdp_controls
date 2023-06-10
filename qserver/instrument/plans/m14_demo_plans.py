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

from .. import iconfig
from ..devices.data_management import dm_workflow, DM_WorkflowConnector

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
dm_workflow.workflow.put(DM_WORKFLOW_NAME)


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
            owner=dm_workflow.owner.get(),
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

    def collect_data(max_num=5):
        for index_, child in enumerate(sorted(MDA_PATH.iterdir())):
            if (
                child.is_file()
                and child.name.startswith(f"{sample}_")
                and child.suffix == ".mda"
                and index_ < max_num
            ):
                yield child

    @bpp.run_decorator(md=_md)
    def _inner():
        for mda_file in collect_data(max_num=5):
            logger.info("Simulated data collection for %s s.", fly_scan_time)
            yield from bps.sleep(fly_scan_time)
            print(f"{mda_file=}")
            logger.info("Data file: %s", mda_file.name)

            # sim = make_dict_device(dict(x=1, y=2), name="sim")
            # for x, y in [
            #     [1, 2],
            #     [2, 73],
            #     [3, 119],
            #     [4, 13],
            # ]:
            #     # add the simulated data, point by point, as usual
            #     yield from bps.mv(sim.x, x, sim.y, y)
            #     yield from write_stream(sim, "primary")

            # TODO: wait if previous workflow still executing
            logger.info(f"Start DM workflow: {workflow=}")
            yield from bps.mv(dm_workflow.concise_reporting, dm_concise)
            yield from dm_workflow.run_as_plan(
                workflow,
                # str(mda_file),
                wait=dm_wait,  # TODO:
                timeout=dm_timeout,
                # all kwargs after this line are DM argsDict content
                # filePath=filePath,
                filePath=str(mda_file),
                outputDataDir=str(XRF_PATH / "output"),
                # TODO: numFramesExpected=something,
                # time acq started
                # time acq ended
            )
            yield from write_stream([dm_workflow], "dm_workflow")
        logger.info("Bluesky plan m14_simulated_xrf() complete. %s", dm_workflow)

    yield from _inner()
