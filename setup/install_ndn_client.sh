#!/bin/bash

# this bash script installs the NDN python client library for python3

sudo apt-get update
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev python3-pip -y

# Maintained version of pyndn currently does not have packet v0.3 support, so alternate version must be built
# sudo pip3 install pyndn
git clone https://github.com/Pesa/PyNDN2 ~/PyNDN2
cd ~/PyNDN2 && git merge remotes/origin/packet03
pip3 install ~/PyNDN2

# copy the client code to the user's home directory
cp /local/repository/request_data.py ~/
