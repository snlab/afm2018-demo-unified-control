#!/bin/bash

# Python3.6 environment
source ~/afm-demo/kytosvenv/bin/activate

# add the DDP module to PYTHONPATH or install DDP module
export PYTHONPATH="/home/afm18/afm-demo/afm2018-demo-unified-control/ddp/lib"

mkdir -p log

ADDR=$1
OFPORT=$2
CONTROLLER=$3
python3.6 -m nccontainer.switch.main -b $ADDR -p $OFPORT --forward $CONTROLLER -v
