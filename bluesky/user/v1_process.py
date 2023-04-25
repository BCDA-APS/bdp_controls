#!/usr/bin/env python

"""
Processing: Demonstrate handshakes between acquisition and processing.
"""

import time

import bdp_handshake
import pysumreg
from handshake_common import *

HEADING = "   ..."


class Manager:
    enabled = False
    listener = None
    server = None
    pvname = None

    def __init__(self, pvname):
        self.enabled = True
        self.pvname = pvname
        self.listener = bdp_handshake.HandshakeListener(pvname)

    def analyze(self, data):
        if isinstance(data, str):
            return dict(
                error="NotImplementedError",
                reason=f"Data file handling not available: {data}",
            )
        sr = pysumreg.SummationRegisters()
        [sr.add(*xy) for xy in data]
        return dict(data=data, stats=sr.to_dict())

    def responder(self, index_, uid, dt, dictionary):
        report("   >>>", f"#{index_} {dt} {uid[:7]}  {dictionary=}")
        if dictionary.get("action") == ACTION_START_SERVER:
            self.startServer(dictionary["pvname"])  # this comes first
            self.acknowledge(ACTION_START_SERVER)

        elif dictionary.get("action") == ACTION_STOP_SERVER:
            self.acknowledge(ACTION_STOP_SERVER)
            self.enabled = False
            self.stopServer()

        elif dictionary.get("action") == ACTION_COMPUTE_STATISTICS:
            self.acknowledge(ACTION_COMPUTE_STATISTICS)
            message = dict(
                results=self.analyze(dictionary["data"]),
                data_uid=uid,
            )
            self.publish(message)

    def publish(self, dictionary):
        self.server.put(dictionary)
        report("   <<<", f"{self.server}: {dictionary=}")

    def acknowledge(self, action, **kwargs):
        message = dict(
            response=HANDSHAKE_ACKNOWLEGED,
            request=action,
        )
        message.update(**kwargs)
        self.publish(message)

    def start(self):
        self.listener.user_function = self.responder
        self.listener.start()

    def stop(self):
        self.listener.stop()
        self.listener = None

    def startServer(self, pvname):
        self.server = bdp_handshake.HandshakeServer(pvname)
        self.server.start()
        report(HEADING, f"{self.server} started")

    def stopServer(self):
        self.server.stop()
        report(HEADING, f"{self.server} stopped")
        self.server = None


def main(duration=20):
    mgr = Manager(ACQUISITION_PV)
    mgr.start()

    deadline = time.time() + duration
    while mgr.enabled and time.time() < deadline:
        time.sleep(0.1)
    mgr.stop()


if __name__ == "__main__":
    report(HEADING, f"{__file__=} started")
    main()
    report(HEADING, f"{__file__=} finished")
