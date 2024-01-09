"""
Support for BDP demos.
"""

import datetime
import logging
import pathlib
import subprocess
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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


def get_workflow_last_stage(workflow_dir, wf_file=None):
    import ast

    if not WF_BASE.exists():
        raise FileNotFoundError(f"DM workflow directory {WF_BASE} not found.")

    # In some workflows, the Python code is named the same as the directory.
    # Other workflow directories might have more than one workflow.
    wf_file = wf_file or f"workflow-{workflow_dir}.py"
    path = WF_BASE / workflow_dir / wf_file
    if not path.exists():
        raise FileNotFoundError(f"DM workflow file {path} not found.")

    with open(path) as f:
        config = ast.literal_eval(f.read())
        stages = config.get("stages", {})
        if len(stages) > 0:
            return list(stages)[-1]


def run_blocking_function(function, *args, **kwargs):
    """Override from apstools."""
    from apstools.utils import run_in_thread
    POLL_DELAY = 0.000_05

    @run_in_thread
    def internal():
        logger.debug("...internal...")
        result = function(*args, **kwargs)
        logger.debug("%s(%s, %s) result=%s", function, args, kwargs, result)

    logger.debug(f"run_blocking_function(): function=%s  args=%s  kwargs=%s", function, args, kwargs)
    thread = internal()
    while thread.is_alive():
        yield from bps.sleep(POLL_DELAY)


def run_workflow_command(
    results, wf_dir, shell_command, *args, raises=False, env=None, **kwargs
):
    """Run a shell command as a bluesky plan."""
    from apstools.utils import run_in_thread

    if not isinstance(results, dict):
        raise TypeError("'results' must be a dictionary.")

    POLL_DELAY = 0.000_05

    script = WF_BASE / wf_dir / shell_command
    logger.debug("run_workflow_command(): path=%s", script)
    if not script.exists():
        raise FileNotFoundError(f"Workflow executable {script} not found.")

    @run_in_thread
    def threaded_process():
        command = f"{script} " + " ".join([a for a in args])
        logger.debug(f"run_workflow_command(): {command=}")

        process = subprocess.Popen(
            command,
            shell=True,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **kwargs,
        )

        stdout, stderr = process.communicate()
        results["stdout"] = stdout
        results["stderr"] = stderr

        if len(stderr) > 0:
            emsg = f"subprocess.Popen({command}) returned error:\n{stderr}"
            logger.error(emsg)
            if raises:
                raise RuntimeError(emsg)

        logger.debug(f"run_workflow_command(): {stdout=}")

    def as_plan():
        thread = threaded_process()
        while thread.is_alive():
            yield from bps.sleep(POLL_DELAY)

    logger.debug(f"run_workflow_command(): {script=}  {args=}  {kwargs=}")
    yield from as_plan()


def share_bluesky_metadata_with_dm(experimentName="", runId="", uid=None):
    """Once a bluesky run ends, share its metadata with APS DM."""
    import yaml
    from dm import CatApiFactory

    from ..qserver_framework import cat

    if len(experimentName.strip()) == 0:
        experimentName = cat.name  # databroker catalog name
    if len(runId.strip()) == 0:
        run = cat[uid or -1]
        runId = f"uid_{run.metadata['start']['uid'][:8]}"  # first part of run uid

    runInfo = dict(
        experimentName=experimentName,
        runId=runId,
        metadata={k: getattr(run, k).metadata for k in run},  # all streams
    )
    logger.info("Metadata shared to DM: %s", runInfo)

    # TODO: only upload if we have a workflow
    api = CatApiFactory.getRunCatApi()
    dm_md = api.addExperimentRun(runInfo)

    # confirm
    dm_mdl = api.getExperimentRuns(experimentName)
