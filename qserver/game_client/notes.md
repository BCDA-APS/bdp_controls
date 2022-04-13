# Game: center the image

Center an image with `instrument`, bluesky queueserver, and EPICS PVaccess.

In a console window:

```bash
conda activate bdp2022
cd ~/Documents/projects/BCDA-APS/bdp_controls/qserver
code -na ..  # open the VSCode editor
./qserver.sh checkup  # ensures the queueserver is running in screen session
qserver environment close  # shut it down (OK if not already running)
qserver environment open  # start the RunEngine process
queue-monitor &
qserver-console-monitor
```

## queue monitor GUI

1. Press `Connect` button.
2. Select `Edit and Control Queue` tab (on left side).
3. (optional) Press `Clear History` button.
4. Might need to *prime* the Area Detector HDF5 plugin.
   1. Select `Plan Editor` tab.
   2. Select `prime_hdf_plugin` from drop-down menu.
   3. Press `Add to Queue` button.
5. Press `Start` button (in *Queue* pane at screen top).
6. Watch the queue run in the console window or from the `Monitor Queue` tab.
7. If successful, plan will appear in the *HISTORY* pane.

### take an image

In the queue monitor GUI, queue and run these plans:

plan | parameter(s)
--- | ---
`open_shutter` |
`take_image` | `atime`: 0.01, `compression`: `zlib` (if available)

## PVA image viewer

In a console window:

```bash
conda activate c2dataviewer
c2dv --app image --pv bdpad:Pva1:Image &
```

1. Status should show `Connected`.
2. Click check box `Show image profiles (average calculation)`.
3. Press `Auto` button.
4. Press `Reset zoom` button.
5. Image and profiles should appear in main pane.

## Play the game : simple version

Goal: center the image by adjusting the fine positioners.

In the game setup plan, set the fine gain to 1.0 and the coarse gain to 0.0.
This will make the image position change by 1 pixel with every change of 1 in
the fine positioners (gain of 1.0).  The coarse positioners will be ignored
(gain of 0.0).

### run the PVA client

The PVA client computes the centroid & FWHM or each new image.  With the goal of
pushing the peak to the center of the image, a cost function is computed for the
current position.

In the VSCode editor, open the `game_client/qs_pva_client.py` and run it. (For
now, run in the debugger with breakpoint set on the `c.stopMonitor()` line.  This will create the monitor and provide advice for the human to use as feedback in the queue monitor.)

### start the game

In the queue monitor GUI, queue and run these plans to start the game:

plan | parameter(s)
--- | ---
`move_fine_positioner` | `x`: 0, `y`: 0
`game_configure` | `coarse_gain`: 0, `fine_gain`: 1, `noise`: 0
`take_image` | `atime`: 0.01, `compression`: `zlib` (if available)

Repeat these plans, supplying new values for the fine positioner, based on
minimizing the *cost* of each position.  Continue until acceptable criterion has
been reached (such as when `cost < 0.5`).

Hint: To re-run plan(s):

1. Select the plan(s) from the *HISTORY* pane.
2. Press the `Copy to Queue` button.
3. Double-click the `move_fine_positioner` plan in the `QUEUE` pane
4. Change the `x` & `y` values as desired.
5. Press the `Save` button.
6. Press the `Start` button.
