#!/usr/bin/env python

"""
PVA server and client communicating a Python dict in JSON in a single PVAccess PV.

See the ``myExampleServer.py`` file for a custom server example.

USAGE::

    $ bdpPvaMetadata.py --help
    usage: bdpPvaMetadata.py [-h] [--channel CHANNEL] [--runtime RUNTIME] [--update-freq UPDATEFREQ] [--listener]

    PVA server and client communicating a Python dict in JSON in a single PVAccess PV.

    options:
    -h, --help            show this help message and exit
    --channel CHANNEL     Server channel name.
    --runtime RUNTIME     Server runtime (default: 60.0 seconds).
    --update-freq UPDATEFREQ
                            Update frequency in Hz (default: 1.0).
    --listener            Run a PVA listener client instead of a PVA server.
"""

import datetime
import json
# import cjson as json  # franzinc / python-cjson 1.1.0
import logging
import random
import time
import uuid

import pvaccess as pva


DEFAULT_CHANNEL = "PVA:TEST"
logger = logging.getLogger(__name__)


def dictionary_to_table(o):
    """
    Make a pyRestTable from a dictionary.

    Nested dictionaries are possible, where the value of some key
    can be a dictionary.
    """
    import pyRestTable

    if not isinstance(o, dict):
        return o

    table = pyRestTable.Table()
    table.labels = "key value".split()
    for k, v in sorted(o.items()):
        table.addRow((k, str(dictionary_to_table(v)).rstrip()))

    return table


class PvaMetadataClassError(RuntimeError):
    """General errors involving the PVA metadata class."""


class PvaListenerError(RuntimeError):
    """General errors involving the PVA listener."""


class PvaServerError(RuntimeError):
    """General errors involving the PVA server."""


class PvaMetadataClass:
    """Structure of the PVA object."""

    def newPvaObject(self):
        """
        Create a new PVA object.

        :see: https://epics.anl.gov/extensions/pvaPy/production/pvaccess.html
        """
        return pva.PvObject(
            # define the data types of _this_ PVA object
            dict(
                value=pva.STRING,  # Python dict as JSON
                index=pva.UINT,  # update number, starts 0
                uid=pva.STRING,  # uuid.uuid4
                # customary, not required
                # timeStamp (or dateTimeStamp)
                timeStamp=dict(secondsPastEpoch=pva.UINT, nanoseconds=pva.UINT),
            )
        )

    def marshall(self, content):
        return json.dumps(content, indent=2)

    def unmarshall(self, content):
        return json.loads(content)

    @property
    def pvname(self):
        return self._pvname

    @pvname.setter
    def pvname(self, value):
        if self.pvname is not None:
            raise PvaMetadataClassError("Cannot change pvname: {self.pvname}")
        self._pvname = value


class Server(PvaMetadataClass):
    _pvname = None
    pv = None
    counter = None
    server = None

    def __init__(self, pvname=None) -> None:
        self.pvname = pvname or DEFAULT_CHANNEL

    @property
    def running(self):
        return self.server is not None

    def start(self):
        if self.running:
            raise PvaServerError(f"PVA server already running: {self.server}")

        self.pv = self.newPvaObject()
        self.counter = 0

        print(f"Starting PVA server: {self.pvname}")  # TODO: remove for production
        logger.info("Starting PVA server: %s", self.pvname)
        self.server = pva.PvaServer(self.pvname, self.pv)
        self.server.start()

    def stop(self):
        if not self.running:
            raise PvaServerError("PVA server is not running.")

        self.server.stop()
        self.server = None
        self.pv = None

    def __repr__(self):
        return f"Server(pvname={self.pvname}, running={self.running})"

    def getValue(self):
        """
        Return Python dict with content to be published as JSON over PVA.

        This is the method to override in user-specific subclasses.
        """
        content = {"undefined": "Override getContent() method in a subclass of Server."}
        return content

    def publishContent(self, content=None):
        """
        Return a new PVA object with the new content.

        Why not modify the public PV?
        To avoid multiple PVA update events,
        we'll write new content to a _local_ PVA object,
        then update the published PVA object all at once.
        """
        if self.server is None:
            raise PvaServerError("PVA server is not running.")

        md_dict = content or {}

        # generate some new content
        payload = self.marshall(md_dict)

        self.counter += 1
        uid = uuid.uuid4()
        now = time.time()
        secondsPastEpoch = int(now)
        nanoseconds = int((now - secondsPastEpoch) * 1e9)

        logger.debug("new PVA content #%d, uid=%s", self.counter, uid)

        # fill the local pv object with the new content
        pv = self.newPvaObject()
        pv["value"] = payload
        pv["index"] = self.counter
        pv["uid"] = str(uid)
        pv["timeStamp.secondsPastEpoch"] = secondsPastEpoch
        pv["timeStamp.nanoseconds"] = nanoseconds

        self.server.update(pv)  # publish the new content


