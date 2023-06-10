"""
Setup for for this beam line's APS Data Management Python API client.
"""

import logging
import os
import pathlib

from . import iconfig

logger = logging.getLogger(__name__)

logger.info(__file__)

DM_SETUP_FILE = iconfig.get("DM_SETUP_FILE")
if DM_SETUP_FILE is not None:
    # parse environment variables from bash script
    ENV_VAR_FILE = pathlib.Path(DM_SETUP_FILE)
    logger.info("APS DM environment file: %s", str(ENV_VAR_FILE))
    ENV_VARS = {}
    for line in open(ENV_VAR_FILE).readlines():
        if not line.startswith("export "):
            continue
        k, v = line.strip().split()[-1].split("=")
        ENV_VARS[k] = v

    os.environ.update(ENV_VARS)
    BDP_WORKFLOW_OWNER = os.environ["DM_STATION_NAME"].lower()
    logger.info("APS DM workflow owner: %s", BDP_WORKFLOW_OWNER)
