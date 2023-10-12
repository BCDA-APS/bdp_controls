#!/usr/bin/env python

"""
IPC between data acquisition and data processing.
"""

import datetime

PVA_PREFIX = "bdp:"
ACQUISITION_PV = f"{PVA_PREFIX}handshake"

ACTION_REQUEST_ACKNOWLEDGEMENT = "request acknowledgement"
ACTION_START_SERVER = "start PVA server"
ACTION_STOP_SERVER = "stop PVA server"
ACTION_COMPUTE_STATISTICS = "compute statistics"

CATALOG = "training"
TEST_RUNS = "897c4 b4216 589cc cfa4a".split()


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


class PutQueue:
    """
    Update the PVA from the main thread.

    EXAMPLES:

    Create instance in the main thread::

        putq = PutQueue(agent)

    Add communication task to the queue::

        putq.add({"comment": "example"}, a_key="more info", wait=False)

    Process (and empty) the queue periodically from the main thread::

        while time.time() < deadline:
            putq.process()
            time.sleep(sleep_period)
    """

    agent = None
    queue = []

    def __init__(self, agent):
        self.agent = agent

    def add(self, dictionary, wait=False, **kwargs):
        dictionary.update(**kwargs)
        self.queue.append(dict(wait=wait, dictionary=dictionary))

    def process(self):
        for task in list(self.queue):
            self.queue.remove(task)
            put_func = {
                True: self.agent.put_and_wait,
                False: self.agent.put,
            }[task["wait"]]
            put_func(task["dictionary"])
