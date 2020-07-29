"""
This script handles setup for the powder-ndn profile

"""
import argparse
from fabric import Connection



def install_dtach():
    """Installs dtach on all connections"""
    for c in connection.values():
        c.run('sudo apt install dtach')


def run_bg(this_connection, cmd, sockname='dtach'):
    """Runs a process in the background with dtach"""
    return this_connection.run('dtach -n `mktemp -u /tmp/%s.XXXX` %s' % (sockname, cmd))


def create_faces():
    """Creates the relevant UDP faces between routers"""
    connection['up-cl'].run('nfdc face create udp4://10.10.3.2')
    connection['up-cl'].run('nfdc face create udp4://10.10.2.2')
    connection['external-dn'].run('nfdc face create udp4://10.10.2.1')
    connection['internal-dn'].run('nfdc face create udp4://10.10.3.1')


def start_nlsr():
    """Starts the NLSR routing daemon on all servers"""
    run_bg(connection['up-cl'], 'nlsr -f ~/nlsr/nlsr.conf')
    run_bg(connection['external-dn'], 'nlsr -f ~/nlsr/nlsr.conf')
    run_bg(connection['internal-dn'], 'nlsr -f ~/nlsr/nlsr.conf')


def start_ping_servers():
    """Starts ping servers on all three servers"""
    run_bg(connection['up-cl'], 'ndnpingserver /ndn/up-cl/ping')
    run_bg(connection['external-dn'], 'ndnpingserver /ndn/external/ping')
    run_bg(connection['internal-dn'], 'ndnpingserver /ndn/internal/ping')


def configure_network(internal_latency, internal_packet_loss, internal_bandwidth, external_latency, external_packet_loss, external_bandwidth):
    """Configure latency, bandwidth, and packet loss rates to internal and external networks.

    Note that this may need to be updated if profile topolgy changes.
    """

    #  set_latency(connection['up-cl'], "eth3", internal_latency)
    #  set_bandwidth(connection['up-cl'], "eth3", internal_bandwidth)
    #  set_packet_loss(connection['up-cl'], "eth3", internal_packet_loss)

    #  set_latency(connection['up-cl'], "eth2", external_latency)
    #  set_bandwidth(connection['up-cl'], "eth2", external_bandwidth)
    #  set_packet_loss(connection['up-cl'], "eth2", external_packet_loss)

    # note that this may need to be updated if profile topology changes
    shape_link(connection['up-cl'], 'eth3', internal_latency, internal_packet_loss, bandwidth, latency_variation=3)

    # note that this may need to be updated if profile topology changes
    shape_link(connection['up-cl'], 'eth2', external_latency, external_packet_loss, bandwidth, latency_variation=10)


def shape_link(this_connection, interface, latency, packet_loss, bandwidth, latency_variation=3):
    """Set packet loss, bandwidth, and latency on a given connection and interface."""

    # TODO: properly implement this method, bandwidth included

    if latency == 0 and packet_loss == 0:
        return this_connection.run(f'sudo tc qdisc del root dev {interface}')
    elif packet_loss == 0:
        return this_connection.run(f'sudo tc qdisc replace dev {interface} root netem delay {latency}ms')
    elif latency == 0:
        return this_connection.run(f'sudo tc qdisc replace dev {interface} root netem loss {packet_loss}%')
    else:
        return this_connection.run(f'sudo tc qdisc replace dev {interface} root netem loss {packet_loss}% delay {latency}ms {latency_variation}ms distribution normal')

    #  this_connection.run(f'sudo tc qdisc replace dev {interface} root handle 1:0 netem delay {latency}ms')
    #  this_connection.run(f'sudo tc qdisc replace dev {interface} parent 1:0


    #  return this_connection.run(f'tc qdisc add dev {interface} root tbf rate 1mbit burst 32kbit latency 400ms')


def reset_nfd():
    """Restarts the NDN forwarding daemon."""
    for k, c in connection.items():
        if k != 'UE1':
            c.run('nfd-stop')
            c.run('nfd-start')


