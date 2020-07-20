import time
import argparse
import traceback
import random
import asyncio
from pyndn import Name
from pyndn import Data
from pyndn import Face
from pyndn.security import KeyChain
from pyndn.threadsafe_face import ThreadsafeFace
import numpy as np
import pandas as pd


def dump(*list):
    """Prints all parameters"""

    result = ""
    for element in list:
        result += (element if type(element) is str else str(element)) + " "
    print(result)



class Producer():
    """Hosts data under a certain namespace"""

    def __init__(self, data_size, verbose=False):
        # create a KeyChain for signing data packets
        self._key_chain = KeyChain()
        self._is_done = False
        self._num_interests = 0
        #  self._keyChain.createIdentityV2(Name("/ndn/identity"))

        # the number of interests to satisfy before shutdown of server
        self._max_interests = 0

        # host data at the local forwarder
        self._face = Face()

        # immutable byte array to use as data
        self._byte_array = bytes(data_size)

        # the number of bytes contained in each data packet
        self._data_size = data_size

        # the verbosity of diagnostic information
        self._verbose = verbose

        # keep track of if the first interest has been recieved (for timing)
        self._is_first_interst = True

        # keep track of various performance metrics:
        self._interests_satisfied = 0
        self._interests_recieved = 0
        self._data_sent = 0
        self._elapsed_time = {}
        self._initial_time = {}
        self._final_time = {}

        print("Producer instance created.")


    def run(self, namespace, max_interests):
        """Starts listening for interest packets in the given namespace"""

        prefix = Name(namespace)
        self._max_interests = max_interests

        # Use the system default key chain and certificate name to sign commands.
        self._face.setCommandSigningInfo(self._key_chain, self._key_chain.getDefaultCertificateName())

        # Also use the default certificate name to sign Data packets.
        self._face.registerPrefix(prefix, self.onInterest, self.onRegisterFailed)

        dump("Registering prefix", prefix.toUri())

        print(f"Listening for interests under {namespace}...")
        print(f"Will satisfy {max_interests} before termination.")

        # Run the event loop forever. Use a short sleep to
        # prevent the Producer from using 100% of the CPU.
        while not self._is_done:
            self._face.processEvents()
            time.sleep(0.01)

        # shutdown this face - TODO: figure out why this can't be done in the self.shutdown() method
        self._face.shutdown()


    def onInterest(self, prefix, interest, transport, registeredPrefixId):
        """Called when an interest for the specified name is recieved"""

        # keep track of when first interest was recieved
        self._initial_time['download_time'] = time.time()

        # set data to a byte array of a specified size
        interestName = interest.getName()
        data = Data(interestName)
        data.setContent(self._byte_array)

        # sign and send data
        data.getMetaInfo().setFreshnessPeriod(3600 * 1000)
        self._key_chain.sign(data, self._key_chain.getDefaultCertificateName())
        transport.send(data.wireEncode().toBuffer())

        # print additional information if verobse flag is set
        if self._verbose:
            dump("Replied to:", interestName.toUri())

        # increment appropriate variables
        self._interests_recieved += 1
        self._interests_satisfied += 1
        self._num_interests += 1

        # stop loop if the required number of interests have been satisified
        if self._num_interests >= self._max_interests:
            self.shutdown()


    def onRegisterFailed(self, prefix):
        """Called when forwarder can't register prefix."""
        dump("Register failed for prefix", prefix.toUri())
        self.shutdown()


    def shutdown(self):
        self._final_time['download_time'] = time.time()
        self._is_done = True
        self.print_status_report()


    def print_status_report(self):
        """Prints performance metrics for this producer."""

        # compute total data sent (in bytes)
        self._data_sent = self._interests_satisfied * self._data_size

        # compute timing
        for key, value in self._initial_time.items():
            self._elapsed_time[key] = self._final_time[key] - self._initial_time[key]

        # calculate bitrate of interests sent
        download_kbps = ((self._data_sent * 8) / 1000) / self._elapsed_time['download_time']


        print("\n----------------------------------")
        print(f"Number of interests recieved: {self._interests_recieved}")
        print(f"Number of interests satisfied: {self._interests_satisfied}")
        print("----------------------------------")
        # this probably isn't a useful metric, as the output interface will drastically throttle this
        #  print(f"{self._data_sent / 1000} kilobytes sent for a bitrate of {download_kbps} kbps")
        print(f"{self._data_size * self._interests_satisfied} bytes of data sent.")
        print("----------------------------------\n")



def main():

    # handle and specify arguments
    parser = argparse.ArgumentParser()

    parser.add_argument("-p", "--prefix", help="the prefix to host data under", default="/ndn/external/test")
    parser.add_argument("-c", "--count", help="the number of interests to satisfy", type=int, default=10)
    parser.add_argument("-v", "--verbosity", help="increase output verbosity", action="store_true")
    parser.add_argument("-s", "--data_size", help="set the per-packet data size in bytes", type=int, default=1000)

    args = parser.parse_args()

    # host data under a user-specified name prefix
    producer = Producer(args.data_size, verbose=args.verbosity)
    producer.run(args.prefix, args.count)


main()
