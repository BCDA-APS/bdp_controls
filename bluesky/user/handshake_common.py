#!/usr/bin/env python

"""
IPC between data acquisition and data processing.
"""

import datetime

from bdp_handshake import HANDSHAKE_ACKNOWLEGED  # needed for v1 only

PVA_PREFIX = "bdp:"
ACQUISITION_PV = f"{PVA_PREFIX}handshake"

ACTION_REQUEST_ACKNOWLEDGEMENT = "request acknowledgement"
ACTION_START_SERVER = "start PVA server"
ACTION_STOP_SERVER = "stop PVA server"
ACTION_COMPUTE_STATISTICS = "compute statistics"


def report(subject, message):
    print(f"{datetime.datetime.now()}: {subject}: {message}")


def build_server(heading, timeout=10):
    from bdp_handshake import HandshakeServer

    agent = HandshakeServer(ACQUISITION_PV)
    agent.start()
    report(heading, agent)

    agent.put(dict(role="server", heading=heading, comment="startup"))
    yield agent

    agent.stop()
    report(heading, agent)


def build_listener(heading, callback=None, timeout=10):
    from bdp_handshake import HandshakeListener

    agent = HandshakeListener(ACQUISITION_PV)
    if callback is not None:
        agent.user_function = callback
    agent.start()
    agent.wait_connection(timeout=timeout)
    report(heading, agent)

    agent.put(dict(role="listener", heading=heading, comment="startup"))
    yield agent

    agent.stop()
    report(heading, agent)


def start_server(heading, timeout=10):
    return next(build_server(heading, timeout=10))


def start_listener(heading, callback=None, timeout=10):
    return next(build_listener(heading, timeout=10))
