#!/bin/bash

# this bash script installs the NDN python client library for python3

sudo apt-get install build-essential libssl-dev libffi-dev python3-dev python3-pip -y
sudo pip3 install pyndn

# copy the client code to the user's home directory
cp /local/repository/request_data.py ~/
