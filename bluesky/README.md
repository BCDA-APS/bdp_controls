# README: instrument

1.  Activate the conda environment and start ipython:

    ```bash
    conda activate bpd2022
    ipython
    ```

2.  Note the [instrument configuration file](instrument/configuration.yml).

3.  load the `instrument` package:

    ```py
    from instrument.collection import 
    ```

4.  (optional) To make any error messages less verbose:

    ```py
    %xmode Plain
    ```

    Note: This command is only available in the interactive shell and notebooks.
    It will not work (as `%xmode Plain`) in a function or from a file.

5.  To take an image (as bluesky a *run*):

    ```py
    RE(take_image())
    ```

6.  (optional) View the most recent image in the ipython session:

    ```py
    cat[-1].primary.read()["adsimdet_image"][0][0].plot.pcolormesh()
    ```

7.  Find the HDF5 image file (from most recent run) on local storage:

    ```py
    In [11]: cat[-1].primary._get_resources()
    Out[20]: 
    [{'spec': 'AD_HDF5',
    'root': '/',
    'resource_path': 'tmp/docker_ioc/iocad/tmp/adsimdet/2022/03/19/ba5b0a21-832f-4ecf-b178_000.h5',
    'resource_kwargs': {'frame_per_point': 1},
    'path_semantics': 'posix',
    'uid': '64311a08-fd4b-4963-a7f0-ebc04bfdab3c',
    'run_start': '35a8d7bd-f3eb-4ea4-bc12-997fad9ab1db'}]
    ```

    The HDF5 file is named:
    `/tmp/docker_ioc/iocad/tmp/adsimdet/2022/03/19/ba5b0a21-832f-4ecf-b178_000.h5`

    It has this structure (default for area detector HDF5 file writer, using NeXus schema):

    ```bash
    user@localhost ~ $ h5dump -n /tmp/docker_ioc/iocad/tmp/adsimdet/2022/03/19/ba5b0a21-832f-4ecf-b178_000.h5
    HDF5 "/tmp/docker_ioc/iocad/tmp/adsimdet/2022/03/19/ba5b0a21-832f-4ecf-b178_000.h5" {
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
