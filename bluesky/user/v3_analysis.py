#!/usr/bin/env python

"""
Listen for (and print) PV monitors from an IOC.  Nothing else.
"""

import pathlib
import time

from handshake_common import ACTION_REQUEST_ACKNOWLEDGEMENT
from handshake_common import PutQueue
from handshake_common import start_listener

CALLER = pathlib.Path(__file__).stem

def main():
    agent = start_listener(CALLER)
    putq = PutQueue(agent)  # post PVA updates from main thread

    def pv_monitor(index_, uid, dt, dictionary):
        print(f"{CALLER} #{index_} {dt} {uid[:7]}  {dictionary=}")
        action = dictionary.get("action")
        caller = dictionary.get("_caller")
        if action is not None and caller is not CALLER:
            # TODO: analysis
            message = dict(
                request=action,
                response=ACTION_REQUEST_ACKNOWLEDGEMENT,
                _caller=CALLER,
            )
            putq.add(message, wait=False)

    agent.user_function = pv_monitor

    while True:
        putq.process()
        time.sleep(0.1)


if __name__ == "__main__":
    main()
