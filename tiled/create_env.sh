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

# see PyMongo version dependency table
#  https://www.mongodb.com/docs/drivers/pymongo/#mongodb-compatibility
# APS has Mongod version 3.4.20, so pymongo<4 is the requirement from the table
pip install \
  event_model \
  "pymongo<4"

pip install --pre \
  databroker \
  tiled[all] \
  area_detector_handlers

