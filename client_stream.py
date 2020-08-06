import time
import argparse
import asyncio
from pyndn import Name
from pyndn import Interest
from pyndn.transport import UdpTransport
from pyndn.threadsafe_face import ThreadsafeFace
from pyndn import Face
import numpy as np
import pandas as pd


def dump(*list):
    """Prints all parameters"""

    result = ""
    for element in list:
        result += (element if type(element) is str else str(element)) + " "
    print(result)


class Consumer():
    """Creates a consumer for sending interest packets."""

    def __init__(self, ip, verbose=0):

        # constants for adjusting performance
        self.UPDATE_TIMING = 0.001
        self.SEND_RATE = 0.00001

        # establish asyncio loop
        self._loop = asyncio.get_event_loop()
        #  self._loop.set_debug(True)

        # set up runtime
        self._time_to_run = 0
        # control verbosity
        self._verbose = verbose
        # establish a local or remote face
        self._face = self._setup_face(ip)
        # a prefix variable
        self._prefix = ""

        # create a list of dictionaries for storing data from this stream
        self._data = []

        # keep track of some performance metrics
        self._interests_sent = {'current': 0, 'previous': 0}
        self._data_recieved = {'current': 0, 'previous': 0}
        self._num_nacks = {'current': 0, 'previous': 0}
        self._num_timeouts = {'current': 0, 'previous': 0}
        self._time = {'current': 0, 'previous': 0, 'start': 0}
        self._time_to_first_byte = 0
        # keeps track of the whether the first data packet has been recieved
        self._is_first_packet = True
        self._send_latency_packet = False
        self._latency = {'interest': 0, 'data': 0}
        self._latency_packet = ""
        self._data_goodput = {'current': 0, 'previous': 0}


        print(f"Consumer instance created with UDP tunnel to {ip}!")


    def _setup_face(self, ip):
        """Sets up a face that connects to a remote forwarder."""
        udp_connection_info = UdpTransport.ConnectionInfo(ip, 6363)
        udp_transport = UdpTransport()
        return ThreadsafeFace(self._loop, udp_transport, udp_connection_info)


    def run(self, prefix, time_to_run):
        """Runs this consumer, sending interests to the specified prefix.

        Returns a dataframe containing performance information for analysis.
        """

        print(f"Starting stream for {time_to_run} seconds to {prefix}...")

        # properly name interests
        if prefix[-1] != '/':
            self._prefix = prefix + '/'
        else:
            self._prefix = prefix

        self._time_to_run = time_to_run

        # update face to recieve packets
        self._loop.create_task(self._update())
        # calculate and store performance information
        self._loop.create_task(self._compute_metrics(0.5))
        # send interest stream
        self._loop.create_task(self._send_interests(self._prefix, time_to_run))
        # schedule shutdown
        self._loop.create_task(self._shutdown())

        # start event loop and run shutdown method activates
        self._loop.run_forever()

        # shutdown face to forwarder
        self._face.shutdown()

        # create dataframe from list of dictionaries
        return pd.DataFrame(self._data)


    async def _send_interests(self, prefix, send_time):
        """Sends a specified amount of interests with sequentially numbered names."""

        # begin timing
        self._time['current'] = self._time['start'] = time.time()

        # send interests for a specified amount of time
        i = 0
        while time.time() - self._time['start'] < send_time:
            if self._send_latency_packet:
                self._latency_packet = prefix + str(i)
                self._latency['interest'] = time.time()
                self._send_latency_packet = False
            self._send(prefix + str(i))
            i += 1
            # interest sending rate
            await asyncio.sleep(self.SEND_RATE)


    def _send(self, name):
        """Sends a singular interest."""
        interest = Interest(name)
        interest.setMustBeFresh(False)
        self._face.expressInterest(interest, self.onData, self.onTimeout, self.onNetworkNack)
        self._interests_sent['current'] += 1

        if self._verbose >= 2:
            dump("Send interest with name", name)


    def onData(self, interest, data):
        """Called when a data packet is recieved."""

        if self._is_first_packet:
            self._time_to_first_byte = time.time()
            self._is_first_packet = False

        if self._latency_packet == data.getName().toUri():
            self._latency['data'] = time.time()

        self._data_recieved['current'] += 1

        if self._verbose >= 2:
            dump("Got data packet with name", data.getName().toUri())
            dump(data.getContent().toRawStr())

        # add the data packet size to total goodput
        self._data_goodput['current'] += len(data.getContent())


    def onTimeout(self, interest):
        """Called when an interest packet times out."""
        self._num_timeouts['current'] += 1
        if self._verbose >= 2:
            dump("Time out for interest", interest.getName().toUri())


    def onNetworkNack(self, interest, networkNack):
        """Called when an interest packet is responded to with a nack."""
        self._num_nacks['current'] += 1
        if self._verbose >= 2:
            dump("Network nack for interest", interest.getName().toUri())


    async def _compute_metrics(self, measurement_rate):
        """Returns a dictionary containing performance information.

        Snapshots information every measurement_rate seconds.
        """

        while True:

            # snapshot previous time and goodput
            self._data_goodput['previous'] = self._data_goodput['current']
            self._time['previous'] = time.time()
            self._num_nacks['previous'] = self._num_nacks['current']
            self._num_timeouts['previous'] = self._num_timeouts['current']
            self._interests_sent['previous'] = self._interests_sent['current']

            # arrange for latency measurement
            self._send_latency_packet = True

            # allow other tasks to be completed
            await asyncio.sleep(measurement_rate)

            # record time for bandwidth calculation
            self._time['current'] = time.time()

            # calculate current goodput in kilobytes
            data_goodput_kilobytes  = (self._data_goodput['current'] - self._data_goodput['previous']) / 1000

            # calculate kbps
            download_kbps = (data_goodput_kilobytes * 8) / (self._time['current'] - self._time['previous'])

            # calculate time to first byte (milliseconds)
            try:
                time_to_first_byte_ms = (self._time_to_first_byte - self._time['start']) * 1000
            except:
                print("Time to first byte could not be calculated.")
                time_to_first_byte_ms = "not computed"

            # calculate packet loss (as a percentage)
            dropped_packets = (self._num_timeouts['current'] - self._num_timeouts['previous']) + (self._num_nacks['current'] - self._num_nacks['previous'])
            requested_packets = self._interests_sent['current'] - self._interests_sent['previous']

            if requested_packets != 0:
                packet_loss = (dropped_packets / requested_packets) * 100
            else:
                packet_loss = 0

            # calculate average latency
            average_latency = 'not implemented' # TODO

            if download_kbps == 0:
                latency = 0
            else:
                latency = (self._latency['data'] - self._latency['interest']) * 1000

            data = {'timestamp': time.time() - self._time['start'], # seconds since first interest
                    'total_interests_sent': self._interests_sent['current'],
                    'total_data_recieved': self._data_recieved['current'],
                    'total_num_timeouts': self._num_timeouts['current'],
                    'total_num_nacks': self._num_nacks['current'],
                    'packet_loss_percent': packet_loss,
                    'time_to_first_byte_ms': time_to_first_byte_ms,
                    'latency': latency,
                    'data_goodput_kilobytes': data_goodput_kilobytes,
                    'total_data_goodput_kilobytes': self._data_goodput['current'] / 1000,
                    'bitrate_kbps': download_kbps,
                    'average_latency': average_latency
                    }


            # add data to log
            self._data.append(data)



    async def _update(self):
        """Updates events on this Consumer's face."""
        while True:
            self._face.processEvents()
            await asyncio.sleep(self.UPDATE_TIMING)


    async def _shutdown(self):
        """Shuts down this particular consumer and ends timing."""

        # wait to shutdown
        await asyncio.sleep(self._time_to_run)

        # wait 5 seconds to allow any unrecieved interests to timeout
        await asyncio.sleep(5)

        if self._loop is not None:
            self._loop.stop()



