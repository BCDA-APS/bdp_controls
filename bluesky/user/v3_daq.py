#!/usr/bin/env python

"""
Simulated data acquisition.
"""

import pathlib
import time

from handshake_common import ACTION_COMPUTE_STATISTICS
from handshake_common import CATALOG
from handshake_common import PutQueue
from handshake_common import start_listener
from handshake_common import TEST_RUNS

CALLER = pathlib.Path(__file__).stem


def main():
    agent = start_listener(CALLER)
    putq = PutQueue(agent)  # post PVA updates from main thread

    def pv_monitor(index_, uid, dt, dictionary):
        import pvaccess as pva
        print(f"{CALLER} #{index_} {dt} {uid[:7]}  {dictionary=}")
        action = dictionary.get("action")
        caller = dictionary.get("_caller")
        if action is not None:
            if caller != CALLER:
                message = dict(comment="should respond")
            else:
                message = dict(comment="should not respond")
            putq.add(message, wait=False, _caller=CALLER)

    agent.user_function = pv_monitor

    for ref in TEST_RUNS:
        # TODO: get run's data
        message = dict(reference=ref, action=ACTION_COMPUTE_STATISTICS)
        putq.add(message, wait=True, _caller=CALLER)
        putq.process()
        time.sleep(1)


if __name__ == "__main__":
    main()
