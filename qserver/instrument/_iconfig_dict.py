"""
Provide information from the configuration.yml file.

Example YAML configuration file::

    # simple key:value pairs

    ADSIM_IOC_PREFIX: "bdpad:"
    GP_IOC_PREFIX: "bdp:"
    catalog: bdp2022
"""

__all__ = [
    "iconfig",
]

import logging
import pathlib
import yaml

logger = logging.getLogger(__name__)
logger.info(__file__)
print(__file__)


CONFIG_FILE = pathlib.Path(__file__).absolute().parent / "iconfig.yml"

if CONFIG_FILE.exists():
    iconfig = yaml.load(open(CONFIG_FILE, "r").read(), yaml.Loader)
else:
    raise FileNotFoundError(
        f"Could not find instrument configuration file: {CONFIG_FILE}"
    )

# os environment variable
iconfig["BDP_DEMO"] = pathlib.os.environ.get("BDP_DEMO", "")
iconfig["RUNENGINE_METADATA"]["milestone"] = f"BDP {iconfig['BDP_DEMO']} demo"
