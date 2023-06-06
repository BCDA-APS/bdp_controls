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

from .. import iconfig
from ..devices import dm_workflow

SECOND = 1
MINUTE = 60 * SECOND

TITLE = "Simulate XRF data collection and processing"
VOYAGER = pathlib.Path().home() / "voyager"
XRF_DATA = VOYAGER / "BDP" / "XRF-demo"
DM_WORKFLOW_NAME = "does_not_exist"
DEFAULT_FLY_SCAN_TIME = MINUTE
DM_FILE_PATH = str(XRF_DATA)


def m14_simulated_xrf(
    image_dir=DM_FILE_PATH,
    dm_workflow=DM_WORKFLOW_NAME,
    fly_scan_time=DEFAULT_FLY_SCAN_TIME,
    dm_filePath=DM_FILE_PATH,
    dm_timeout=3 * MINUTE,
    dm_wait=True,
    dm_concise=True,
    md={},
):
    """
    Simulate XRF data collection and processing.

    See: https://github.com/APS-1ID-MPE/hexm-bluesky/blob/9fbe4efc2b6849a21dffd0c83f4b12bfb953fcdc/instrument/plans/bdp_plans.py#L31
    """
    # TODO: start DM workflow for each "line" of collected data (needs params)

    image_path = pathlib.Path(image_dir)
    _md = dict(
        title=TITLE,
        description=(
            "Simulate fly scan acquisition of a set"
            " of image files and start DM workflow."
        ),
        dm_workflow=dm_workflow,
        datetime=str(datetime.datetime.now()),
        data_management=dict(
            owner=dm_workflow.owner.get(),
            workflow=dm_workflow,
            filePath=dm_filePath,
            image_directory=image_dir,
            concise=dm_concise,
        ),
    )
    _md.update(md)

    logger.info(
        "In m14_simulated_xrf() plan."
        f"  {image_dir=}"
        f" (exists: {image_path.exists()})"
        f" {fly_scan_time=} s"
        f" {md=} s"
    )

    # TODO: "collect" data
    yield from bps.null()
