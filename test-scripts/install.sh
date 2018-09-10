#!/bin/bash
DIR=$(cd `dirname $0`; pwd)

source "$DIR/env.sh"
source "$VENV/bin/activate"

ROOT=$(dirname $DIR)


function help {
	echo "Usage: ";
	echo "	install.sh [ddp trident both]";
}

function ddp {
	cd $DIR; 
	cd ../ddp/napps; 
	kytos napps install snlab/DDP;
}

function trident {
	cd $DIR; 
	cd ../trident/napps; 
	kytos napps install snlab/trident_server;
}

if [ ! -n "$1" ]; then
	help;
	exit
fi

case "$1" in 
	ddp) ddp;;
	trident) trident;;
	both) ddp;trident;;
    *) help;;
esac