# test sequence

Model two separate Python processes:

process | description | Python file
--- | --- | ---
_ACQUIRE_ | data acquisition | `dev_acquire.py`
_PROCESS_ | data processing | `dev_process.py`

Each process will:

- start its own PVA server to post its requests and information
- listen for monitor events from the other PVA server

The process that hosts the pre-determined PV name: (`bdp:handshake`) will tell
the other what PV name to create.

## Start _acquire_ and _process_

Start _ACQUIRE_ and _PROCESS_ separately, in the background. Write output to the
same console.  Shows output in chronological sequence.

```text
17:04:29.178472: ...   : __file__='dev_acquire.py' started

Starting PVA server: bdp:handshake
17:04:29.227016: ...   : server=HandshakeServer(pvname=bdp:handshake, running=True) started
17:04:29.228064: ...   : listener=HandshakeListener(pvname=bdp:0b57be8, running=True) started
```

_ACQUIRE_ starts a PVA server with the pre-determined PV name (`bdp:handshake`).

## _ACQUIRE_ requests _PROCESS_ to start PVA server with given pvname

_ACQUIRE_ provides pvname for _PROCESS_ to start PVA server.  Pvname chosen with
common prefix (`bdp:`) and random suffix (first 7 characters of
`uuid.uuid4()`).  This pvname will change each time _ACQUIRE_ is started.

Once _PROCESS_ received the request (`action`), it started the server, **then**
acknowledged the request using its own PV.

```text
17:04:29.228224: >>>   : server=HandshakeServer(pvname=bdp:handshake, running=True) published dictionary={'action': 'start PVA server', 'pvname': 'bdp:0b57be8'}
17:04:29.232638:    ...: __file__='dev_process.py' started
17:04:29.282846:    >>>: #1 17:04:29.228098 a296b3c  dictionary={'action': 'start PVA server', 'pvname': 'bdp:0b57be8'}

Starting PVA server: bdp:0b57be8
17:04:29.283555:    ...: HandshakeServer(pvname=bdp:0b57be8, running=True) started
17:04:29.283682:    <<<: HandshakeServer(pvname=bdp:0b57be8, running=True): dictionary={'response': 'acknowledged', 'request': 'start PVA server'}
17:04:29.468614: <<<   : #1 17:04:29.283574 e984a4e  dictionary={'response': 'acknowledged', 'request': 'start PVA server'}
```

_ACQUIRE_ did not wait for _PROCESS_ to start.  It was written assuming that
_PROCESS_ will receive the `"start PVA server"` as it starts.  The assumption is
correct. _PROCESS_ acknowledged receiving the request.

## get statistics on XY data

Create a dataset of three ordered pairs $(x, y)$ and send it as part of the
dictionary.  This is not efficient and not likely common practice.  It is a
simple way to demonstrated the acquisition/processing workflow without adding
more software complexity.

```text
17:04:29.529375: >>>   : server=HandshakeServer(pvname=bdp:handshake, running=True) published dictionary={'action': 'compute statistics', 'data': [[0, 0.0001], [1, 1], [2, 2]]}
17:04:29.529824:    >>>: #2 17:04:29.528720 688da9c  dictionary={'action': 'compute statistics', 'data': [[0, 0.0001], [1, 1], [2, 2]]}
17:04:29.530301:    <<<: HandshakeServer(pvname=bdp:0b57be8, running=True): dictionary={'response': 'acknowledged', 'request': 'compute statistics'}
17:04:29.530660: <<<   : #2 17:04:29.529894 9983b19  dictionary={'response': 'acknowledged', 'request': 'compute statistics'}
```

