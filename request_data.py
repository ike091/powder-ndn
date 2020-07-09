import time
from pyndn import Name
from pyndn import Face
from pyndn import Interest
from pyndn.transport import UdpTransport
from pyndn.security import KeyChain


def dump(*list):
    """Prints all parameters"""

    result = ""
    for element in list:
        result += (element if type(element) is str else str(element)) + " "
    print(result)
    


class Counter():
    
    def __init__(self):
        self._callbackCount = 0

    
    def onData(self, interest, data):
        self._callbackCount += 1
        dump("Got data packet with name", data.getName().toUri())
        dump(data.getContent().toRawStr())


    def onTimeout(self, interest):
        self._callbackCount += 1
        dump("Time out for interest", interest.getName().toUri())


    def onNetworkNack(self, interest, networkNack):
        self._callbackCount += 1
        dump("Network nack for interest", interest.getName().toUri())


def main():

    # silence the warning from interest wire encode
    Interest.setDefaultCanBePrefix(True)

    # set up a face that connects to the remote forwarder
    ip_address = input("Enter an IP address to connect to: ")
    udp_connection_info = UdpTransport.ConnectionInfo(ip_address, 6363)
    udp_transport = UdpTransport()
    face = Face(udp_transport, udp_connection_info)

    counter = Counter()

    # try to fetch from provided name
    name_text = input("Enter a name to request content from: ")
    name = Name(name_text)
    dump("Express name", name.toUri())

    interest = Interest(name)
    interest.setMustBeFresh(False)
    face.expressInterest(interest, counter.onData, counter.onTimeout, counter.onNetworkNack)

    while counter._callbackCount < 1:
        face.processEvents()

        # don't use 100% of the CPU
        time.sleep(0.01)

    face.shutdown()


main()


