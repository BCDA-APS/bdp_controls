#!/usr/bin/env python

"""
Acquisition: Demonstrate handshakes between acquisition and processing.
"""
import time
import uuid

import bdp_handshake
from handshake_common import *

HEADING = "...   "
ACK_RECEIVED = False


def publish(server, dictionary, **kwargs):
    dictionary.update(**kwargs)
    server.put(dictionary)
    report(">>>   ", f"{server=} published {dictionary=}")


def publishRequestAndWait(server, request, **kwargs):
    global ACK_RECEIVED

    ACK_RECEIVED = False
    publish(server, dict(action=request), **kwargs)
    wait_for_acknowledge()


def responder(index_, uid, dt, dictionary):
    """Respond to PVA monitors."""
    global ACK_RECEIVED

    report("<<<   ", f"#{index_} {dt} {uid[:7]}  {dictionary=}")
    if dictionary.get("response") == bdp_handshake.HANDSHAKE_ACKNOWLEGED:
        ACK_RECEIVED = True


def wait_for_acknowledge(timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ACK_RECEIVED:
            return
        time.sleep(0.1)
    raise TimeoutError("No acknowledgement in {timeout} s.")


def data_acquisition(agent):
    publishRequestAndWait(
        agent,
        ACTION_COMPUTE_STATISTICS,
        data=[
            [0, 0.000_1],
            [1, 1],
            [2, 2],
        ],
    )

    publishRequestAndWait(agent, ACTION_COMPUTE_STATISTICS, data="data_file.hdf5")

def main(duration=60):
    global ACK_RECEIVED

    server = bdp_handshake.HandshakeServer(ACQUISITION_PV)
    server.start()
    report(HEADING, f"{server=} started")

    # ask processing to create a PVA, random name
    processing_pv = f"{PVA_PREFIX}{str(uuid.uuid4())[:7]}"

    remote_ioc = bdp_handshake.HandshakeListener(processing_pv)
    remote_ioc.user_function = responder
    remote_ioc.start()
    report(HEADING, f"{remote_ioc=} started")

    publishRequestAndWait(server, ACTION_START_SERVER, pvname=processing_pv)
    data_acquisition(server)
    publishRequestAndWait(server, ACTION_STOP_SERVER)

    remote_ioc.stop()
    report(HEADING, f"{remote_ioc=} stopped")

    server.stop()
    report(HEADING, f"{server=} stopped")


if __name__ == "__main__":
    report(HEADING, f"{__file__=} started")
    main()
    report(HEADING, f"{__file__=} finished")
