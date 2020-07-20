#!/bin/bash

# this bash script installs various NDN software on all routers

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

# copy a .vimrc (provides useful remappings)
cp /local/repository/.vimrc ~/