def rate_parser(string):
    """Parses the rate argument."""
    try:
        parsed_rate = float(string)
    except ValueError:
        raise argparse.ArgumentTypeError("Error in parsing rate parameter, please enter a valid one")
    return parsed_rate


def main():
    """Runs a consumer with the specified properties."""

    # silence the warning from interest wire encode
    Interest.setDefaultCanBePrefix(True)

    # handle and specify arguments
    parser = argparse.ArgumentParser()

    parser.add_argument("-p", "--prefix", help="the prefix to request data from", action="append", default=["/ndn/external/test"])
    parser.add_argument("-t", "--time", help="the number of seconds to run each stream for", type=int, default=10)
    parser.add_argument("-f", "--filename", help="the output file to store data to (in CSV form)")
    parser.add_argument("-i", "--ipaddress", help="the ip address to tunnel to", default="10.10.1.1")
    #  parser.add_argument("-r", "--rate", help="the rate at which interests are sent", type=rate_parser, default="0.00001")
    parser.add_argument("-v", "--verbosity", help="increase output verbosity", choices=[0, 1, 2], type=int, default=0)
    parser.add_argument("-d", "--demo", help="enable demo mode (more intuitive printouts)", action="store_true")

    args = parser.parse_args()

    # clean up prefix argument
    if len(args.prefix) > 1:
        args.prefix.pop(0)

    # create a list for storing dataframes
    final_data = []

    # run experiment once for provided prefix
    for namespace in args.prefix:
        consumer = Consumer(args.ipaddress, verbose=args.verbosity)
        #  TODO: add rate functionality back in if needed

        # run consumer and put output into dataframe
        final_data.append(consumer.run(namespace, args.time))


    # store output to file if filename option is enabled
    if args.filename is not None:
        i = 0
        for dataframe in final_data:
            dataframe.to_csv(args.filename + args.prefix[i].replace('/', '-'), index=False)
            i += 1

    # print results to stdout
    if not args.demo:
        for dataframe in final_data:
            print(dataframe)

    # print modified results for demo
    if args.demo:
        for dataframe in final_data:
            print(dataframe[['timestamp', 'packet_loss_percent', 'total_data_goodput_kilobytes', 'bitrate_kbps', 'latency']])
            #  print(f"Average bitrate: {dataframe.bitrate_kbps.sum() / len(dataframe.index)} kbps")
            #  print(len(dataframe.index))
            #  print(f"Time to first byte: {dataframe.loc[0, 'time_to_first_byte_ms']} ms")

            # compute average latency, loss, and bitrate
            for bitrate in dataframe['bitrate_kbps'].tolist():
                total = num = 0
                if bitrate != 0:
                    total += bitrate
                    num += 1
                print(f"Average bitrate: {total / num} kbps")

            for latency in dataframe['latency'].tolist():
                total = num = 0
                if latency != 0:
                    total += latency
                    num += 1
                print(f"Average latency: {total / num} ms")

            #  print(f"Average packet loss: {(dataframe.tail(1)['total_num_timeouts']) / (dataframe.tail(1)['total_interests_sent])}")


main()

# TODO list:
#  adjust verbosity implementation
#  revamp timing and reporting metrics
#  fix time to first byte implementation
#  add average latency implementation
