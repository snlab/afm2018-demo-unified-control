#!/bin/bash

# Python3.6 environment
source ~/App/venv3.6/bin/activate

# add the DDP module to PYTHONPATH or install DDP module
export PYTHONPATH="/home/yutao/Desktop/nccontainer"

mkdir -p log

ADDR=$1
OFPORT=$2
CONTROLLER=$3
LOG=$4
python3.6 -m nccontainer.switch.main -b $ADDR -p $OFPORT --forward $CONTROLLER -v > log/$LOG 2>&1
