#!/bin/bash

# this bash script configures the external-dn router

# create a directory for nlsr config and logging
mkdir -p ~/nlsr/log/

# copy the appropriate nlsr configuration file to the nlsr directory
cp /local/repository/setup/external_dn.conf ~/nlsr/nlsr.conf
