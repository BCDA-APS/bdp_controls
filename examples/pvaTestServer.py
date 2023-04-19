#!/usr/bin/env python

"""
pvaTestServer.py

Example of a PVA server serving a single PVAccess PV.
This code was modified from the original:

* to separate the functional blocks
* apply consistent source code style (tools: isort, flake8, black)

:see: https://git.aps.anl.gov/C2/daq/apps/daq-aggregator/-/blob/master/daq_aggregator/pvaTestServer.py
"""

import random
import time

import pvaccess as pva


DEFAULT_CHANNEL = "PVA:TEST"


def new_PvObject():
    """
    Create a new PVA object.

    :see: https://epics.anl.gov/extensions/pvaPy/production/pvaccess.html
    """
    return pva.PvObject(
        # define the data types of _this_ PVA object
        dict(
            i=pva.INT,
            f=pva.FLOAT,
            da=[pva.DOUBLE],
            # ta=[pva.DOUBLE],  # unused below
            Time=[pva.DOUBLE],
            # customary, not required
            # timeStamp (or dateTimeStamp)
            timeStamp=dict(secondsPastEpoch=pva.UINT, nanoseconds=pva.UINT),
        )
    )


def getNewContent(i, deltaT, now, arraySize):
    """
    Return a new PVA object with the new content.

    Why not modify the public PV?
    To avoid multiple PVA update events,
    we'll write new content to a _local_ PVA object,
    then update the published PVA object all at once.
    """
    pv = new_PvObject()

    # generate some new content
    i += 1
    f = random.uniform(0, 1)
    ta = [now + j * deltaT for j in range(0, arraySize)]
    da = [f + j * deltaT for j in range(0, arraySize)]
    secondsPastEpoch = int(now)
    nanoseconds = int((now - secondsPastEpoch) * 1e9)

    # fill the local pv object with the new content
    pv["i"] = i
    pv["f"] = f
    pv["da"] = da
    # local_pv['ta'] = ta
    pv["Time"] = ta
    pv["timeStamp.secondsPastEpoch"] = secondsPastEpoch
    pv["timeStamp.nanoseconds"] = nanoseconds

    return pv


def test_server(channel=None, runtime=60, arraySize=16, updateFreq=1.0):
    """Run the PVA server demo."""
    channel = channel or DEFAULT_CHANNEL

    pv = new_PvObject()

    print(f"Starting PVA server on channel {channel} with object {pv}")
    s = pva.PvaServer(channel, pv)
    s.start()

    i = 0
    startTime = time.time()
    deltaT = 1.0 / updateFreq / arraySize
    deadline = startTime + runtime

    while time.time() < deadline:
        now = time.time()
        i += 1
        pv = getNewContent(i, deltaT, now, arraySize)

        print(pv["Time"] - startTime)
        print(f"Time: {now}\n{pv}")
        s.update(pv)  # publish the new content
        time.sleep(1 / updateFreq)

    print(f"Stopping PVA server on channel {channel}")
    s.stop()


def command_line_options():
    """Get the command line options."""
    import argparse

    parser = argparse.ArgumentParser(description="DAQ Test PVA Server.")

    parser.add_argument(
        "--channel",
        dest="channel",
        default=DEFAULT_CHANNEL,
        help="Server channel name.",
    )
    parser.add_argument(
        "--runtime",
        dest="runtime",
        type=float,
        default=60,
        help="Server runtime (default: 60.0 seconds).",
    )
    parser.add_argument(
        "--array-size",
        dest="arraySize",
        type=int,
        default=16,
        help="Array size (default: 16).",
    )
    parser.add_argument(
        "--update-freq",
        dest="updateFreq",
        type=float,
        default=1.0,
        help="Update frequency in Hz (default: 1.0).",
    )
    return parser.parse_args()


def main():
    args = command_line_options()
    test_server(args.channel, args.runtime, args.arraySize, args.updateFreq)


if __name__ == "__main__":
    main()
