#!/usr/bin/env python

"""
IPC between data acquisition and data processing.
"""

import datetime
import time
import uuid

import pvaccess as pva

PVA_PREFIX = "bdp:"
ACQUISITION_PV = f"{PVA_PREFIX}handshake"

ACTION_START_SERVER = "start PVA server"
ACTION_STOP_SERVER = "stop PVA server"
ACTION_COMPUTE_STATISTICS = "compute statistics"
# convention: client will acknowledge every ACTION
HANDSHAKE_ACKNOWLEGED = "acknowledged"

acknowledgment_received = False


def report(subject, message):
    print(f"{datetime.datetime.now()}: {subject}: {message}")


def put_and_wait(listener, dictionary, timeout=5, **kwargs):
    """
    Publish new dictionary content and wait for acknowledgment by client.

    EXAMPLE::

    def responder(index_, uid, dt, dictionary):
        '''Respond to PVA monitors.'''
        report("responder", f"#{index_} {dt} {uid[:7]}  {dictionary=}")
        if dictionary.get("response") == HANDSHAKE_ACKNOWLEGED:
            set_acknowledgment_received()
    """
    global acknowledgment_received

    acknowledgment_received = False

    # add the timeout value
    dictionary["timeout"] = timeout
    listener.put(dictionary, **kwargs)

    # wait for success or timeout
    # The ``acknowledgment_received`` object will be set by a pvmonitor process
    # which is a HANDSHAKE_ACKNOWLEGED message returned by the client.
    # TODO: retries (if not acknowledged)?
    deadline = time.time() + timeout
    while time.time() < deadline:
        if acknowledgment_received:
            return
        time.sleep(0.1)
    raise TimeoutError("No acknowledgement in {timeout} s.")


def set_acknowledgment_received(success=True):
    global acknowledgment_received

    acknowledgment_received = success
