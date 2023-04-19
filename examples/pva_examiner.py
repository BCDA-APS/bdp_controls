#!/usr/bin/env python

"""
Monitor a PVA (or CA) process variable.

Print contents of each update.

PVA EXAMPLE::

    $ ./pva_examiner.py kad:Pva1:Image
    PVA monitor event: 'kad:Pva1:Image' at 2023-04-15 10:42:39.985581
    image.shape=(1024, 1024)  image.dtype=dtype('uint8')  image.min()=0  image.max()=255
    ================ ====== ============================================================
    key              length value
    ================ ====== ============================================================
    alarm            43     {'severity': 0, 'status': 0, 'message': ''}
    attribute        158    [{'name': 'ColorMode', 'value': ({'value': 0}, {'value': pva
    codec            87     {'name': '', 'parameters': ({'value': 5}, {'value': pvaccess
    compressedSize   7      1048576
    dataTimeStamp    72     {'secondsPastEpoch': 1681573359, 'nanoseconds': 985581040, '
    descriptor       0
    dimension        158    [{'size': 1024, 'offset': 0, 'fullSize': 1024, 'binning': 1,
    display          81     {'limitLow': 0.0, 'limitHigh': 0.0, 'description': '', 'form
    timeStamp        72     {'secondsPastEpoch': 1681573359, 'nanoseconds': 986649796, '
    uncompressedSize 7      1048576
    uniqueId         4      7622
    value            127    ({'ubyteValue': array([198, 199, 200, ..., 194, 195, 196], d
    ================ ====== ============================================================

    NDAttributes (metadata)
    ================ ======================================================================
    key              value
    ================ ======================================================================
    ColorMode        [{'value': 0}, {'value': pvaccess.pvaccess.ScalarType.INT}]
    codec            ========== ===========================================================
                    key        value
                    ========== ===========================================================
                    name
                    parameters ({'value': 5}, {'value': pvaccess.pvaccess.ScalarType.INT})
                    ========== ===========================================================
    uncompressedSize 1048576
    uniqueId         7622
    ================ ======================================================================

CA EXAMPLE::

    $ ./pva_examiner.py -ca gp:UPTIME
    CA monitor event: 'gp:UPTIME' at 2023-04-15 10:50:25.860167
    ========= ====== ============================================================
    key       length value
    ========= ====== ============================================================
    alarm     43     {'severity': 0, 'status': 0, 'message': ''}
    timeStamp 72     {'secondsPastEpoch': 1681573825, 'nanoseconds': 615652992, '
    value     8      20:29:44
    ========= ====== ============================================================

USAGE::

    $  ./pva_examiner.py -h
    usage: pva_examiner [-h] [-ca] pvname

    Monitor a PVA (or CA) process variable.

    positional arguments:
    pvname      EPICS PV name

    options:
    -h, --help  show this help message and exit
    -ca         use EPICS Channel Access (default: PV Access)

SUGGESTIONS

This code works with NTNDArrays.  The same approach works with any object. To
inspect structure of a particular channel, invoke ``getStructureDict()`` on the
received ``PvObject``.  For example, the _daq-aggregator_ (see
https://git.aps.anl.gov/C2/daq/apps/daq-aggregator) can monitor any number of
CA and/or PVA channels and create/serve aggregate PV Object.

Create IOCs (in Python) to serve PVs:

Example PVA IOC - simple test server for something other than AD images:
https://git.aps.anl.gov/C2/daq/apps/daq-aggregator/-/blob/master/daq_aggregator/pvaTestServer.py

Example CA IOC:
https://github.com/epics-base/pvaPy/blob/master/examples/caIocExample.py
"""

import datetime
import time

import pvaccess
import pyRestTable

PROTOCOL = None  # set below by command-line options or debug setup
PVNAME = None  # set below by command-line options or debug setup


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
    for k, v in sorted(pv_object.get().items()):
        row = [k, len(str(pv_object[k])), str(v)[:clip]]
        table.addRow(row)
    return table


