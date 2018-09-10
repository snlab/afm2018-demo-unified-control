#!/bin/bash
DIR=$(cd `dirname $0`; pwd)

source "$DIR/env.sh"
source "$VENV/bin/activate"

ROOT=$(dirname $DIR)

kytos napps list