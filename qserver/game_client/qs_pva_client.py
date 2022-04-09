"""
Find centroid and width of central peak in image PV.

- Monitor a PVA PV

In the PVA monitor handler:

- receive image data and attributes
- reshape the image
- compute centroid & fwhm
- log results:
    - image timestamp
    - uniqueId
    - fine xy
    - centroid
    - fwhm

TODO: steps with queueserver and monitor above

- communicate with qserver
- setup game
- open the shutter!
- set goal
- repeat until success or limited
    - load queue with plans
        - set fine xy
        - take image
        - print positioners
    - start queue
    - wait until queue finished
    - compute cost from results (from monitor)
    - set next target or terminate with success
    - report progress
"""

import datetime
import numpy as np
import pvaccess
import pyRestTable
import time
from scipy.ndimage.measurements import center_of_mass
from scipy.integrate import trapz

IMAGE_PV = "bdpad:Pva1:Image"
gpv = None


def analyze_peak(y_arr, x_arr=None):
    """Measures of peak center & width."""
    # clear all results
    center_position = None
    centroid_position = None
    maximum_position = None
    minimum_position = None
    crossings = None
    fwhm = None

    y = np.array(y_arr)
    num_points = len(y)
    if x_arr is None:
        x = np.arange(num_points)
    else:
        if len(x_arr) != num_points:
            raise ValueError("x and y arrays are not of the same length.")
        x = np.array(x_arr)

    # Compute x value at min and max of y
    y_max_index = y.argmax()
    y_min_index = y.argmin()
    maximum_position = (x[y_max_index], y[y_max_index])
    minimum_position = (x[y_min_index], y[y_min_index])

    (center_position,) = np.interp(center_of_mass(y), np.arange(num_points), x)

    # # for now, assume x is regularly spaced, otherwise, should be integrals
    # sumY = sum(y)
    # sumXY = sum(x*y)
    # sumXXY = sum(x*x*y)
    # # weighted_mean is same as center_position
    # # weighted_mean = sumXY / sumY
    # stdDev = np.sqrt((sumXXY / sumY) - (sumXY / sumY)**2)

    mid = (np.max(y) + np.min(y)) / 2
    crossings = np.where(np.diff((y > mid).astype(int)))[0]
    _cen_list = []
    for cr in crossings.ravel():
        _x = x[cr : cr + 2]
        _y = y[cr : cr + 2] - mid

        dx = np.diff(_x)[0]
        dy = np.diff(_y)[0]
        m = dy / dx
        _cen_list.append((-_y[0] / m) + _x[0])

    if _cen_list:
        centroid_position = np.mean(_cen_list)
        crossings = np.array(_cen_list)
        if len(_cen_list) >= 2:
            fwhm = np.abs(crossings[-1] - crossings[0], dtype=float)

    return dict(
        centroid_position=centroid_position,
        fwhm=fwhm,
        # half_max=mid,
        crossings=crossings,
        maximum=maximum_position,
        center_position=center_position,
        minimum=minimum_position,
        # stdDev=stdDev,
    )


def analyze_image(image):
    return dict(
        horizontal = analyze_peak(image.sum(axis=0)),
        vertical = analyze_peak(image.sum(axis=1)),
    )

    # table = pyRestTable.Table()
    # table.addLabel("measure")
    # table.addLabel("vertical (dim_1)")
    # table.addLabel("horizontal (dim_2)")
    # for key in horizontal.keys():
    #     table.addRow(
    #         (
    #             key,
    #             vertical[key],
    #             horizontal[key],
    #         )
    #     )

    # print(table)


def monitor(pv):
    global gpv

    shape = [
        axis["size"]
        for axis in pv["dimension"]
    ]
    image = pv["value"][0]["ubyteValue"].reshape(*shape)

    timestamp = pv["dataTimeStamp"]["secondsPastEpoch"]
    timestamp += pv["dataTimeStamp"]["nanoseconds"] * 1e-9

    attributes = {
        attr["name"]: [v for v in attr.get("value", "")]
        for attr in pv["attribute"]
    }
    fine = [
        attributes[f"samplexy_fine_{k}"][0].get("value", "")
        for k in 'x y'.split()
    ]

    # print(f"analysis timestamp = {datetime.datetime.now()}")
    # print(f"{dir(pv) = }")
    # print(f"uniqueId = {pv['uniqueId']}")
    # print(f"{pv['dimension'] = }")

    stats = analyze_image(image)
    centroid = [stats[k]['centroid_position'] for k in 'horizontal vertical'.split()]
    fwhm = [stats[k]['fwhm'] for k in 'horizontal vertical'.split()]

    goal = np.array(shape)/2
    advise = goal - np.array(centroid) + np.array(fine)
    cost = ((goal - np.array(centroid)) / np.array(fwhm))**2

    # print(f"{shape = }")
    # print(f"{image.shape = }")
    # print(f"{pv.keys() = }")
    # print(f"image timestamp = {datetime.datetime.fromtimestamp(timestamp)}")
    # print(pv["attribute"])
    # print(f"id={pv['uniqueId']}  {fine=}  {centroid=}  {fwhm=}")
    print(pv['uniqueId'], *fine, *centroid, *fwhm, cost.sum(), *advise)
    # gpv = pv

    # table = pyRestTable.Table()
    # table.labels = "key length value".split()
    # for k in pv.keys():
    #     table.addRow((k, len(str(pv[k])), str(pv[k])[:80]))
    #     # table.addRow((k, pv[k]))
    # # print(table)

    # table = pyRestTable.Table()
    # table.labels = "name value descriptor sourceType source".split()
    # for attr in pv["attribute"]:
    #     row = [attr[k] for k in table.labels]
    #     row[1] = row[1][0].get("value", "")
    #     table.addRow(row)
    # print(table)


def main():
    c = pvaccess.Channel(IMAGE_PV)
    c.subscribe("monitor", monitor)
    c.startMonitor()
    time.sleep(.1)
    # print(f"{c.isConnected() = }")
    # print(f"{c = }")
    # print(f"{dir(gpv) = }")
    c.stopMonitor()
    c.unsubscribe("monitor")


if __name__ == "__main__":
    main()
