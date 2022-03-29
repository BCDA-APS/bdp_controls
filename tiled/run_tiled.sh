#!/bin/bash

# manage the bluesky tiled server process in a screen session

#--------------------
# change the program defaults here
CONDA_ENVIRONMENT=tiled
DEFAULT_SESSION_NAME=tiled-server
TILED_HOST=192.168.144.97
TILED_PORT=8010
#--------------------

SHELL_SCRIPT_NAME=${BASH_SOURCE:-${0}}
if [ -z "$STARTUP_DIR" ] ; then
    # If no startup dir is specified, use the directory with this script
    STARTUP_DIR=$(dirname "${SHELL_SCRIPT_NAME}")
fi

TILED_CONFIG_FILE=${1:-${STARTUP_DIR}/config.yml}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# activate conda environment
CONDA_BASE_DIR=/opt/miniconda3/bin
source "${CONDA_BASE_DIR}/activate" "${CONDA_ENVIRONMENT}"

cd "${STARTUP_DIR}"
tiled serve config \
    --host "${TILED_HOST}" \
    --port "${TILED_PORT}" \
    "${TILED_CONFIG_FILE}"
