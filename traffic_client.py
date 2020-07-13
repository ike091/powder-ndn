import time
import argparse
import asyncio
from pyndn import Name
from pyndn import Interest
from pyndn.transport import UdpTransport
from pyndn.threadsafe_face import ThreadsafeFace
from pyndn import Face


def dump(*list):
    """Prints all parameters"""

    result = ""
    for element in list:
        result += (element if type(element) is str else str(element)) + " "
    print(result)
    


class Consumer():
    
    def __init__(self, ip, verbose=False):
        # establish asyncio loop
        self._loop = asyncio.get_event_loop()
        self._loop.set_debug(True)

        # set up counters so we know when consumer is finished
        self._maxCallbackCount = 0
        self._callbackCount = -1

        # control verbosity
        self._verbose = verbose

        # establish a local or remote face
        self._face = self._setup_face(ip)

        # keep track of some performance metrics
        self._interests_sent = 0
        self._data_recieved = 0
        self._num_nacks = 0
        self._num_timeouts = 0
        print(f"Consumer instance created with UDP tunnel to {ip}!")


    def _setup_face(self, ip):
        """Sets up a face that connects to a remote forwarder."""
        udp_connection_info = UdpTransport.ConnectionInfo(ip, 6363)
        udp_transport = UdpTransport()
        return ThreadsafeFace(self._loop, udp_transport, udp_connection_info)


    def send_interests(self, prefix, num_interests):
        """Sends a specified number of interests to the specified prefix."""

        print(f"Sending {num_interests} interests to {prefix}...")

        # start counting callbacks
        self._callbackCount = 0
        self._maxCallbackCount = num_interests

        # properly name interests 
        if prefix[-1] == '/':
            prefix = prefix
        else:
            prefix = prefix + '/'

        # create asyncio loop and run until explicitly shut down
        self._loop.create_task(self._update())
        self._loop.create_task(self._send_all(prefix, num_interests))
        self._loop.run_forever()


    async def _send_all(self, prefix, num_interests):
        for i in range(0, num_interests):
            self._send(prefix + str(i))
        await asyncio.sleep(0.0001)


    def _send(self, name):
        """Send a singular interest."""
        interest = Interest(name)
        interest.setMustBeFresh(False)
        self._face.expressInterest(interest, self.onData, self.onTimeout, self.onNetworkNack)
        self._interests_sent += 1

        if(self._verbose):
            dump("Send interest with name", name)

    
    def onData(self, interest, data):
        """Called when a data packet is recieved."""
        self._callbackCount += 1
        self._data_recieved += 1

        if(self._verbose):
            dump("Got data packet with name", data.getName().toUri())
            dump(data.getContent().toRawStr())

        if self._callbackCount >= self._maxCallbackCount:
            self.shutdown()


    def onTimeout(self, interest):
        """Called when an interest packet times out."""
        self._callbackCount += 1
        self._num_timeouts += 1
        if(self._verbose):
            dump("Time out for interest", interest.getName().toUri())

        if self._callbackCount >= self._maxCallbackCount:
            self.shutdown()


    def onNetworkNack(self, interest, networkNack):
        """Called when an interest packet is responded to with a nack."""
        self._callbackCount += 1
        self._num_nacks += 1
        if(self._verbose):
            dump("Network nack for interest", interest.getName().toUri())

        if self._callbackCount >= self._maxCallbackCount:
            self.shutdown()


    def print_status_report(self):
        """Prints diagnostic information."""
        print("\n----------------------------------")
        print(f"{self._interests_sent} interests sent")
        print("----------------------------------")
        print(f"{self._data_recieved} data packets recieved")
        print(f"{self._num_nacks} nacks")
        print(f"{self._num_timeouts} timeouts")
        print("----------------------------------\n")


    async def _update(self):
        """Updates events on the face"""
        while True:
            if self._face is not None:
                self._face.processEvents()
                await asyncio.sleep(0.01)


    def shutdown(self):
        """Shuts down this particular consumer"""
        self._face.shutdown()
        if self._loop is not None:
            self._loop.stop()
        self.print_status_report()



def main():

    # silence the warning from interest wire encode
    Interest.setDefaultCanBePrefix(True)

    # handle and specify arguments
    parser = argparse.ArgumentParser()

    parser.add_argument("-p", "--prefix", help="the prefix to request data from", default="/ndn/external/test")
    parser.add_argument("-c", "--count", help="the number of interests to send", type=int, default=10)
    parser.add_argument("-i", "--ipaddress", help="the ip address to tunnel to", default="10.10.1.1")
    parser.add_argument("-v", "--verbosity", help="increase output verbosity", action="store_true")

    args = parser.parse_args()


    # create a consumer and send interests with it
    consumer = Consumer(args.ipaddress, verbose=args.verbosity)
    consumer.send_interests(args.prefix, args.count)

    input("Press enter to shutdown this consumer.")


main()


