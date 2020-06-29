#!/bin/bash

# this bash script installs various NDN software on router 1

# set up ppa repository
sudo apt-get install software-properties-common -y
sudo add-apt-repository ppa:named-data/ppa -y
sudo apt-get update

# install ndn software
sudo apt-get install nfd -y
sudo apt-get install ndn-tools -y
sudo apt-get install ndn-traffic-generator -y
sudo apt-get install nlsr -y
sudo apt-get install libchronosync -y
sudo apt-get install libpsync -y

# create a directory for nlsr config and logging
mkdir -p ~/nlsr/log/

# copy the appropriate nlsr configuration file to the nlsr directory
cp /local/repository/setup/external_dn.conf ~/nlsr/nlsr.conf

# copy the client code to the user's home directory
cp /local/repository/host_data.py ~/

# copy a .vimrc on each VM (provides useful remappings)
cp /local/repository/.vimrc ~/

