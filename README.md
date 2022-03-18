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

### instrument configuration

- https://github.com/BCDA-APS/bluesky_training/tree/main/bluesky/instrument

### databroker catalog

catalog name: [`bdp2022`](/bdp2022_databroker.yml)

### plans

### bluesky-queueserver

(a stretch goal but will try this first)

- https://github.com/bluesky/bluesky-queueserver
- https://github.com/bluesky/bluesky-queueserver-api
- https://github.com/bluesky/bluesky-httpserver

### tiled data server

- https://github.com/bluesky/tiled
