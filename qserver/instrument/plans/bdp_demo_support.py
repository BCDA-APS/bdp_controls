"""
Support for BDP demos.
"""

import datetime
import logging
import pathlib

logger = logging.getLogger(__name__)

logger.info(__file__)
print(__file__)

import pyRestTable
from bluesky import plan_stubs as bps

SECOND = 1.0
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY


DEFAULT_PERIOD = 10 * SECOND
DEFAULT_WAIT = False
WF_BASE = pathlib.Path.home() / "DM" / "workflows"
WORKFLOW_DONE_STATES = "done failed timeout aborted".split()


class WorkflowCache:
    """Keep track of one or more workflows for bluesky plans."""

    cache = {}

    def define_workflow(self, key, workflow):
        self.cache[key] = workflow

    def print_cache_summary(self, title="Summary"):
        """Summarize the DM workflow cache."""
        table = pyRestTable.Table()
        table.labels = "# process status runTime started id".split()
        for i, k in enumerate(self.cache, start=1):
            v = self.cache[k]
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

    def report_dm_workflow_output(self, final_stage_id):
        """Final (summary) report about DM workflow."""
        for wf in self.cache.values():
            job = wf.getJob()
            stage = job.getWorkflowStage(final_stage_id)  # example: "06-DONE"
            for process in stage.get("childProcesses", {}).values():
                for key in "stdOut stdErr".split():
                    value = str(process.get(key, "")).strip()
                    if len(value):
                        print(f"{final_stage_id}  {key}:\n{value}")
                        print("~" * 50)

    def _update_processing_data(self):
        for wf in self.cache.values():
            wf._update_processing_data()

    def wait_workflows(self, period=DEFAULT_PERIOD, wait=DEFAULT_WAIT):
        """(plan) Wait (if ``True``) for existing workflows to finish."""
        print(f"DEBUG: wait_workflows(): waiting={wait}")
        if wait:
            print(
                f"Waiting for all previous workflows ({len(self.cache)}) to finish..."
            )
            for workflow in self.cache.values():
                # wait for each workflow to end
                while workflow.status.get() not in WORKFLOW_DONE_STATES:
                    print(f"Waiting for {workflow=}")
                    yield from bps.sleep(period)


def build_run_metadata_dict(user_md, **dm_kwargs):
    """Return the run metadata dictionary."""
    _md = {
        "title": "title placeholder",
        "description": "description placeholder",
        "datetime": str(datetime.datetime.now()),
        "data_management": dm_kwargs,
    }
    _md.update(user_md)
    return _md


def data_measurement_plan(acquisition_time, *args):
    """Perform (or simulate) the data measurement."""
    logger.info("Simulated data collection for %s s.", acquisition_time)
    yield from bps.sleep(acquisition_time)
    print(f"Collected: {args=}")


def get_workflow_last_stage(workflow):
    import ast

    if not WF_BASE.exists():
        raise FileNotFoundError(f"DM workflow directory {WF_BASE} not found.")
    path = WF_BASE / workflow / f"workflow-{workflow}.py"
    if not path.exists():
        raise FileNotFoundError(f"DM workflow file {path} not found.")
    with open(path) as f:
        config = ast.literal_eval(f.read())
        stages = config.get("stages", {})
        if len(stages) > 0:
            return list(stages)[-1]