def update_repositories():
    """Updates git repository on all nodes."""
    for c in connection.values():
        c.run('cd /local/repository && git stash && git checkout master && git pull')


def set_caching(caching_state):
    """Turn caching in the network on or off."""
    for k, c in connection.items():
        if k != 'UE1':
            if caching_state:
                c.run('nfdc cs config serve on')
            else:
                c.run('nfdc cs config serve off')


def parse_packet_loss(string):
    """Properly parse packet loss integer values."""
    try:
        value = int(string)
    except ValueError:
        raise argparse.ArgumentTypeError("Please enter a packet loss rate between 0 and 100%.")
    if value > 100 or value < 0:
        raise argparse.ArgumentTypeError("Please enter a packet loss rate between 0 and 100%.")
    return value


# begin rest of script

parser = argparse.ArgumentParser()

# add mandatory pc number section
parser.add_argument("pc_number", help="the number corresponding to the pc running the POWDER experiement")

# network setup and reset options
group = parser.add_mutually_exclusive_group()
group.add_argument("-S", "--setup", help="setup the network from scratch", action="store_true")
group.add_argument("-R", "--reset", help="reset the forwarding and routing daemons", action="store_true")

# network latency and loss parameters
parser.add_argument("-n", "--internal_loss", help="set internal packet loss rate (0 - 100)", type=parse_packet_loss, default=0)
parser.add_argument("-x", "--external_loss", help="set external packet loss rate (0 - 100)", type=parse_packet_loss, default=0)
parser.add_argument("-i", "--internal_latency", help="set internal latency (ms)", metavar="INTERNAL_LATENCY", type=int, default=0, choices=range(1, 1000))
parser.add_argument("-e", "--external_latency", help="set external latency (ms)", metavar="EXTERNAL_LATENCY", type=int, default=0, choices=range(1, 1000))

# bandwidth parameters (note that a 0 indicates no bandwidth restriction)
parser.add_argument("-b", "--bandwidth", help="set internal and external bandwidth (mbits) - usage: -b [INTERNAL] [EXTERNAL]", type=int, default=[0, 0], nargs=2)

# pull from github option
parser.add_argument("-u", "--update_repos", help="pull new changes into all profile repositories", action="store_true")


# set to specify alternate ssh address
parser.add_argument("-a", "--address", help="sets the MEB as the server location", action="store_true")

# adjust network caching
parser.add_argument("-c", "--caching", help="turn in-network caching on or off", choices=["on", "off"])

args = parser.parse_args()

# set up ssh addresses
if args.address:
    ADDRESS_BEGINNING = f'pc{args.pc_number}-mebvm-'
else:
    ADDRESS_BEGINNING = f'pc{args.pc_number}-fortvm-'
ADDRESS_END = '.emulab.net'
USERNAME = 'ike091'

HOSTS = {'UE1': '3',
                'up-cl': '4',
                'external-dn': '1',
                'internal-dn': '2'
                }

# establish connections
connection = {}
for host, number in HOSTS.items():
    connection[host] = Connection(USERNAME + '@' + ADDRESS_BEGINNING + str(number) + ADDRESS_END)
    print('Connection added to: ' + USERNAME + '@' + ADDRESS_BEGINNING + str(number) + ADDRESS_END)


# run methods based on command line arguments specified
if args.setup:
    create_faces()
    start_nlsr()
    start_ping_servers()
elif args.reset:
    reset_nfd()
    create_faces()
    start_nlsr()
    start_ping_servers()

if args.update_repos:
    update_repositories()

# if caching flag is specified, set accordingly
if args.caching is not None and args.caching == "on":
    set_caching(True)
elif args.caching is not None:
    set_caching(False)

# configure network latency, loss, and bandwidth parameters
#  configure_network(args.internal_latency, args.internal_loss, args.bandwidth[0], args.external_latency, args.external_loss, args.bandwidth[1])


# close connections when finished
for c in connection.values():
    c.close()
    print('Connection closed to: ' + USERNAME + '@' + ADDRESS_BEGINNING + str(number) + ADDRESS_END)
