#!/usr/bin/env python

"""
Retrieve the metadata for a bluesky run directly from databroker.

* Only uses databroker.
* Does not use the tiled.client API.
* Does not use tiled at all.

.. autosummary:
   ~get_bluesky_run_metadata
"""

from apstools.utils import listruns
import databroker
import logging
import json
import yaml


logger = logging.getLogger(__name__)
CATALOG = "training"
# CATALOG = "apstools_test"
# CATALOG = "usaxs_test"

DUMPERS = dict(
    json=json.dumps,
    yaml=yaml.dump,
)
DUMP = list(DUMPERS.keys())[0]
INDENT = 2


def get_bluesky_run_metadata(run):
    """
    Retrieve the metadata for a bluesky run directly from databroker.

    Includes the run metadata, the metadata for any streams, and for any resources.

    Parameters

    run *obj*:
        Instance of databroker.core.BlueskyRun
    """
    logger.debug(f"{type(run)=}")
    md = dict(run=run.metadata, streams={}, resources=[])

    # look at the (data) streams
    for stream_name in run:
        s_md = getattr(run, stream_name).metadata
        for redundant in "start stop".split():
            if (redundant in md["run"]) and (redundant in s_md):
                if md["run"][redundant] == s_md[redundant]:
                    del s_md[redundant]
        md["streams"][stream_name] = s_md
    
    # look for any (external file) resources
    for resource in run._get_resources():
        resource_uid = resource["uid"]
        resource["datum_pages"] = list(run._get_datum_pages(resource_uid))
        md["resources"].append(resource)

    return md


def main(catalog=CATALOG, refs=None, dumper=DUMP):
    logger.debug(f"{list(databroker.catalog)=}")
    # listruns(cat=cat)
    cat = databroker.catalog[catalog]
    logger.debug(f"{cat.name=}  {len(cat)=}")

    if refs is None:
        refs = cat  # _every_ run in the catalog
    elif isinstance(refs, (int, str)):
        refs = [refs]
    if isinstance(dumper, str):
        dumper = DUMPERS[dumper.lower()]

    for uid in refs:
        logger.debug(f"{uid=}")
        md = get_bluesky_run_metadata(cat[uid])
        print(dumper(md, indent=INDENT))


def get_command_line_options():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("catalog", action="store", help="databroker catalog name")
    parser.add_argument(
        "--uid",
        "-u",
        action="store",
        default=[],
        nargs="+",
        help="uid(s), full or shortened",
        type=str,
    )
    parser.add_argument(
        "--scan_id",
        "-s",
        action="store",
        default=[],
        nargs="+",
        help="scan id(s)",
        type=int,
    )
    parser.add_argument(
        "--format",
        "-f",
        action="store",
        default=list(DUMPERS.keys())[0],
        help=f"output type (one of these): {list(DUMPERS.keys())}",
        type=str,
    )

    return parser.parse_args()


if __name__ == "__main__":
    cl_opts = get_command_line_options()
    logger.debug(f"{cl_opts=}")

    refs = set(cl_opts.scan_id + cl_opts.uid)  # remove redundancies
    if refs == set():
        refs = None
    logger.debug(f"{refs=}")

    main(cl_opts.catalog, refs=refs, dumper=cl_opts.format)
