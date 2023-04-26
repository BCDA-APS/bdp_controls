#!/usr/bin/env python

import pathlib
import time

import pysumreg
from bdp_handshake import HandshakeListener
from handshake_common import (
    ACQUISITION_PV,
    ACTION_COMPUTE_STATISTICS,
    HANDSHAKE_ACKNOWLEGED,
    report,
)

HEADING = pathlib.Path(__file__).name


def analysis(xarr, yarr):
    sr = pysumreg.SummationRegisters()
    for x, y in zip(xarr, yarr):
        sr.add(x, y)
    return sr.to_dict()


def v2_data_analysis_as_client(duration=30):
    listener = HandshakeListener(ACQUISITION_PV)

    def pva_monitor(index_, uid, dt, dictionary):
        """Respond to PVA monitors."""
        report(f"{HEADING}.pva_monitor", f"#{index_} {dt} {uid[:7]}  {dictionary=}")

        # listener.put(dict(comment="test"))
        # print("after put()")

    #     if dictionary.get("action") == ACTION_COMPUTE_STATISTICS:
    #         message = dict(
    #             response=HANDSHAKE_ACKNOWLEGED,
    #             request=ACTION_COMPUTE_STATISTICS
    #         )
    #         print(f"acknowledging {uid[:7]}")
    #         listener.put(message)
    #         print(f"computing ... {message}")

    #         stats = analysis(dictionary["x"], dictionary["y"])
    #         listener.put(dict(data_uid=uid, stats=stats))
    #         print("responded with results")

    listener.user_function = pva_monitor
    listener.start()
    report(HEADING, listener)

    listener.put(dict(comment="ready"))

    deadline = time.time() + duration
    while time.time() < deadline:
        if listener.channel.isConnected():
            listener.put(dict(comment="waiting ..."))
        print("waiting ...")
        time.sleep(1.0)

    listener.stop()
    report(HEADING, listener)


def simpler(duration=30):
    from handshake_common import start_listener

    def pv_monitor(index_, uid, dt, dictionary):
        report(f"{HEADING}.pva_monitor", f"#{index_} {dt} {uid[:7]}  {dictionary=}")
        # print("before")
        # listener.put(dict(comment=f"{HEADING} pv_monitor()"))
        # print("after")

    listener = start_listener(HEADING, timeout=20)
    listener.user_function = pv_monitor

    listener.put(dict(role="client", heading=HEADING))

    time.sleep(duration)

    # listener = HandshakeListener(ACQUISITION_PV)
    # report(HEADING, listener)

    # def pva_monitor(*args, **kwargs):
    #     # listener.put(dict(comment="Hello, World!"))
    #     print(f"{args=}, {kwargs=}  {listener.channel.isConnected()=}")
    #     # if listener.channel.isConnected():
    #     #     listener.put(dict(comment=f"{HEADING} pvmonitor()"))

    # listener.user_function = pva_monitor
    # listener.start()
    # report(HEADING, listener)

    # # listener.put(dict(comment=f"{HEADING} ready"))

    # time.sleep(duration)

    # listener.stop()
    # report(HEADING, listener)


class Manager:
    listener = None
    results = None
    idle_period = 0.1

    def __init__(self, timeout=30):
        from handshake_common import start_listener

        self.listener = start_listener(HEADING, timeout=timeout)
        self.listener.user_function = self.pv_monitor

    def pv_monitor(self, index_, uid, dt, dictionary):
        """
        Called by a PVA monitor event.

        Cannot respond back in this method since it is a separate thread.
        Instead, queue results for reporting.
        """
        report(f"{HEADING}.pva_monitor", f"#{index_} {dt} {uid[:7]}  {dictionary=}")
        action = dictionary.get("action")
        if action is not None:
            self.results = dict(response=HANDSHAKE_ACKNOWLEGED, request=action)
            time.sleep(self.idle_period)

            if action == ACTION_COMPUTE_STATISTICS:
                self.results = dict(data_uid=uid, results="TODO")
                time.sleep(self.idle_period)

    def report_any_results(self):
        if self.results is not None:
            print("before")
            self.listener.put(self.results)
            print("after")
            self.results = None


def main(duration=20):
    # v2_data_analysis_as_client()
    # simpler()
    mgr = Manager()

    deadline = time.time() + duration
    while time.time() <= deadline:
        mgr.report_any_results()
        time.sleep(mgr.idle_period)


if __name__ == "__main__":
    report(HEADING, "started")
    main()
    report(HEADING, "finished")
