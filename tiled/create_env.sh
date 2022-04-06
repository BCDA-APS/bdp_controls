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
    tzlocal \
    Mako \
    MarkupSafe \
    aiofiles \
    alembic \
    anyio \
    appdirs \
    asgiref \
    blosc \
    cachetools \
    cachey \
    click \
    cloudpickle \
    dask \
    ecdsa \
    entrypoints \
    et-xmlfile \
    fastapi \
    fsspec \
    greenlet \
    h11 \
    h5netcdf \
    heapdict \
    httpcore \
    httptools \
    httpx \ \
    jinja2 \
    jmespath \
    locket \
    lz4 \
    msgpack \
    openpyxl \
    orjson \
    pandas \
    partd \
    prometheus-client \
    psutil \
    pyarrow \
    pyasn1 \
    pydantic \
    python-dotenv \
    python-jose \
    python-multipart \
    pytz \
    pyyaml \
    rfc3986 \
    rsa \
    sniffio \
    sqlalchemy \
    starlette \
    tifffile \
    toolz \
    typer \
    typing-extensions \
    uvicorn \
    uvloop \
    watchgod \
    websockets \
    xarray \
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

