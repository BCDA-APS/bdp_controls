# bluesky metadata updated in DM

Build this into the M19_Cohere demo for 2023-12

Here's the demo/test from 2023-05-04:

```py
from dm import CatApiFactory
run = cat[-1]
experimentName = cat.name  # databroker catalog name
runId = f"uid_{run.metadata['start']['uid'][:8]}"  # first part of run uid
runInfo = dict(
    experimentName=experimentName,
    runId=runId,
    metadata={k: getattr(run, k).metadata for k in run}  # all streams
)
api = CatApiFactory.getRunCatApi()
md = api.addExperimentRun(runInfo)
# confirm
mdl = api.getExperimentRuns(experimentName)
```

and some names we used

```py
In [91]: print(f"{experimentName=}  {runId=}")
experimentName='1id_hexm'  runId='uid_f20c5c18' 
```
