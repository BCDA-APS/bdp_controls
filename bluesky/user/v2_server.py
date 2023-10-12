#!/usr/bin/env python

import pathlib
import time

from bdp_handshake import HandshakeListener, HandshakeServer
from handshake_common import (
    ACQUISITION_PV,
    ACTION_COMPUTE_STATISTICS,
    ACTION_REQUEST_ACKNOWLEDGEMENT,
    report,
)

CATALOG = "training"
TEST_RUNS = "897c b4216 589cc".split()
HEADING = pathlib.Path(__file__).name


def v2_data_acquisition_as_server():
    import databroker

    server = HandshakeServer(ACQUISITION_PV)
    server.start()
    server.put({}, comment="startup")
    report(HEADING, server)

    # monitor for updates to ACQUISITION_PV
    listener = HandshakeListener(ACQUISITION_PV)

    def pva_monitor(index_, uid, dt, dictionary):
        """Respond to PVA monitors."""
        report(f"{HEADING}.pva_monitor", f"#{index_} {dt} {uid[:7]}  {dictionary=}")

    listener.user_function = pva_monitor
    listener.start()
    report(HEADING, listener)

    cat = databroker.catalog[CATALOG]
    print(f"{cat.name=}  {len(cat)=}")

    # example activity: list(range(-3, 0))
    # scans:
    for ref in "897c b4216 589cc".split():
        run = cat[ref]
        ds = run.primary.read()
        md = dict(
            action=ACTION_COMPUTE_STATISTICS,
            ref=ref,
            scan_id=run.metadata["start"]["scan_id"],
            plan_name=run.metadata["start"]["plan_name"],
            uid=run.name,
            # Not the best way to communicate data, but it's a start.  This data is small.
            x=ds["m1"].values.tolist(),
            y=ds["noisy"].values.tolist(),
        )
        try:
            listener.put_and_wait(md)
        except TimeoutError as exc:
            print(f"TimeoutError: {exc}")
        time.sleep(0.1)

    listener.stop()
    report(HEADING, listener)

    server.stop()
    report(HEADING, server)


def data_acquisition(listener):
    import databroker

    cat = databroker.catalog[CATALOG]
    print(f"{cat.name=}  {len(cat)=}")

    for ref in TEST_RUNS:
        run = cat[ref]
        ds = run.primary.read()
        md = dict(
            action=ACTION_COMPUTE_STATISTICS,
            ref=ref,
            scan_id=run.metadata["start"]["scan_id"],
            plan_name=run.metadata["start"]["plan_name"],
            uid=run.name,
        )
        print(f"{md=}")

        # Since this data is small, transmit it the easy way, in the dictionary.
        # It's not the best way to communicate data, but it's a start.  This
        # data is small.
        md["x"] = ds["m1"].values.tolist()
        md["y"] = ds["noisy"].values.tolist()

        listener.put_and_wait(md)


def simpler(duration=120):
    from handshake_common import start_listener, start_server

    def pv_monitor(index_, uid, dt, dictionary):
        report(f"{HEADING}.pva_monitor", f"#{index_} {dt} {uid[:7]}  {dictionary=}")
        # report(f"{HEADING}.pva_monitor", f"#{index_} {dt} {uid[:7]}")

    server = start_server(HEADING, timeout=2)
    listener = start_listener(HEADING, timeout=20)
    listener.user_function = pv_monitor
    # listener.wait_connection(timeout=2)

    listener.put_and_wait(
        dict(action=ACTION_REQUEST_ACKNOWLEDGEMENT),
        timeout=30,
        attempts=3,
    )
    print("after")

    listener.put(dict(comment="Starting 'data acquisition' ..."))

    data_acquisition(listener)  # send some bluesky data for analysis

    deadline = time.time() + duration
    while time.time() < deadline:
        time.sleep(5)
        listener.put(
            dict(
                comment=f"{HEADING} waiting...",
                remaining=round(deadline - time.time(), 1),
            )
        )


def main():
    # v2_data_acquisition_as_server()
    simpler()


if __name__ == "__main__":
    report(HEADING, "started")
    main()
    report(HEADING, "finished")
