#!/bin/bash
source ../test-scripts/env.sh
source $VENV/bin/activate
python3 ../nfs/fakeradius/client.py $1 $2