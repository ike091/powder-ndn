import time
import asyncio
from pyndn import Name
from pyndn import Interest
from pyndn.transport import UdpTransport
from pyndn.security import KeyChain
from pyndn.threadsafe_face import ThreadsafeFace


def dump(*list):
    """Prints all parameters"""

    result = ""
    for element in list:
        result += (element if type(element) is str else str(element)) + " "
    print(result)
    


class Counter():
    
    def __init__(self, loop, maxCallbackCount):
        self._loop = loop
        self._maxCallbackCount = maxCallbackCount
        self._callbackCount = 0

    
    def onData(self, interest, data):
        self._callbackCount += 1
        dump("Got data packet with name", data.getName().toUri())
        dump(data.getContent().toRawStr())

        if self._callbackCount >= self._maxCallbackCount:
            self._loop.stop()


    def onTimeout(self, interest):
        self._callbackCount += 1
        dump("Time out for interest", interest.getName().toUri())

        if self._callbackCount >= self._maxCallbackCount:
            self._loop.stop()


    def onNetworkNack(self, interest, networkNack):
        self._callbackCount += 1
        dump("Network nack for interest", interest.getName().toUri())

        if self._callbackCount >= self._maxCallbackCount:
            self._loop.stop()

def main():

    # silence the warning from interest wire encode
    Interest.setDefaultCanBePrefix(True)

    # get an event loop
    loop = asyncio.get_event_loop()

    # set up a face that connects to the remote forwarder
    ip_address = input("Enter an IP address to tunnel to: ")
    udp_connection_info = UdpTransport.ConnectionInfo(ip_address, 6363)
    udp_transport = UdpTransport()
    face = ThreadsafeFace(udp_transport, udp_connection_info)

    #  face.setCommandSigningInfo(KeyChain(), certificateName)
    #  face.registerPrefix(Name("/ndn"), onInterest, onRegisterFailed)

    counter = Counter(loop, 10)

    name_text = input("Enter a prefix to request content from: ")

    for i in range(0, 10):
        name = Name(name_text + str(i))
        dump("Express name", name.toUri())
        interest = Interest(name)
        interest.setMustBeFresh(False)
        face.expressInterest(interest, counter.onData, counter.onTimeout, counter.onNetworkNack)



    # run until loop is shut down by the Counter
    loop.run_forever()
    face.shutdown()


main()


