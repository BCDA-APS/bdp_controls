#!/usr/bin/env python

"""
Post new content to a PV (hosted elsewhere).
"""

import pathlib
import time

from handshake_common import start_listener

CALLER = pathlib.Path(__file__).stem

def main():
    agent = start_listener(CALLER)

    def pv_monitor(index_, uid, dt, dictionary):
        print(f"{CALLER} #{index_} {dt} {uid[:7]}  {dictionary=}")

    agent.user_function = pv_monitor

    for i in range(10):
        agent.put(dict(sequence=i, comment=f"{CALLER} test", _caller=CALLER))
        time.sleep(1)


if __name__ == "__main__":
    main()
