
# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Copyright (c) 2014 Susmit Shannigrahi, Steve DiBenedetto
#
# Author: Jeff Thompson <jefft0@remap.ucla.edu>
# Author Steve DiBenedetto <http://www.cs.colostate.edu/~dibenede>
# Author Susmit Shannigrahi <http://www.cs.colostate.edu/~susmit>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# A copy of the GNU General Public License is in the file COPYING.

import sys
import time
import argparse
import traceback
import random

from pyndn import Name
from pyndn import Data
from pyndn import Face
from pyndn.security import KeyChain


def dump(*list):
    """Prints all parameters"""

    result = ""
    for element in list:
        result += (element if type(element) is str else str(element)) + " "
    print(result)



class Producer():
    """Hosts data under a certain namespace"""
    def __init__(self):
        self.keyChain = KeyChain()
        self.keyChain.createIdentityV2(Name("/ndn/identity"))
        self.isDone = False


    def run(self, namespace):
        """Starts listening for interest packets in the given namespace"""
        # Create a connection to the local forwarder over a Unix socket
        face = Face("155.98.38.240")

        prefix = Name(namespace)

        # Use the system default key chain and certificate name to sign commands.
        face.setCommandSigningInfo(self.keyChain, self.keyChain.getDefaultCertificateName())

        # Also use the default certificate name to sign Data packets.
        face.registerPrefix(prefix, self.onInterest, self.onRegisterFailed)

        dump("Registering prefix", prefix.toUri())

        # Run the event loop forever. Use a short sleep to
        # prevent the Producer from using 100% of the CPU.
        while not self.isDone:
            face.processEvents()
            time.sleep(0.01)



    def onInterest(self, prefix, interest, transport, registeredPrefixId):
        """Called when an interest for the specified name is recieved"""
        interestName = interest.getName()

        data = Data(interestName)
        data.setContent("Hello, " + interestName.toUri())

        hourMilliseconds = 3600 * 1000
        data.getMetaInfo().setFreshnessPeriod(hourMilliseconds)

        self.keyChain.sign(data, self.keyChain.getDefaultCertificateName())

        transport.send(data.wireEncode().toBuffer())

        dump("Replied to:", interestName.toUri())


    def onRegisterFailed(self, prefix):
        """Called when forwarder can't register prefix"""
        dump("Register failed for prefix", prefix.toUri())
        self.isDone = True


def main():

    producer = Producer()

    # host data under a user-specified name prefix
    name_input = input("Enter a name to host content at: ")
    producer.run(name_input)


if __name__ == '__main__':
    main()
