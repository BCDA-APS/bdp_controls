# README: instrument

1.  Activate the conda environment and start ipython:

    ```bash
    conda activate bpd2022
    ipython
    ```

2.  load the `instrument` package:

    ```py
    from instrument.collection import 
    ```

3.  (optional) To make any error messages less verbose:

    ```py
    %xmode Plain
    ```

    Note: This command is only available in the interactive shell and notebooks.
    It will not work (as `%xmode Plain`) in a function or from a file.

4.  To take an image (as bluesky a *run*):

    ```py
    RE(take_image())
    ```

5.  (optional) View the most recent image in the ipython session:

    ```py
    cat[-1].primary.read()["adsimdet_image"][0][0].plot.pcolormesh()
    ```
