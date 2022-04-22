#!/bin/bash

# usage:  source bash_epics_env_config.sh

# avoid this exception due to host using multiple network interfaces:
# CA.Client.Exception...............................................
#     Warning: "Identical process variable names on multiple servers"

LOCALHOST=127.0.0.1
S1_PV_GATEWAY_IP=164.54.112.168

export EPICS_CA_AUTO_ADDR_LIST=NO
export EPICS_CA_ADDR_LIST="${LOCALHOST} ${S1_PV_GATEWAY_IP}"
