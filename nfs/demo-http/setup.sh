#!/bin/sh

apt-get update

apt-get -y install git apt-utils gcc wget unzip tar realpath
apt-get -y install curl libcurl4-openssl-dev

apt-get -y install python3 python3-pip

apt-get -y install tmux

pip3 install pycurl flask

WORKDIR=$(pwd)

# Install bro

BRO_DEB_PATH="http://download.opensuse.org/repositories/network:/bro/xUbuntu_14.04/"
BRO_APT_FILE="/etc/apt/sources.list.d/bro.list"

sh -c "echo \'deb $BRO_DEB_PATH /\' > $BRO_APT_FILE"

wget http://download.opensuse.org/repositories/network:bro/xUbuntu_14.04/Release.key
apt-key add — < Release.key
rm Release.key

apt-get update
apt-get -y install bro

# Install demo applications

git clone https://github.com/emiapwil/demo-http tutorial-sc16
make -C tutorial-sc16

export PATH="$PATH:$WORKDIR/tutorial-sc16/"

# Install bro script

git clone https://github.com/charlierproctor/bro_http

export PATH="$PATH:$WORKDIR/bro_http/"

# Install the controller
apt-get -y install software-properties-common debconf-utils

add-apt-repository ppa:webupd8team/java -y
echo "oracle-java8-installer shared/accepted-oracle-license-v1-1 select true" | debconf-set-selections

apt-get update
apt-get -y install oracle-java8-installer

git clone https://github.com/emiapwil/demo-bootstrap

export PATH="$PATH:$WORKDIR/demo-bootstrap"

setup-controller.sh

# Install the mininet script
