"""
This script handles setup for the powder-ndn profile

"""
import argparse
from fabric import Connection
from fabric.transfer import Transfer



def install_dtach():
    """Installs dtach on all connections."""
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

    # note that these may need to be updated if profile topology changes
    shape_link(connection['up-cl'], 'eth3', internal_latency, internal_packet_loss, internal_bandwidth, latency_variation=3)
    shape_link(connection['up-cl'], 'eth2', external_latency, external_packet_loss, external_bandwidth, latency_variation=10)


def shape_link(this_connection, interface, latency, packet_loss, bandwidth, latency_variation=3):
    """Set packet loss, bandwidth, and latency on a given connection and interface."""

    # TODO: fix this to work with no latency and packet loss values

    this_connection.run(f'sudo tc qdisc replace dev {interface} root handle 1: netem loss {packet_loss}% delay {latency}ms {latency_variation}ms distribution normal')
    this_connection.run(f'sudo tc qdisc replace dev {interface} parent 1: handle 2: tbf rate {bandwidth}mbit latency 400ms burst 100mbit')
    this_connection.run(f'sudo tc qdisc show dev {interface}')


def clear_qdiscs():
    """Clears the two qdiscs on the up-cl router."""
    connection['up-cl'].run(f'sudo tc qdisc del dev eth2 root')
    connection['up-cl'].run(f'sudo tc qdisc del dev eth3 root')


def reset_nfd():
    """Restarts the NDN forwarding daemon on all routers."""
    routers = ('up-cl', 'external-dn', 'internal-dn')
    for router in routers:
        connection[router].run('nfd-stop')
        connection[router].run('nfd-start')


def update_repositories():
    """Updates git repository on all nodes."""
    for c in connection.values():
        c.run('cd /local/repository && git stash && git checkout master && git pull')


def set_caching(caching_state):
    """Turn caching in the network on or off."""
    routers = ('up-cl', 'external-dn', 'internal-dn')
    for router in routers:
        if caching_state:
            connection[router].run('nfdc cs config serve on')
        else:
            connection[router].run('nfdc cs config serve off')


def set_servers(server_state):
    if server_state:
        run_bg(connection['external-dn'], 'python3 /local/repository/server_stream.py -p /ndn/external/test')
        run_bg(connection['internal-dn'], 'python3 /local/repository/server_stream.py -p /ndn/internal/test')
        print('servers on')


def run_client(number):
    #  number = str(number)
    #  run_bg(connection['client' + number], f'python3 /local/repository/client_stream.py -p /ndn/external/test -p /ndn/internal/test -t 120 -f data{number} -i 155.98.37.73')
    for i in range(1, 9):
        run_bg(connection['client' + str(i)], f'python3 /local/repository/client_stream.py -p /ndn/external/test -p /ndn/internal/test -t 20 -f data{str(i)} -i 155.98.37.73')


def stream_on_all_nodes():
    """Start streaming on all client nodes."""

    # iterate only through client nodes
    for name, c in connection.items():
        if name[:6] == 'client':
            run_bg(c, 'python3 /local/repository/client_stream.py -p /ndn/external/test -f data-{name} -i 155.98.37.73')


