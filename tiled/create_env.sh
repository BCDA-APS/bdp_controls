#!/bin/bash
#
# setup custom conda environment for tiled

export ENV_NAME=tiled

conda create -y \
    -n "${ENV_NAME}" \
    python=3.9 \
    httpie \
    ipython \
    matplotlib \
    pyresttable \
    spec2nexus \
    -c defaults -c conda-forge

conda activate "${ENV_NAME}"

pip install \
  event_model \
  pymongo

pip install --pre \
  databroker \
  tiled[all] \
  area_detector_handlers

