#!/usr/bin/env python

"""
Run an IOC that provides the PV.

Only run the IOC (and print any PV monitor events received).
"""

import pathlib
import time

from handshake_common import start_server

CALLER = pathlib.Path(__file__).stem


def run_ioc():
    def pv_monitor(pv_object):
        print(f"{CALLER} {pv_object.toDict()=}")

    ioc = start_server(CALLER)
    ioc.channel.subscribe("IOC monitors", pv_monitor)
    ioc.channel.startMonitor()

    while True:
        time.sleep(1)


def main():
    run_ioc()


if __name__ == "__main__":
    main()
