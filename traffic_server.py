import time
import traceback
import random
import asyncio
from pyndn import Name
from pyndn import Data
from pyndn import Face
from pyndn.security import KeyChain
from pyndn.threadsafe_face import ThreadsafeFace


def dump(*list):
    """Prints all parameters"""

    result = ""
    for element in list:
        result += (element if type(element) is str else str(element)) + " "
    print(result)



class Producer():
    """Hosts data under a certain namespace"""

    def __init__(self):
        self._key_chain = KeyChain()
        #  self._keyChain.createIdentityV2(Name("/ndn/identity"))
        self._is_done = False
        self._num_interests = 0
        # the number of interests to satisfy before shutdown of server
        self._max_interests = 0


    def run(self, namespace, max_interests):
        """Starts listening for interest packets in the given namespace"""

        prefix = Name(namespace)
        self._max_interests = max_interests

        # host data at the local forwarder
        face = Face()

        # Use the system default key chain and certificate name to sign commands.
        face.setCommandSigningInfo(self._key_chain, self._key_chain.getDefaultCertificateName())

        # Also use the default certificate name to sign Data packets.
        face.registerPrefix(prefix, self.onInterest, self.onRegisterFailed)

        dump("Registering prefix", prefix.toUri())

        # Run the event loop forever. Use a short sleep to
        # prevent the Producer from using 100% of the CPU.
        while not self._is_done:
            face.processEvents()
            time.sleep(0.01)

        # shutdown face when done
        face.shutdown()



    def onInterest(self, prefix, interest, transport, registeredPrefixId):
        """Called when an interest for the specified name is recieved"""
        interestName = interest.getName()

        data = Data(interestName)
        data.setContent("Hello, " + interestName.toUri())

        hourMilliseconds = 3600 * 1000
        data.getMetaInfo().setFreshnessPeriod(hourMilliseconds)
        self._key_chain.sign(data, self._key_chain.getDefaultCertificateName())

        transport.send(data.wireEncode().toBuffer())

        dump("Replied to:", interestName.toUri())

        self._num_interests += 1

        # stop loop if the required number of interests have been satisified
        if self._num_interests >= self._max_interests:
            print(f"{self._num_interests} interests satisfied")
            self._is_done = True


    def onRegisterFailed(self, prefix):
        """Called when forwarder can't register prefix"""
        dump("Register failed for prefix", prefix.toUri())
        self._is_done = True


def main():

    producer = Producer()

    # host data under a user-specified name prefix
    name_input = input("Enter a name to host content at: ")
    producer.run(name_input, 10)
    

main()
