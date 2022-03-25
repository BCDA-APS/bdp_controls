# bluesky-queueserver

Follow the
[tutorial](https://blueskyproject.io/bluesky-queueserver/tutorial.html#running-re-manager-with-custom-startup-code)

Need these two files to start the server and load the instrument:

- `user_group_permissions.yaml` copied from the example
- `starter.py` loads the instrument (the **only** `.py` file in this directory)

- [bluesky-queueserver](#bluesky-queueserver)
  - [v2 Runtime Operations](#v2-runtime-operations)
    - [queueserver](#queueserver)
    - [tiled](#tiled)
    - [queueserver-monitor](#queueserver-monitor)
  - [v1 Runtime Operations](#v1-runtime-operations)
    - [qserver-console-monitor](#qserver-console-monitor)
    - [RunEngine session](#runengine-session)
    - [queue-server client](#queue-server-client)
      - [Example](#example)
  - [v0 Initial test of the server](#v0-initial-test-of-the-server)
    - [run server in a console](#run-server-in-a-console)
    - [Tell qserver to open an environment (in different console)](#tell-qserver-to-open-an-environment-in-different-console)
    - [New output in first console](#new-output-in-first-console)

## v2 Runtime Operations

Need three servers running.

### queueserver

Runs the bluesky `RunEngine` in a terminal (or background such as `screen`):

```bash
cd ./qserver
conda activate bluesky_2022_2
start-re-manager \
    --startup-dir ./  \
    --zmq-publish-console ON \
    --databroker-config bdp2022
```

### tiled

```bash
conda activate bluesky_2022_2
tiled serve config \
    --host "${HOST}" \
    --port "${PORT}" \
    --public \
    ./tiled-config.yml
```

Use web browser to visit `http://${HOST}:${PORT}/`

### queueserver-monitor

Install via `conda` or `pip`:
```
conda install -n bluesky_2022_2 -c defaults -c conda-forge bluesky-widgets
pip install bluesky-widgets
```

run the qserver:

```bash
conda activate bluesky_2022_2
queue-monitor &
```

Alternative, is to run from source:

```bash
git clone https://github.com/bluesky/bluesky-widgets
cd bluesky-widgets
python -m bluesky_widgets.apps.queue_monitor.main &
```

----

## v1 Runtime Operations

Need 3 terminal windows

### qserver-console-monitor

```bash
cd ./qserver
conda activate queue_server
qserver-console-monitor
```

- [docs](https://blueskyproject.io/bluesky-queueserver/cli_tools.html#qserver-console-monitor)

### RunEngine session

```bash
cd ./qserver
conda activate queue_server
start-re-manager \
    --startup-dir ./  \
    --zmq-publish-console ON \
    --databroker-config bdp2022
```

- [docs: pick databroker catalog](https://blueskyproject.io/bluesky-queueserver/cli_tools.html#instances-of-run-engine-and-databroker)
- [docs: publish console output?](https://blueskyproject.io/bluesky-queueserver/cli_tools.html#instances-of-run-engine-and-databroker)
- [docs: log verbosity](https://blueskyproject.io/bluesky-queueserver/cli_tools.html#other-configuration-parameters)

### queue-server client

This is where the user interacts with the queue-server.

```bash
cd ./qserver
conda activate queue_server

```

command | description
--- | ---
`qserver environment open` | Load devices & plans, connect databroker, start `RE`
`qserver environment close` | Stop `RE`
`qserver allowed devices` | Display the list of allowed devices. 
`qserver allowed plans` | Display the list of allowed plans. 
`qserver history clear` | Clear the (short-term) history. 
`qserver history get` | Show the (short-term) history. 
`qserver queue add instruction -2 queue-stop` | Stop the queue two items before the end of the queue (before position  `-2`.) 
`qserver queue add plan ${JSON_STRING}` | Add plan (json string) to the queue. 
`qserver queue clear` | Clear the queue. 
`qserver queue get` | Show the queue. 
`qserver queue start` | Start the queue. 
`qserver queue stop` | Stop the queue. 
`qserver status \| grep re_state` | `'idle'` when ready to run new jobs
`qserver status \| grep worker_environment_state` | `'idle'` when environment is open
`qserver status` | Status information from the qserver

- [docs: interacting with qserver](https://blueskyproject.io/bluesky-queueserver/tutorial.html#starting-the-queue-server)

#### Example

```bash
cd ./qserver
conda activate queue_server
qserver environment open
qserver status
qserver queue add plan '{"name": "take_image"}'
qserver status
qserver history clear
qserver queue clear
qserver queue add plan '{"name": "move_coarse_positioner", "args": [2.71, 3.14]}'
qserver queue add plan '{"name": "move_fine_positioner", "args": [.123, -0.456]}'
qserver queue add plan '{"name": "take_image", "kwargs": {"md": {"task": "use the qserver"}}}'
qserver queue add plan front '{"name": "set_acquire_time", "args": [0.5]}'
qserver status
qserver queue get
qserver queue start
```

Another example (add jobs while queue is running):

```bash
qserver queue clear
qserver queue add plan '{"name": "take_image", "kwargs": {"md": {"task": "use the qserver"}}}'
qserver queue add plan '{"name": "take_image", "args": [], "kwargs": {"md": {"task": "use the qserver"}}}'
qserver queue start
qserver queue add plan '{"name": "move_fine_positioner", "args": [0, 0]}'
qserver queue add plan '{"name": "move_coarse_positioner", "args": [0, 0]}'
```

----


## v0 Initial test of the server

Starting from a local repository clone (in the root directory of the clone):

### run server in a console

```bash
cd ./qserver
conda activate queue_server
start-re-manager --startup-dir ./
```

### Tell qserver to open an environment (in different console)

```bash
cd ./qserver
conda activate queue_server
qserver environment open
```

### New output in first console

Check for new output in the console where  `start-re-manager` is running.
