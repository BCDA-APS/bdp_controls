"""
Connect with APS Data Management workflows.

DM API: https://git.aps.anl.gov/DM/dm-docs/-/wikis/DM/Beamline-Services/API-Reference/DS-Service

Original code hoisted from: https://github.com/APS-1ID-MPE/hexm-bluesky/blob/main/instrument/devices/data_management.py
"""

__all__ = """
    DM_WorkflowConnector
    dm_workflow
""".split()

import logging
import os
import time

import pyRestTable
from apstools.utils import run_in_thread
from ophyd import Component, Device, Signal

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # allow any log content at this level
logger.info(__file__)
print(__file__)

DM_STATION_NAME = str(os.environ.get("DM_STATION_NAME", "terrier")).lower()
NOT_AVAILABLE = "-n/a-"
NOT_RUN_YET = "not_run"
POLLING_PERIOD_S = 1.0
REPORT_PERIOD_DEFAULT = 10
REPORT_PERIOD_MIN = 1
STARTING = "running"
TIMEOUT_DEFAULT = 180


class DM_WorkflowConnector(Device):
    """
    Support for the APS Data Management tools.

    The DM workflow dictionary of arguments (``workflow_args``)
    needs special attention.  Python's ``dict`` structure is not
    compatible with MongoDB.  In turn, ophyd does not support it.

    A custom plan can choose how to use `the `workflow_args`` dictionary:
        - use with DM workflow, as planned
        - add ``workflow_args`` to the start metadata
        - write as run stream::

            from apstools.devices import make_dict_device
            from apstools.plans import write_stream

            yield from write_stream(
                [make_dict_device(workflow_args, name="kwargs")],
                "workflow_args"
            )

    .. autosummary:

        ~_update_processing_data
        ~api
        ~ds_api
        ~proc_api
        ~getJob
        ~idle
        ~processing_jobs
        ~put_if_different
        ~report_processing_stages
        ~report_status
        ~run_as_plan
        ~start_workflow
        ~workflows
    """

    job = None  # DM processing job (must update during workflow execution)
    _ds_api = None  # DM data storage API
    _proc_api = None  # DM processing API

    owner = Component(Signal, value=DM_STATION_NAME, kind="config")
    workflow = Component(Signal, value="")
    workflow_args = {}

    job_id = Component(Signal, value=NOT_RUN_YET)

    # exit_status = Component(Signal, value=NOT_RUN_YET)
    run_time = Component(Signal, value=0)
    stage_id = Component(Signal, value=NOT_RUN_YET)
    status = Component(Signal, value=NOT_RUN_YET)

    polling_period = Component(Signal, value=POLLING_PERIOD_S, kind="config")
    reporting_period = Component(Signal, value=REPORT_PERIOD_DEFAULT, kind="config")
    concise_reporting = Component(Signal, value=True, kind="config")

    def __repr__(self):
        """Default representation of class instance."""
        # fmt: off
        innards = f"owner='{self.owner.get()}'"
        innards += f", workflow='{self.workflow.get()}'"
        for k, v in sorted(self.workflow_args.items()):
            innards += f", {k}={v!r}"
        # fmt: on
        if self.job_id.get() != NOT_RUN_YET:
            innards += f", id={self.job_id.get()!r}"
            rt = self.run_time.get()
            if rt > 0:
                innards += f", run_time={rt:.2f}"
            innards += f", stage_id={self.stage_id.get()!r}"
        innards += f", status={self.status.get()!r}"
        return f"{self.__class__.__name__}({innards})"

    def __init__(self, name=None, workflow=None, **kwargs):
        """Constructor."""
        if name is None:
            raise KeyError("Must provide value for 'name'.")
        super().__init__(name=name)
        if workflow is not None:
            self.workflow.put(workflow)
        self.workflow_args.update(kwargs)

    def put_if_different(self, signal, value):
        """Put ophyd signal only if new value is different."""
        if signal.get() != value:
            signal.put(value)

    def getJob(self, job_id=None):
        """Get the current processing job object."""
        job_id = job_id or self.job_id.get()
        return self.proc_api.getProcessingJobById(self.owner.get(), job_id)

    def _update_processing_data(self):
        """
        Called periodically (while process runs) to update self.job.

        Also updates certain ophyd signals.
        """
        if self.job_id.get() == NOT_RUN_YET:
            return
        # fmt: off
        # logger.debug("periodic update of job progress: %.3f", time.time())
        self.job = self.getJob()
        # fmt: on

        rep = self.job.getDictRep()
        # self.put_if_different(self.exit_status, rep.get("exitStatus", NOT_AVAILABLE))
        self.put_if_different(self.run_time, rep.get("runTime", -1))
        self.put_if_different(self.stage_id, rep.get("stage", NOT_AVAILABLE))
        self.put_if_different(self.status, rep.get("status", NOT_AVAILABLE))

    @property
    def ds_api(self):
        """Local copy of DM Data Storage API object."""
        from dm import DsApiFactory

        if self._ds_api is None:
            self._ds_api = DsApiFactory.getExperimentDsApi()
        return self._ds_api

    @property
    def proc_api(self):
        """Local copy of DM Processing API object."""
        from dm import ProcApiFactory

        if self._proc_api is None:
            self._proc_api = ProcApiFactory.getWorkflowProcApi()
        return self._proc_api

    api = proc_api  # backwards compatibility

    @property
    def idle(self):
        """Is DM Processing idle?"""
        return self.status.get() in (NOT_RUN_YET, "done", "failed", "aborted")

    def report_status(self, t_offset=None):
        """Status report."""
        if self.concise_reporting.get():
            t = f"{self.__class__.__name__} {self.name}:"
            t += f" {self.workflow.get()!r}"
            t += f" {self.job_id.get()[:8]!r}"
            t += f" {self.status.get()!r}"
            t += f" {self.stage_id.get()!r}"
            if t_offset is not None:
                t += f" elapsed: {time.time()-t_offset:.0f}s"

            logger.info(t)

        else:
            self.report_processing_stages()

    def start_workflow(self, workflow="", timeout=TIMEOUT_DEFAULT, **kwargs):
        """Kickoff a DM workflow with optional wait & timeout."""
        if workflow == "":
            workflow = self.workflow.get()
        else:
            workflow = workflow
        if workflow == "":
            raise AttributeError("Must define a workflow name.")
        self.put_if_different(self.workflow, workflow)

        wfargs = self.workflow_args.copy()
        wfargs.update(kwargs)
        logger.info(f"args {wfargs}")
        self.start_time = time.time()
        self._report_deadline = self.start_time

        def update_report_deadline(catch_up=False):
            period = max(self.reporting_period.get(), REPORT_PERIOD_MIN)
            if catch_up:  # catch-up (if needed) and set in near future
                new_deadline = round(self._report_deadline, 2)
                while time.time() > new_deadline:
                    new_deadline += period
            else:
                new_deadline = time.time() + period
            self._report_deadline = new_deadline

        def _reporter(*args, **kwargs):
            update_report_deadline(catch_up=False)
            self.report_status(t_offset=self.start_time)

        def _cleanup():
            """Call when DM workflow finishes."""
            self.stage_id.unsubscribe_all()
            self.status.unsubscribe_all()
            if "_report_deadline" in dir(self):
                del self._report_deadline

        @run_in_thread
        def _run_DM_workflow_thread():
            logger.info(
                "run DM workflow: %s with timeout=%s s", self.workflow.get(), timeout
            )
            logger.info(f"args: {wfargs}")
            self.job = self.proc_api.startProcessingJob(
                workflowOwner=self.owner.get(),
                workflowName=workflow,
                argsDict=wfargs,
            )
            self.job_id.put(self.job["id"])
            logger.info(f"DM workflow started: {self}")
            # wait for workflow to finish
            deadline = time.time() + timeout
            while time.time() < deadline and self.status.get() not in "done failed timeout aborted".split():
                self._update_processing_data()
                if "_report_deadline" not in dir(self) or time.time() >= self._report_deadline:
                    _reporter()
                time.sleep(self.polling_period.get())

            _cleanup()
            logger.info("Final workflow status: %s", self.status.get())
            if self.status.get() in "done failed".split():
                logger.info(f"{self}")
                self.report_status(self.start_time)
                return
            self.status.put("timeout")
            logger.info(f"{self}")
            # fmt: off
            logger.error(
                "Workflow %s timeout in %s s.", repr(self.workflow.get()), timeout
            )
            # raise TimeoutError(
            #     f"Workflow {self.workflow.get()!r}"
            #     f" did not finish in {timeout} s."
            # )
            # fmt: on

        self.job = None
        self.stage_id.put(NOT_RUN_YET)
        self.job_id.put(NOT_RUN_YET)
        self.status.put(STARTING)
        self.stage_id.subscribe(_reporter)
        self.status.subscribe(_reporter)
        _run_DM_workflow_thread()

    def run_as_plan(self, workflow="", wait=True, timeout=TIMEOUT_DEFAULT, **kwargs):
        """Run the DM workflow as a bluesky plan."""
        from bluesky import plan_stubs as bps

        if workflow == "":
            workflow = self.workflow.get()

        self.start_workflow(workflow=workflow, timeout=timeout, **kwargs)
        logger.info("plan: workflow started")
        if wait:
            while not self.idle:
                yield from bps.sleep(self.polling_period.get())

    @property
    def processing_jobs(self):
        """Return the list of processsing jobs."""
        return self.proc_api.listProcessingJobs(self.owner.get())

    @property
    def workflows(self):
        """Return the list of workflows."""
        return self.proc_api.listWorkflows(self.owner.get())

    def report_processing_stages(self, truncate=40):
        """
        Print a table about each stage of the workflow process.
        """
        if self.job is None:
            return

        wf = self.job["workflow"]
        stage_keys = "status runTime exitStatus stdOut stdErr".split()
        table = pyRestTable.Table()
        table.labels = "stage_id process processTime".split() + stage_keys
        for stage_id, dstage in wf["stages"].items():
            childProcesses = dstage.get("childProcesses", {"": {}})
            for k, v in childProcesses.items():
                row = [stage_id, k]

                status = v.get("status")
                if status is None:
                    processTime = 0
                else:
                    submitTime = v.get("submitTime", time.time())
                    endTime = v.get("endTime", submitTime)  # might be unknown
                    processTime = max(0, min(endTime - submitTime, 999999))
                row.append(round(processTime, 3))

                for key in stage_keys:
                    value = v.get(key, "")
                    if key in ("runTime"):
                        value = round(v.get(key, 0), 4)
                    if key in ("stdOut", "stdErr"):
                        value = str(value).strip()[:truncate]
                    row.append(value)
                table.addRow(row)
        logger.info(
            f"{wf['description']!r}"
            f" workflow={wf['name']!r}"
            f" id={self.job['id'][:8]!r}"
            f" elapsed={time.time()-self.start_time:.1f}s"
            f"\n{self!r}"
            f"\n{table}"
        )


dm_workflow = DM_WorkflowConnector(name="dm_workflow", labels=["DM"])
# RE(dm_workflow.run_as_plan(workflow="example-01", filePath="/home/beams/S1IDTEST/.bashrc"))
