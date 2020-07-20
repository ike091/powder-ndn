#!/bin/bash

# this bash script installs the NDN python client library for python3

sudo apt-get update
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev python3-pip -y

# Maintained version of pyndn currently does not have packet v0.3 support, so alternate version must be built
# sudo pip3 install pyndn
git clone https://github.com/Pesa/PyNDN2 ~/PyNDN2
cd ~/PyNDN2 && git merge remotes/origin/packet03
pip3 install ~/PyNDN2

# install numpy and pandas for data analysis
cd ~/ && pip3 install numpy
cd ~/ && pip3 install pandas

# copy a .vimrc on each VM (provides useful remappings)
cp /local/repository/.vimrc ~/