_PROCESS_ uses `pysumreg.SummationRegisters()` from
[pysumreg](https://prjemian.github.io/pysumreg/1.0.3/index.html) to compute
summary statistics from the $(x, y)$ pairs.  The data is almost a perfect
straight line so $r$ (regression coefficient) should be very close to 1.0.  The
equation of fit should be close to $y=x+0$.

To coordinate the result with the request, the `uid` of the original data is returned with the results.

```text
17:04:29.531107:    <<<: HandshakeServer(pvname=bdp:0b57be8, running=True): dictionary={'results': {'data': [[0, 0.0001], [1, 1], [2, 2]], 'stats': {'mean_x': 1.0, 'mean_y': 1.0000333333333333, 'stddev_x': 1.0, 'stddev_y': 0.9999500004166876, 'slope': 0.9999500000000001, 'intercept': 8.333333333313912e-05, 'correlation': 0.9999999995832919, 'centroid': 1.6666111129629013, 'sigma': 0.4714948583831874, 'min_x': 1, 'max_x': 2, 'min_y': 0.0001, 'max_y': 2, 'x_at_max_y': 2, 'x_at_min_y': 0}}, 'data_uid': '688da9ce-d59c-4177-9d72-0206a3dbed01'}
17:04:29.531537: <<<   : #3 17:04:29.530511 11ae059  dictionary={'results': {'data': [[0, 0.0001], [1, 1], [2, 2]], 'stats': {'mean_x': 1.0, 'mean_y': 1.0000333333333333, 'stddev_x': 1.0, 'stddev_y': 0.9999500004166876, 'slope': 0.9999500000000001, 'intercept': 8.333333333313912e-05, 'correlation': 0.9999999995832919, 'centroid': 1.6666111129629013, 'sigma': 0.4714948583831874, 'min_x': 1, 'max_x': 2, 'min_y': 0.0001, 'max_y': 2, 'x_at_max_y': 2, 'x_at_min_y': 0}}, 'data_uid': '688da9ce-d59c-4177-9d72-0206a3dbed01'}
```

## process a data file

The code is not ready for this.  Still, return an informative message rather
than fail with an exception.

```text
17:04:29.630004: >>>   : server=HandshakeServer(pvname=bdp:handshake, running=True) published dictionary={'action': 'compute statistics', 'data': 'data_file.hdf5'}
17:04:29.630227:    >>>: #3 17:04:29.629787 f510c12  dictionary={'action': 'compute statistics', 'data': 'data_file.hdf5'}
17:04:29.630412:    <<<: HandshakeServer(pvname=bdp:0b57be8, running=True): dictionary={'response': 'acknowledged', 'request': 'compute statistics'}

17:04:29.630587:    <<<: HandshakeServer(pvname=bdp:0b57be8, running=True): dictionary={'results': {'error': 'NotImplementedError', 'reason': 'Data file handling not available: data_file.hdf5'}, 'data_uid': 'f510c122-9537-4742-99b1-65ea1d5ab59e'}
17:04:29.630600: <<<   : #4 17:04:29.630255 72a8944  dictionary={'response': 'acknowledged', 'request': 'compute statistics'}
17:04:29.630766: <<<   : #5 17:04:29.630437 c5d836e  dictionary={'results': {'error': 'NotImplementedError', 'reason': 'Data file handling not available: data_file.hdf5'}, 'data_uid': 'f510c122-9537-4742-99b1-65ea1d5ab59e'}
```

## _ACQUIRE_ tells _PROCESS_ to stop the server

```text
17:04:29.730817: >>>   : server=HandshakeServer(pvname=bdp:handshake, running=True) published dictionary={'action': 'stop PVA server'}
17:04:29.731258:    >>>: #4 17:04:29.730295 df9c5cb  dictionary={'action': 'stop PVA server'}
17:04:29.731743:    <<<: HandshakeServer(pvname=bdp:0b57be8, running=True): dictionary={'response': 'acknowledged', 'request': 'stop PVA server'}
17:04:29.732093: <<<   : #6 17:04:29.731331 946a3bd  dictionary={'response': 'acknowledged', 'request': 'stop PVA server'}
17:04:29.733871:    ...: HandshakeServer(pvname=bdp:0b57be8, running=False) stopped
```

## final steps to exit

```text
17:04:29.784814:    ...: __file__='dev_process.py' finished
17:04:29.832244: ...   : listener=HandshakeListener(pvname=bdp:0b57be8, running=False) stopped
17:04:29.832882: ...   : server=HandshakeServer(pvname=bdp:handshake, running=False) stopped
17:04:29.832908: ...   : __file__='dev_acquire.py' finished
```
