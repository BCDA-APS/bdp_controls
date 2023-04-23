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


DEFAULT_CHANNEL = "BDP:Handshake"
logger = logging.getLogger(__name__)


class HandshakeBaseError(RuntimeError):
    """Errors from HandshakeBase."""


class HandshakeListenerError(RuntimeError):
    """Errors from HandshakeListener."""


class HandshakeServerError(RuntimeError):
    """Errors from HandshakeServer."""


class HandshakeBase:
    """Structure of the PVA object."""

    def newPvaObject(self):
        """
        Create a new PVA object.

        :see: https://epics.anl.gov/extensions/pvaPy/production/pvaccess.html
        """
        return pva.PvObject(
            # define the data types of _this_ PVA object
            dict(
                dictionary=pva.STRING,  # Python dict, see marshall & unmarshall
                index=pva.UINT,  # sequential update number, starts 0
                uid=pva.STRING,  # unique identifier (uuid.uuid4)
                timeStamp=dict(secondsPastEpoch=pva.UINT, nanoseconds=pva.UINT),
            )
        )

    def marshall(self, content):
        """Transform dictionary into a string."""
        return json.dumps(content, indent=2)

    def unmarshall(self, content):
        """Transform string back into a dictionary."""
        return json.loads(content)

    @property
    def running(self):
        """Redefine in both Server and Listener subclasses."""
        return False  # Cannot "run" the base class.

    @property
    def pvname(self):
        return self._pvname

    @pvname.setter
    def pvname(self, value):
        if self.running:
            raise HandshakeBaseError("Cannot change pvname: {self.pvname}")
        self._pvname = value


class HandshakeServer(HandshakeBase):
    """
    Run a PVA server for BDP handshakes.

    Override the ``getDictionary()`` method in a subclass to define the content
    of the dictionary to be published.  See the `MyServer` class below for an
    example.

    EXAMPLE::

        server = HandshakeServer("BDP:Handshake")
        server.start()
        #
        # repeat as required by application
        # ... publish new content ...
        server.publishDictionary(self.getDictionary())
        #
        server.stop()
    """

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
            raise HandshakeServerError(f"PVA server already running: {self.server}")

        self.pv = self.newPvaObject()
        self.counter = 0

        print(f"Starting PVA server: {self.pvname}")  # TODO: remove for production
        logger.info("Starting PVA server: %s", self.pvname)
        self.server = pva.PvaServer(self.pvname, self.pv)
        self.server.start()

    def stop(self):
        if not self.running:
            raise HandshakeServerError("PVA server is not running.")

        self.server.stop()
        self.server = None
        self.pv = None

    def __repr__(self):
        return (
            f"HandshakeServer(pvname={self.pvname}"
            f", running={self.running})"
        )

    def getDictionary(self):
        """
        Return Python dict with content to be published as JSON over PVA.

        NOTE: Override this the method in user-specific subclasses.
        """
        dictionary = {
            "undefined": "Override getDictionary() method in a subclass of Server."
        }
        return dictionary

    def publishDictionary(self, dictionary=None):
        """
        Publish the dictionary by PVA.

        Q: Why not modify the public PV?
        A: To avoid multiple PVA update events, we'll write new content to a
        _local_ PVA object, then update the _published_ PVA object all at once.
        """
        if self.server is None:
            raise HandshakeServerError("PVA server is not running.")

        self.counter += 1
        now = time.time()
        secondsPastEpoch = int(now)
        nanoseconds = int((now - secondsPastEpoch) * 1e9)

        # Write new content to a local PVA object.
        pv = self.newPvaObject()
        pv["dictionary"] = self.marshall(dictionary or {})
        pv["index"] = self.counter
        pv["uid"] = str(uuid.uuid4())
        pv["timeStamp.secondsPastEpoch"] = secondsPastEpoch
        pv["timeStamp.nanoseconds"] = nanoseconds

        logger.debug("new PVA content #%d, uid=%s", pv["index"], pv["uid"])

        # Publish the new content from the local PVA object.
        self.server.update(pv)


