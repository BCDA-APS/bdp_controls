#!/usr/bin/env python

"""
IPC between data acquisition and data processing.
"""

import datetime

import pvaccess as pva
from bdp_handshake import HANDSHAKE_ACKNOWLEGED

PVA_PREFIX = "bdp:"
ACQUISITION_PV = f"{PVA_PREFIX}handshake"

ACTION_START_SERVER = "start PVA server"
ACTION_STOP_SERVER = "stop PVA server"
ACTION_COMPUTE_STATISTICS = "compute statistics"


def report(subject, message):
    print(f"{datetime.datetime.now()}: {subject}: {message}")
