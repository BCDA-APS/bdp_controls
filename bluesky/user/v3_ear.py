#!/usr/bin/env python

"""
Listen for (and print) PV monitors from an IOC.  Nothing else.
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

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
