#!/bin/bash

# this bash script configures the up-cl router

# create a directory for nlsr config and logging
mkdir -p ~/nlsr/log/

# copy the appropriate nlsr configuration file to the nlsr directory
cp /local/repository/setup/up_cl.conf ~/nlsr/nlsr.conf

# copy a .vimrc on each VM (provides useful remappings)
cp /local/repository/.vimrc ~/

