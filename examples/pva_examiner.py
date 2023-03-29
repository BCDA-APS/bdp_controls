"""
Monitor a PVA process variable. Print contents of each update.
"""
import datetime
import time

import pvaccess
import pyRestTable

LISTEN_PVA = "ad:Pva1:Image"


def dictionary_to_table(o):
    """
    Make a pyRestTable from a dictionary.
    
    Nested dictionaries are possible, where the value of some key
    can be a dictionary.
    """
    if not isinstance(o, dict):
        return o

    table = pyRestTable.Table()
    table.labels = "key value".split()
    for k, v in sorted(o.items()):
        table.addRow((k, str(dictionary_to_table(v)).rstrip()))

    return table


def pva_to_table(pv_object, clip=60):
    """Make a pyRestTable from a PVA object."""
    table = pyRestTable.Table()
    table.labels = "key length value".split()
    for k in sorted(pv_object.keys()):
        v = pv_object[k]
        row = [k, len(str(pv_object[k])), str(v)[:clip]]
        table.addRow(row)
    return table


def pva_to_image(pv_object):
    """Return the image from a PVA object.  Or ``None``."""
    try:
        shape = [axis["size"] for axis in pv_object["dimension"]]
        image = pv_object["value"][0]["ubyteValue"].reshape(*shape)
    except KeyError:
        image = None
    return image


def get_pva_ndattributes(pv_object):
    """Return a dict with the NDAttributes."""
    attributes = {
        attr["name"]: [v for v in attr.get("value", "")]
        for attr in pv_object["attribute"]
    }
    for k in "codec uniqueId uncompressedSize".split():
        if k in pv_object:
            attributes[k] = pv_object[k]
    return attributes


def get_pva_timestamp(pv_object):
    """Reconstruct the timestamp of the PVA object."""
    timestamp = pv_object["dataTimeStamp"]["secondsPastEpoch"]
    timestamp += pv_object["dataTimeStamp"]["nanoseconds"] * 1e-9
    ts = datetime.datetime.fromtimestamp(timestamp)
    return ts


def monitor(pv_object):
    """Receive PVA monitor events."""
    ts = get_pva_timestamp(pv_object)
    print(f"PVA monitor event: '{LISTEN_PVA}' at {ts}")
    image = pva_to_image(pv_object)
    if image is not None:
        print(f"{image.shape=}  {image.dtype=}  {image.min()=}  {image.max()=}")
    print(pva_to_table(pv_object))
    metadata = get_pva_ndattributes(pv_object)
    print("NDAttributes (metadata)")
    print(dictionary_to_table(metadata))


def endless():
    """Monitor the PVA for updates.  Print tables."""
    channel = pvaccess.Channel(LISTEN_PVA)
    channel.subscribe("monitor", monitor)
    channel.startMonitor()

    while True:
        time.sleep(1)

    channel.unsubscribe("monitor")


def once():
    """Print immediate values of PVA object.  Useful for debugging."""
    channel = pvaccess.Channel(LISTEN_PVA)
    # channel.subscribe("monitor", monitor)
    channel.startMonitor()
    print(f"{channel.getName()=}  {channel.isConnected() = }")
    time.sleep(0.1)
    monitor(channel.get())
    channel.stopMonitor()


if __name__ == "__main__":
    once()  # for development and source-code debugging
    # endless()  # production use