def fetch_data():
    #  i = 1
    #  for name, c in connection.items():
        #  if name[:6] == 'client':
            #  connection[f'client{str(i)}'].get(f"/users/ike091/data{str(i)}-ndn-external-test.csv", local=f"/mnt/c/Isaak/POWDER/powder-ndn/data/data{str(i)}-ndn-external-test.csv")
            #  connection[f'client{str(i)}'].get(f"/users/ike091/data{str(i)}-ndn-internal-test.csv", local=f"/mnt/c/Isaak/POWDER/powder-ndn/data/data{str(i)}-ndn-internal-test.csv")
            #  i += 1

    for i in range(1, 9):
        connection['client' + str(i)].get(f"/users/ike091/data{str(i)}-ndn-external-test.csv", local=f"/mnt/c/Isaak/POWDER/powder-ndn/data/data{str(i)}-ndn-external-test.csv")
        connection['client' + str(i)].get(f"/users/ike091/data{str(i)}-ndn-internal-test.csv", local=f"/mnt/c/Isaak/POWDER/powder-ndn/data/data{str(i)}-ndn-internal-test.csv")

    for i in range(1, 9):
        connection['client' + str(i)].run(f"rm /users/ike091/data{str(i)}-ndn-external-test.csv")
        connection['client' + str(i)].run(f"rm /users/ike091/data{str(i)}-ndn-internal-test.csv")

    #  connection['client1'].get("/users/ike091/data1-ndn-external-test.csv", local="/mnt/c/Isaak/POWDER/powder-ndn/data/data1-ndn-external-test.csv")
    #  connection['client1'].get("/users/ike091/data1-ndn-internal-test.csv", local="/mnt/c/Isaak/POWDER/powder-ndn/data/data1-ndn-internal-test.csv")


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
parser.add_argument("pc_number", help="the number corresponding to the pc running the routers in the experiement")
parser.add_argument("pc_number_2", help="the number corresponding to the pc running the client nodes in the experiement")
parser.add_argument("client_node_count", help="the number of client nodes in the experiment", type=int)

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

# remove all network adjustments option
parser.add_argument("--clear", help="clear network qdiscs", action="store_true")

# pull from github option
parser.add_argument("-u", "--update_repos", help="pull new changes into all profile repositories", action="store_true")

# set to specify alternate ssh address
parser.add_argument("-a", "--address", help="sets the MEB as the server location", action="store_true")

# adjust network caching
parser.add_argument("-c", "--caching", help="turn in-network caching on or off", choices=["on", "off"])

# start and stop servers
parser.add_argument("-s", "--servers", help="turn servers on or off", choices=["on", "off"])

# run clients
parser.add_argument("-r", "--run_clients", help="start client streaming", action="store_true")

# fetch streaming data
parser.add_argument("-f", "--fetch", help="fetch client streaming data", action="store_true")


args = parser.parse_args()

# set up ssh addresses
if args.address:
    ADDRESS_BEGINNING = f'pc{args.pc_number}-mebvm-'
else:
    ADDRESS_BEGINNING = f'pc{args.pc_number}-fortvm-'
ADDRESS_END = '.emulab.net'
USERNAME = 'ike091'

ROUTER_HOSTS = {'up-cl': '3',
                'external-dn': '1',
                'internal-dn': '2'
                }

CLIENT_HOSTS = {}
for i in range(1, args.client_node_count + 1):
    CLIENT_HOSTS[f'client{i}'] = str(i)


# establish connections
connection = {}
for host, number in ROUTER_HOSTS.items():
    connection[host] = Connection(USERNAME + '@' + ADDRESS_BEGINNING + str(number) + ADDRESS_END)
    print('Connection added to: ' + USERNAME + '@' + ADDRESS_BEGINNING + str(number) + ADDRESS_END)

for host, number in CLIENT_HOSTS.items():
    connection[host] = Connection(USERNAME + '@' + f'pc{args.pc_number_2}-fortvm-' + str(number) + ADDRESS_END)
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

# if server flag is specified, set accordingly
if args.servers is not None and args.servers == "on":
    set_servers(True)
elif args.servers is not None:
    set_servers(False)

# run clients if flag is specified
if args.run_clients is not None and args.run_clients:
    run_client("1")

# fetch data if requested
if args.fetch is not None and args.fetch:
    fetch_data()

# configure network latency, loss, and bandwidth parameters
if args.internal_latency != 0 or args.external_latency != 0 or args.internal_loss != 0 or args.external_loss != 0 or args.bandwidth != [0, 0]:
    configure_network(args.internal_latency, args.internal_loss, args.bandwidth[0], args.external_latency, args.external_loss, args.bandwidth[1])

if args.clear:
    clear_qdiscs()


# close connections when finished
for c in connection.values():
    c.close()
    #  print('Connection closed to: ' + USERNAME + '@' + ADDRESS_BEGINNING + str(number) + ADDRESS_END) FIXME
