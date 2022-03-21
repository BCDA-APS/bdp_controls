# README: instrument

The `instrument` package is the configuration used to make measurements using
bluesky.  It is structured and loaded as a [Python
*package*](https://www.pythontutorial.net/python-basics/python-packages/).  The
package includes setup of the [Bluesky framework](https://blueskyproject.io/)
including storage of the measured data, the hardware devices to be used, and the
measurement [*plans*](https://blueskyproject.io/bluesky/plans.html).

- [README: instrument](#readme-instrument)
  - [Operations](#operations)
  - [Devices](#devices)
    - [Hardware to support](#hardware-to-support)
    - [Devices As-implemented](#devices-as-implemented)
  - [Plans](#plans)
  - [Metadata](#metadata)


## Operations

1.  Activate the bpd2022``conda environment:

    ```bash
    (base) user@localhost $ conda activate bpd2022
    (bpd2022) user@localhost $
    ```

2.  Start an ipython console session:

    ```bash
    (bpd2022) user@localhost $ ipython
    ```

3.  Note the [instrument configuration file](instrument/configuration.yml).

4.  load the `instrument` package:

    ```py
    In [1]: from instrument.collection import *
    ```

5.  (optional) To make any error messages less verbose:

    ```py
    In [2]: %xmode Plain
    Exception reporting mode: Plain
    ```

    Note: This command is only available in the interactive shell and notebooks.
    It will not work (as `%xmode Plain`) in a function or from a file.

6.  To take an image (as bluesky a *run*):

    ```py
    In [3]: RE(take_image())


    Transient Scan ID: 15     Time: 2022-03-19 12:15:09
    Persistent Unique Scan ID: '6c3b1a6a-023a-49a2-b9fa-e16a6cee49f4'
    New stream: 'primary'
    +-----------+------------+
    |   seq_num |       time |
    +-----------+------------+
    |         1 | 12:15:09.8 |
    +-----------+------------+
    generator take_image ['6c3b1a6a'] (scan num: 15)
    Out[3]: ('6c3b1a6a-023a-49a2-b9fa-e16a6cee49f4',)
    ```

7.  (optional) View the most recent image in the ipython session:

    ```py
    In [3]: cat[-1].primary.read()["adsimdet_image"][0][0].plot.pcolormesh()
    ```

8.  Find the HDF5 image file (from most recent run) on local storage:

    ```py
    In [5]: cat[-1].primary._get_resources()
    Out[5]: 
    [{'spec': 'AD_HDF5',
    'root': '/',
    'resource_path': 'tmp/docker_ioc/iocad/tmp/adsimdet/2022/03/19/4652b419-a543-4131-9977_000.h5',
    'resource_kwargs': {'frame_per_point': 1},
    'path_semantics': 'posix',
    'uid': '03b05475-c70e-4bd1-bedd-95037c6048e7',
    'run_start': '6c3b1a6a-023a-49a2-b9fa-e16a6cee49f4'}]
    ```

    The HDF5 file is named:
    `/tmp/docker_ioc/iocad/tmp/adsimdet/2022/03/19/4652b419-a543-4131-9977_000.h5`

    It has this structure (default for area detector HDF5 file writer, using NeXus schema):

    ```bash
    In [6]: !h5dump -n /tmp/docker_ioc/iocad/tmp/adsimdet/2022/03/19/4652b419-a543-4131-9977_000.h5
    HDF5 "/tmp/docker_ioc/iocad/tmp/adsimdet/2022/03/19/4652b419-a543-4131-9977_000.h5" {
    FILE_CONTENTS {
    group      /
    group      /entry
    group      /entry/data
    dataset    /entry/data/data
    group      /entry/instrument
    group      /entry/instrument/NDAttributes
    dataset    /entry/instrument/NDAttributes/NDArrayEpicsTSSec
    dataset    /entry/instrument/NDAttributes/NDArrayEpicsTSnSec
    dataset    /entry/instrument/NDAttributes/NDArrayTimeStamp
    dataset    /entry/instrument/NDAttributes/NDArrayUniqueId
    group      /entry/instrument/detector
    group      /entry/instrument/detector/NDAttributes
    dataset    /entry/instrument/detector/NDAttributes/ColorMode
    dataset    /entry/instrument/detector/data -> /entry/data/data
    group      /entry/instrument/performance
    dataset    /entry/instrument/performance/timestamp
    }
    }
    ```

    The 3-D image is located in this file at HDF5 address: `/entry/data/data`

    The first dimension of the image is the frame number in the set.  Use `[0]`
    unless the area detector is configured differently.

## Devices

[*Devices*](https://blueskyproject.io/ophyd/reference/builtin-devices.html)
(in the Bluesky framework) describe the hardware (and software constructs such
as monochromator energy) to be used during measurements. The devices are defined
using [ophyd](https://blueskyproject.io/ophyd) structures.  Augmenting ophyd*,
additional structures from
[*apstools*](https://apstools.readthedocs.io/en/latest/api/index.html#api-documentation)
are used as appropriate.

### Hardware to support

Initially, it was planned to have these hardware features:

- shutter
- simulated beam intensity
  - include shutter in simulator
- ADSimDetector
  - simulated peak mode
  - randomized position and live jitter
  - include simulated beam intensity in simulator
  - use image, HDF5, and PVA plugins
- couple motors
- couple piezos (simulate with floating-point `ao` PVs)

A [configuration file](instrument/configuration.yml) is used to control
user-selectable features **on startup**.  The bluesky session must be restarted
to use any changes to the configuration file.

### Devices As-implemented

All of the planned hardware to be supported has been configured.  This table
from a bluesky console shows the current implementation.

```py
In [11]: listobjects()
============= ================================ ============ =============
name          ophyd structure                  EPICS PV     label(s)     
============= ================================ ============ =============
adsimdet      MySimDetector                    ad:          area_detector
aps           ApsMachineParametersDevice                                 
coarse_xy     XYstage_Coarse                                stage        
fine_xy       XYstage_Fine                                  stage        
gp_stats      IocInfoDevice                    gp:                       
incident_beam EpicsSignalRO                    gp:userCalc2 simulator    
shutter       SimulatedApsPssShutterWithStatus              shutters     
============= ================================ ============ =============
```

Details on any of these objects are available from the
[`listdevice()`](https://apstools.readthedocs.io/en/latest/api/_utils.html?highlight=listdevice#apstools.utils.device_info.listdevice)
command.  Example: `listdevice(aps, show_pv=True)` to see what is provided by
the `aps` object.

The `adsimdet` generates the images.  It is configured to simulate a single
*spot* (position, intensity, and width parameters are varied stocastically
using random number generators) within the image frame.  

FIXME: Note: The PVA plugin is not yet supported by the `adsimdet` construction.

The `aps` object provides up-to-date parameters about the APS storage ring.
Notably, `aps.current` is the storage ring current.  It's a good thing to record
as the run starts and ends (in the `baseline` stream).  In the [configuration
file](instrument/configuration.yml), change the `APS_IN_BASELINE` parameter to
`true` and restart the bluesky session.

The `shutter` is a simulator that affects the `adsimdet` image.  When the
shutter is closed, the `incident_beam` value will be set to zero and the area
detector image will be background only (maybe noisy, maybe not, depending on the
parameters in use).

The `coarse_xy` and `fine_xy` objects are simulators for hypothetical positions
to be investigated.  Their values are reported with the run's metadata.

The `gp_stats` object has metadata about an EPICS IOC providing the motor support.  It is not necessary but could be added to the run metadata if desired.

## Plans

These are the plans (measurement procedures) provided in
[`bpd_simulation.py`](instrument/plans/bpd_simulation.py):

plan | arguments | docstring
--- | --- | ---
close_shutter | () | Close the (simulated) shutter.
move_coarse_positioner | x, y | Move the coarse_xy positioner, only to new positions.
move_fine_positioner | x, y | Move the fine_xy positioner, only to new positions.
open_shutter | () | Open the (simulated) shutter.
take_image | coarse, fine | Take one image with the area detector.

## Metadata

* TODO:
