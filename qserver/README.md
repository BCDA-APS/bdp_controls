# bluesky-queueserver

Follow the
[tutorial](https://blueskyproject.io/bluesky-queueserver/tutorial.html#running-re-manager-with-custom-startup-code)

This directory needs these resources to start & run the queueserver:

file or directory | description
--- | ---
`instrument/` | the Python package with the devices and plans to be used
`starter.py` | loads the instrument (the **only** `.py` file in this directory)
`user_group_permissions.yaml` | copied from the `bluesky-queueserver` example

- [bluesky-queueserver](#bluesky-queueserver)
  - [Runtime Operations](#runtime-operations)
    - [graphical user interface](#graphical-user-interface)
    - [queueserver](#queueserver)
    - [tiled server](#tiled-server)
    - [queue-server client](#queue-server-client)
      - [Example](#example)

## Runtime Operations

Need one terminal and one graphical user interface.

Optionally, start another terminal for the *tiled* server (which needs a separate conda environment with development, non-production, versions of databroker and tiled).

### graphical user interface

```bash
cd ./qserver
conda activate bluesky_2022_2
queue-monitor &
```
- [docs](https://blueskyproject.io/bluesky-widgets/)

### queueserver

1. Start the bluesky queueserver.

    ```bash
    cd ./qserver
    conda activate bluesky_2022_2
    start-re-manager \
        --startup-dir ./  \
        --update-existing-plans-devices ENVIRONMENT_OPEN \
        --zmq-publish-console ON \
        --databroker-config bdp2022
    ```

2. Return to the queue-monitor started in the previous step.

   1. ***Connect*** with the queueserver process.  Wait for log
      (at bottom) to show `Returning the list of runs for the running plan ...`
   3. Select ***Edit and Control Queue*** from side tab bar.
   4. ***Open*** the environment.  Wait for RE Manager Status
      (at top right) to show: `RE Environment: OPEN`
   5. Select ***Plan Editor*** tab
   6. Build queue of plans using pop-up menu and complete form with plan's arguments.  For each new plan, edit and ***Add to queue***.
   7. Re-arrange order of plans in ***QUEUE*** windows as desired.
   8. ***Start*** processing the queue.

- [docs: pick databroker catalog](https://blueskyproject.io/bluesky-queueserver/cli_tools.html#instances-of-run-engine-and-databroker)
- [docs: publish console output?](https://blueskyproject.io/bluesky-queueserver/cli_tools.html#instances-of-run-engine-and-databroker)
- [docs: log verbosity](https://blueskyproject.io/bluesky-queueserver/cli_tools.html#other-configuration-parameters)

### tiled server

***tiled*** provides a data server to view acquired data.  Here, we only provide
instructions to *access* an APS tiled server providing catalog (`bdp2022`) for the BDP data:

In a web browser with access to the APS network, visit URL: http://wow.xray.aps.anl.gov:8010/bdp2022

Data from each measurement is presented by `uid` in chronolgocial order.  The
most recent is presented at the *end* of the list.  (Yes, the interface is quite
new and very focused yet on real user activities.)

Click on the uid of interest.  Usually, the data to view is found by proceeding
through this chain: *`uid`* -> *primary* -> *data* -> *adsimdet_image*

### queue-server client

- [docs: interacting with qserver](https://blueskyproject.io/bluesky-queueserver/tutorial.html#starting-the-queue-server)

This (optional step) is where the user interacts with the queue-server from a command-line.

```bash
cd ./qserver
conda activate bluesky_2022_2

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
qserver queue add plan '{"name": "take_image", "args": [.5], "kwargs": {"md": {"task": "demonstrate the qserver", "frame_type": "image"}}}'
qserver queue add plan front '{"name": "open_shutter"}'
qserver queue add plan front '{"name": "move_coarse_positioner", "args": [2.71, 3.14]}'
qserver queue add plan front '{"name": "move_fine_positioner", "args": [.123, -0.456]}'
qserver queue add plan '{"name": "close_shutter"}'
qserver queue add plan '{"name": "take_image", "args": [.5], "kwargs": {"md": {"task": "demonstrate the qserver", "frame_type": "dark"}}}'
qserver status
qserver queue get
qserver queue start
```

Another example (add jobs while queue is running):

```bash
qserver queue clear
qserver queue add plan '{"name": "take_image", "args": [.5], "kwargs": {"md": {"task": "use the qserver"}}}'
qserver queue start
qserver queue add plan '{"name": "move_fine_positioner", "args": [0, 0]}'
qserver queue add plan '{"name": "move_coarse_positioner", "args": [0, 0]}'
```
