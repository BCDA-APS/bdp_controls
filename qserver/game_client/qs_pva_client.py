"""
Find centroid and width of central peak in image PV.

    python -m game_client.qs_pva_client

"""

from .analysis import analyze_image
from .examples import plan_dict
from .examples import print_plans_command_line
import datetime
import numpy as np
import pvaccess
import pyRestTable
import time

IMAGE_PV = "bdpad:Pva1:Image"
COST_GOAL = 0.5
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


def pva_to_image(pv):
    try:
        shape = [
            axis["size"]
            for axis in pv["dimension"]
        ]
        image = pv["value"][0]["ubyteValue"].reshape(*shape)
    except KeyError:
        image = None
    return image


def get_pva_ndattributes(pv):
    attributes = {
        attr["name"]: [v for v in attr.get("value", "")]
        for attr in pv["attribute"]
    }
    for k in  "codec uniqueId uncompressedSize".split():
        if k in pv:
            attributes[k] = pv[k]
    return attributes


def get_pva_timestamp(pv):
    timestamp = pv["dataTimeStamp"]["secondsPastEpoch"]
    timestamp += pv["dataTimeStamp"]["nanoseconds"] * 1e-9
    ts = datetime.datetime.fromtimestamp(timestamp)
    return ts


def monitor(pv):
    image = pva_to_image(pv)
    if image is None:
        return
    metadata = get_pva_ndattributes(pv)
    ts = get_pva_timestamp(pv)

    stats = analyze_image(image)
    centroid = [stats[k]['centroid_position'] for k in 'horizontal vertical'.split()]
    fwhm = [stats[k]['fwhm'] for k in 'horizontal vertical'.split()]

    fine = [
        metadata[f"samplexy_fine_{k}"][0].get("value", "")
        for k in 'x y'.split()
    ]
    target = np.array(image.shape)/2
    next_fine = target - np.array(centroid) + np.array(fine)
    cost = ((target - np.array(centroid)) / np.array(fwhm))**2
    results.append(
        dict(
            image_time=str(ts),
            image_timestamp=ts.timestamp(),
            uniqueId=pv['uniqueId'],
            stats=stats,
            cost=cost,
            cost_sum=cost.sum(),
            finexy=fine,
            next_finexy=next_fine,
        )
    )

    total_cost = np.sqrt(cost.sum())
    print(
        f"# {ts}"
        f" {metadata['uniqueId']}"
        f"  fine=({fine[0]:.2f}, {fine[1]:.2f})"
        f"  cost={total_cost}"
    )
    if total_cost < COST_GOAL:
        print("# !!! goal has been reached !!!")
    else:
        print_plans_command_line(
            [
                plan_dict("move_fine_positioner", next_fine[0], next_fine[1]),
                plan_dict("take_image", 0.01),
            ]
        )
        print("qserver queue start")


def runner():
    c = pvaccess.Channel(IMAGE_PV)
    c.subscribe("monitor", monitor)
    c.startMonitor()

    time.sleep(1)
    print("#"*40, "to restart simple simulation...")
    print("qserver history clear")
    print("qserver queue clear")
    print_plans_command_line(
        [
            plan_dict("prime_hdf_plugin"),
            plan_dict("move_fine_positioner", 0, 0),
            plan_dict("new_sample", 0, 1, 0),
            plan_dict("open_shutter"),
            plan_dict("take_image", 0.01),
        ]
    )
    print("qserver queue start")

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
