#!/bin/bash

# Prepare environment and start ioc
DAQ_DIR=/clhome/BDP/DM/daq-support-rh7
source $DAQ_DIR/etc/setup.sh

# Start medm
daq-ad-pva-driver-medm &