class Listener(PvaMetadataClass):
    _pvname = None
    channel = None

    def __init__(self, pvname=None) -> None:
        self.pvname = pvname or DEFAULT_CHANNEL

    @property
    def running(self):
        return self.channel is not None

    def start(self):
        if self.running:
            raise PvaListenerError(f"PVA Listener already running: {self}.")
        self.channel = pva.Channel(self.pvname)
        self.channel.subscribe("monitor", self.monitor)
        self.channel.startMonitor()

    def stop(self):
        if not self.running:
            raise PvaListenerError("PVA Listener is not running.")
        self.channel.unsubscribe("monitor")
        self.channel.stopMonitor()
        self.channel = None

    def __repr__(self):
        return f"Listener(pvname={self.pvname}, running={self.running})"

    def getDatetime(self, pv_object):
        key = "timeStamp"
        timestamp = pv_object[key]["secondsPastEpoch"]
        timestamp += pv_object[key]["nanoseconds"] * 1e-9
        return datetime.datetime.fromtimestamp(timestamp)

    def getValue(self, pv_object):
        return self.unmarshall(pv_object["value"])

    def getIndex(self, pv_object):
        return pv_object["index"]

    def getUid(self, pv_object):
        return pv_object["uid"]

    def monitor(self, pv_object):
        dt = self.getDatetime(pv_object)
        value = self.getValue(pv_object)
        _index = self.getIndex(pv_object)
        uid = self.getUid(pv_object)
        print(f"{dt}: #{_index}, {uid=}, {value=}")


class MyServer(Server):
    """
    Example of a user-defined subclass of Server.

    In the subclass, override (re-define) the getValue(),
    returning a Python dictionary with the content to be published.
    """

    def getValue(self):
        """
        Return Python dict with content to be published as JSON over PVA.

        This is the method to override in user-specific subclasses.

        This example returns a dictionary with a variety of data types. The
        dictionary keys are defined with no particular rules (other than valid
        dictionary keys).
        """
        value = round(random.uniform(0, 1), 2)
        content = {
            "random": value,
            "boolean": value > 0.5,  # True or False
            "text": str(value),
            "array": [value, 1 + value, 2 + value],
            "text_array": [str(value), str(1 + value), str(2 + value)],
            "mixed": dict(constants=[1, True, "string", "-1.2", 1.2]),
        }
        return content


class MyListener(Listener):
    """Example custom subclass of Listener."""
    user_function = None

    def monitor(self, pv_object):
        content = self.getValue(pv_object)  # This is the dict
        index_ = self.getIndex(pv_object)
        uid = self.getUid(pv_object)
        dt = self.getDatetime(pv_object)

        if self.user_function is not None:
            self.user_function(index_, uid, dt, content)


def run_server_demo(channel=None, runtime=60, updateFreq=1.0):
    """Run the PVA server demo."""
    channel = channel or DEFAULT_CHANNEL

    server = MyServer(channel)
    server.start()

    print(f"Starting PVA {server=} with {channel=}")

    startTime = time.time()
    deadline = startTime + runtime

    while time.time() < deadline:
        content = server.getValue()
        server.publishContent(content)
        print(f"{datetime.datetime.now()}: {content=}")
        time.sleep(1 / updateFreq)

    print(f"Stopping PVA server for: {server.pvname}")
    server.stop()


def example_listener_callback(index_, uid, dt, content):
    print(f"example_listener_callback({index_=}, {uid=}, {dt=}, {content=})")
    # print(dictionary_to_table(content))


def run_listener(pvname=None, runtime=60):
    pvname = pvname or DEFAULT_CHANNEL
    listener = MyListener(pvname)
    listener.user_function = example_listener_callback
    listener.start()
    print(f"Running PVA {listener=} for {runtime} s.")
    time.sleep(runtime)
    listener.stop()


def command_line_options():
    """Get the command line options."""
    import argparse

    help = __doc__.strip().splitlines()[0]
    parser = argparse.ArgumentParser(description=help)

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
        "--update-freq",
        dest="updateFreq",
        type=float,
        default=1.0,
        help="Update frequency in Hz (default: 1.0).",
    )
    parser.add_argument(
        "--listener",
        dest="listener",
        default=False,
        action="store_true",
        help="Run a PVA listener client instead of a PVA server.",
    )
    return parser.parse_args()


def main():
    args = command_line_options()
    if args.listener:
        run_listener(args.channel, args.runtime)
    else:
        run_server_demo(args.channel, args.runtime, args.updateFreq)


if __name__ == "__main__":
    main()
