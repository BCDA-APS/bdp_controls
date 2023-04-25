#!/usr/bin/env python

import pathlib
import time
import uuid

from bdp_handshake import HandshakeServer
from bdp_handshake import HandshakeListener
from handshake_common import report
from handshake_common import HANDSHAKE_ACKNOWLEGED
from handshake_common import set_acknowledgment_received
from handshake_common import ACQUISITION_PV
import pvaccess as pva

HEADING = pathlib.Path(__file__).name


def pva_monitor(index_, uid, dt, dictionary):
    '''Respond to PVA monitors.'''
    report(f"{HEADING}.pva_monitor", f"#{index_} {dt} {uid[:7]}  {dictionary=}")
    if dictionary.get("response") == HANDSHAKE_ACKNOWLEGED:
        set_acknowledgment_received()


def main():
    server = HandshakeServer(ACQUISITION_PV)
    server.start()
    server.put({}, comment="startup")
    report(HEADING, server)

    # monitor for updates to ACQUISITION_PV
    listener = HandshakeListener(ACQUISITION_PV)
    listener.user_function = pva_monitor
    listener.start()
    report(HEADING, listener)

    for i in range(3):
        listener.put({"i": i}, comment="test")
    
    time.sleep(.2)

    listener.stop()
    report(HEADING, listener)

    server.stop()
    report(HEADING, server)


if __name__ == "__main__":
    report(HEADING, "started")
    main()
    report(HEADING, "finished")