def pva_to_image(pv_object):
    """Return the image from a PVA object.  Or ``None``."""
    if "dimension" in pv_object:
        shape = [axis["size"] for axis in pv_object["dimension"]]
        image = pv_object["value"][0]["ubyteValue"].reshape(*shape)
    else:
        image = None
    return image


def get_pva_ndattributes(pv_object):
    """Return a dict with the NDAttributes."""
    obj_dict = pv_object.get()
    attributes = {
        attr["name"]: [v for v in attr.get("value", "")]
        for attr in obj_dict.get("attribute", {})
    }
    for k in "codec uniqueId uncompressedSize".split():
        if k in pv_object:
            attributes[k] = pv_object[k]
    return attributes


def monitor(pv_object):
    """Receive PVA/CA monitor events."""
    # sdict = pv_object.getStructureDict()
    dt = datetime.datetime.now()
    for key in "dataTimeStamp timeStamp".split():
        if key in pv_object:
            # "PVA"
            timestamp = pv_object[key]["secondsPastEpoch"]
            timestamp += pv_object[key]["nanoseconds"] * 1e-9
            dt = datetime.datetime.fromtimestamp(timestamp)
            break
    print(f"{PROTOCOL} monitor event: '{PVNAME}' at {dt}")

    if PROTOCOL == "PVA":
        image = pva_to_image(pv_object)
        if image is not None:
            print(
                f"{image.shape=}"
                f"  {image.dtype=}"
                f"  {image.min()=}"
                f"  {image.max()=}"
            )

    print(pva_to_table(pv_object))

    metadata = get_pva_ndattributes(pv_object)
    if len(metadata) > 0:
        print("NDAttributes (metadata)")
        print(dictionary_to_table(metadata))


def endless(pvname, access):
    """Monitor PVNAME for updates.  Print tables.  Stop with ^C"""
    if access == "PVA":
        channel = pvaccess.Channel(pvname)
    else:
        channel = pvaccess.Channel(pvname, pvaccess.CA)
    channel.subscribe("monitor", monitor)
    channel.startMonitor()

    while True:
        time.sleep(1)

    channel.unsubscribe("monitor")


def once(pvname, access):
    """Print immediate values of PVA object.  Useful for debugging."""
    protocol = pvaccess.PVA if access == "PVA" else pvaccess.CA
    channel = pvaccess.Channel(pvname, protocol)

    # When there is a single subscriber, ``monitor()`` call can be
    # used to both subscribe and start monitoring the channel.  As in:
    # channel.subscribe("monitor", monitor)

    # BUT, we want to enable source-code debugging in this function and just
    # receive a single monitor event.
    # Otherwise the first monitor event will be first connection, which has
    # none of the PV values we want to report. These steps get that
    # connection event, _then_ start monitoring.
    channel.startMonitor()
    print(f"{channel.getName()=}  {channel.isConnected() = }")
    time.sleep(0.1)

    monitor(channel.get())
    channel.stopMonitor()


def get_command_line_options():
    import argparse

    doc = __doc__.strip().splitlines()[0]
    parser = argparse.ArgumentParser(prog="pva_examiner", description=doc)
    parser.add_argument("pvname", help="EPICS PV name")
    help_doc = "use EPICS Channel Access (default: PV Access)"
    parser.add_argument("-ca", action="store_true", help=help_doc)
    return parser.parse_args()


if __name__ == "__main__":
    # DEBUG = True
    DEBUG = False
    if DEBUG:
        PVNAME = "ad:Pva1:Image"
        PROTOCOL = "PVA"
        # PVNAME = "gp:UPTIME"
        # PROTOCOL = "CA"
        once(PVNAME, PROTOCOL)  # for development and source-code debugging
    else:
        cli = get_command_line_options()
        PVNAME = cli.pvname
        PROTOCOL = "CA" if cli.ca else "PVA"
        endless(PVNAME, PROTOCOL)  # production use
