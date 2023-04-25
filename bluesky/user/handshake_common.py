#!/usr/bin/env python

"""
Common: Demonstrate handshakes between acquisition and processing.
"""

import datetime

PVA_PREFIX = "bdp:"
ACQUISITION_PV = f"{PVA_PREFIX}handshake"

ACTION_START_SERVER = "start PVA server"
ACTION_STOP_SERVER = "stop PVA server"
ACTION_COMPUTE_STATISTICS = "compute statistics"
HANDSHAKE_ACKNOWLEGED = "acknowledged"


def report(subject, message):
    print(f"{datetime.datetime.now()}: {subject}: {message}")
