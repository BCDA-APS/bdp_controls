"""
Find centroid and width of central peak in image PV.

    python -m game_client.qs_pva_client

"""

from .analysis import analyze_image
import datetime
import numpy as np
import pvaccess
import pyRestTable
import time

IMAGE_PV = "bdpad:Pva1:Image"
results = []


def print_ndattribute_table(pv):
    table = pyRestTable.Table()
    table.labels = "name value descriptor sourceType source".split()
    for attr in pv["attribute"]:
        row = [attr[k] for k in table.labels]
        row[1] = row[1][0].get("value", "")
        table.addRow(row)
    print(table)


def print_pv_as_table(pv, clip=60):
    table = pyRestTable.Table()
    table.labels = "key length value".split()
    for k in pv.keys():
        table.addRow((k, len(str(pv[k])), str(pv[k])[:clip]))
    print(table)


def monitor(pv):

    shape = [
        axis["size"]
        for axis in pv["dimension"]
    ]
    image = pv["value"][0]["ubyteValue"].reshape(*shape)

    timestamp = pv["dataTimeStamp"]["secondsPastEpoch"]
    timestamp += pv["dataTimeStamp"]["nanoseconds"] * 1e-9
    ts = datetime.datetime.fromtimestamp(timestamp)

    attributes = {
        attr["name"]: [v for v in attr.get("value", "")]
        for attr in pv["attribute"]
    }
    fine = [
        attributes[f"samplexy_fine_{k}"][0].get("value", "")
        for k in 'x y'.split()
    ]

    stats = analyze_image(image)
    centroid = [stats[k]['centroid_position'] for k in 'horizontal vertical'.split()]
    fwhm = [stats[k]['fwhm'] for k in 'horizontal vertical'.split()]

    goal = np.array(shape)/2
    advise = goal - np.array(centroid) + np.array(fine)
    cost = ((goal - np.array(centroid)) / np.array(fwhm))**2
    results.append(
        dict(
            image_time=str(ts),
            image_timestamp=timestamp,
            uniqueId=pv['uniqueId'],
            stats=stats,
            cost=cost,
            cost_sum=cost.sum(),
            finexy=fine,
            next_finexy=advise,
        )
    )

    # print(f"{shape = }")
    # print(f"{image.shape = }")
    # print(f"{pv.keys() = }")
    # print(f"image timestamp = {datetime.datetime.fromtimestamp(timestamp)}")
    # print(pv["attribute"])
    # print(f"id={pv['uniqueId']}  {fine=}  {centroid=}  {fwhm=}")
    print(
        datetime.datetime.fromtimestamp(timestamp),
        pv['uniqueId'],
        " ",
        round(fine[0], 3),
        round(fine[1], 3),
        " ",
        round(centroid[0], 3),
        round(centroid[1], 3),
        " ",
        round(fwhm[0], 3),
        round(fwhm[1], 3),
        " ",
        cost.sum(),
        " ",
        round(advise[0], 3),
        round(advise[1], 3),
    )


def runner():
    c = pvaccess.Channel(IMAGE_PV)
    c.subscribe("monitor", monitor)
    c.startMonitor()
    while True:
        time.sleep(1)


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
    # main()
    runner()
