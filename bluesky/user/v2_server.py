#!/usr/bin/env python

import pathlib
import time

from bdp_handshake import HandshakeListener, HandshakeServer
from handshake_common import ACQUISITION_PV
from handshake_common import report

HEADING = pathlib.Path(__file__).name


def main():
    server = HandshakeServer(ACQUISITION_PV)
    server.start()
    server.put({}, comment="startup")
    report(HEADING, server)

    # monitor for updates to ACQUISITION_PV
    listener = HandshakeListener(ACQUISITION_PV)

    def pva_monitor(index_, uid, dt, dictionary):
        """Respond to PVA monitors."""
        report(f"{HEADING}.pva_monitor", f"#{index_} {dt} {uid[:7]}  {dictionary=}")

    listener.user_function = pva_monitor
    listener.start()
    report(HEADING, listener)

    # example activity
    for i in range(3):
        listener.put({"i": i}, comment="test")
        time.sleep(0.1)

    listener.stop()
    report(HEADING, listener)

    server.stop()
    report(HEADING, server)


if __name__ == "__main__":
    report(HEADING, "started")
    main()
    report(HEADING, "finished")