class HandshakeListener(HandshakeBase):
    """
    Run a PVA LIstener (client) for BDP handshakes.

    EXAMPLE:
    
    This simplistic example prints the dictionary as it is received by PVA.

        def example_listener_callback(index_, uid, dt, dictionary):
            "Called from PVA update event"
            print(
                "example_listener_callback("
                f"{index_=}"
                f", {dt=}"
                f", {uid=}"
                f", {dictionary=})"
            )

        listener = HandshakeListener("BDP:Handshake")
        listener.user_function = example_listener_callback
        listener.start()
        print(f"Running PVA {listener=} for {runtime} s.")
        # ... wait 20s for any PVA monitor events ...
        time.sleep(20)
        listener.stop()

    """

    _pvname = None
    channel = None
    user_function = None

    def __init__(self, pvname=None) -> None:
        self.pvname = pvname or DEFAULT_CHANNEL

    @property
    def running(self):
        return self.channel is not None

    def start(self):
        if self.running:
            raise HandshakeListenerError(f"PVA Listener already running: {self}.")
        self.channel = pva.Channel(self.pvname)
        self.channel.subscribe("monitor", self.monitor)
        self.channel.startMonitor()

    def stop(self):
        if not self.running:
            raise HandshakeListenerError("PVA Listener is not running.")
        self.channel.unsubscribe("monitor")
        self.channel.stopMonitor()
        self.channel = None

    def __repr__(self):
        return (
            "HandshakeListener("
            f"pvname={self.pvname}"
            f", running={self.running})"
        )

    def getDatetime(self, pv_object):
        """Return floating-point time from PVA object."""
        key = "timeStamp"
        timestamp = pv_object[key]["secondsPastEpoch"]
        timestamp += pv_object[key]["nanoseconds"] * 1e-9
        return datetime.datetime.fromtimestamp(timestamp)

    def getDictionary(self, pv_object):
        """Return the (unstructured) dictionary from the PVA object."""
        return self.unmarshall(pv_object["dictionary"])

    def getIndex(self, pv_object):
        """Return the sequential index number from the PVA object."""
        return pv_object["index"]

    def getUid(self, pv_object):
        """Return the unique identifier from the PVA object."""
        return pv_object["uid"]

    def monitor(self, pv_object):
        """Called when there is new PVA content."""
        dictionary = self.getDictionary(pv_object)
        index_ = self.getIndex(pv_object)
        uid = self.getUid(pv_object)
        dt = self.getDatetime(pv_object)
        logger.debug("%s: #{index_}, uid=%s, %s", dt, index_, uid, dictionary)

        if self.user_function is not None:
            self.user_function(index_, uid, dt, dictionary)


class MyServer(HandshakeServer):
    """
    Example of a user-defined subclass of Server.

    In the subclass, override (re-define) the getDictionary() method,
    returning a Python dictionary with the content to be published.
    """

    def getDictionary(self):
        """
        Return Python dict with content to be published as JSON over PVA.

        This is the method to override in user-specific subclasses.

        This example returns a dictionary with a variety of data types. The
        dictionary keys are defined with no particular rules (other than valid
        dictionary keys).
        """
        number = round(random.uniform(0, 1), 2)
        dictionary = {
            "random": number,
            "boolean": number > 0.5,  # True or False
            "text": str(number),
            "array": [number, 1 + number, 2 + number],
            "text_array": [str(number), str(1 + number), str(2 + number)],
            "mixed": dict(constants=[1, True, "string", "-1.2", 1.2]),
        }
        return dictionary


def run_server_demo(channel=None, runtime=60, updateFreq=1.0):
    """Run the PVA server demo."""
    channel = channel or DEFAULT_CHANNEL

    server = MyServer(channel)
    server.start()

    print(f"Starting PVA {server=} with {channel=}")

    startTime = time.time()
    deadline = startTime + runtime

    while time.time() < deadline:
        dictionary = server.getDictionary()
        server.publishDictionary(dictionary)
        print(f"{datetime.datetime.now()}: {dictionary=}")
        time.sleep(1 / updateFreq)

    print(f"Stopping PVA server for: {server.pvname}")
    server.stop()


def example_listener_callback(index_, uid, dt, dictionary):
    """Example: Called from PVA update event."""
    print(
        "example_listener_callback("
        f"#{index_}"
        f", {str(dt)}"
        f", uid={uid[:7]}"  # just the first 7 characters
        f", {dictionary=})"
    )


def run_listener(pvname=None, runtime=60):
    pvname = pvname or DEFAULT_CHANNEL
    listener = HandshakeListener(pvname)
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
