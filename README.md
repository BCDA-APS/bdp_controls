# bdp_controls

APS-U Beam line Data Pipelines - experiment controls with EPICS and Bluesky

Copyright (c) 2022 - Advanced Photon Source,
[ANL Open Source License](/LICENSE.txt)

Provides

- [bdp_controls](#bdp_controls)
  - [EPICS softIoc for remote feedback](#epics-softioc-for-remote-feedback)
  - [Bluesky experiment control](#bluesky-experiment-control)
    - [instrument configuration](#instrument-configuration)
    - [databroker catalog](#databroker-catalog)
    - [plans](#plans)
    - [bluesky-queueserver](#bluesky-queueserver)
    - [tiled data server](#tiled-data-server)

## EPICS softIoc for remote feedback

- [README](/feedback/README.md)

## Bluesky experiment control

See the [bluesky-queueserver](#bluesky-queueserver) section below.

### instrument configuration

The instrument configuration is based on the [bluesky_training](https://github.com/BCDA-APS/bluesky_training/tree/main/bluesky/instrument) repository.
It is defined here in the `qserver/instrument` directory.

### databroker catalog

catalog name: [`bdp2022`](/bdp2022_databroker.yml)

### plans

See the plans listed as the queueserver environment is opened (which loads the instrument devices & plans and starts a RunEngine instance).

### bluesky-queueserver

See [README](/qserver/README.md)

- https://github.com/bluesky/bluesky-queueserver
- https://github.com/bluesky/bluesky-queueserver-api
- https://github.com/bluesky/bluesky-httpserver

### tiled data server

See the [README](/tiled/README.md) in the `tiled` section.

- https://github.com/bluesky/tiled

## Instructions to repeat last successful bluesky run

These commands in sequence in a terminal starting from an APS workstation with X11 running.

1. `ssh -X bdp@terrier`
2. `become_bluesky`
3. `cd ~/qserver/`
4. `queue-monitor &`
    1. ... the GUI starts in its own window
    2. click `Connect` in the Queue Server box on the `Monitor Queue` side tab
    3. click on the `Edit and Control Queue` side tab
    4. In the `HISTORY` table, find the last `completed` run and click it
    5. Above the table, click the `Copy to Queue` button
    6. New item should appear in the `QUEUE` table
    7. In the `Queue` section (near top of window), click `Start` button
    8. Watch things work...  Console output will indicate when things are done.
    9. Under `RE Manager Status`, all is done when `Manager state` is `IDLE`
5. `qserver-console-monitor`
    1. Leave this running in the terminal window.
       It shows any/all output from the bluesky queueserver.
