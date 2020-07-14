"""
This script handles setup for the powder-ndn profile

"""
from fabric import Connection


# setup connection addresses

pc_number = input('Enter the host pc number: ')

# set up ssh addresses
ADDRESS_BEGINNING = f'pc{pc_number}-fortvm-'
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


def shape_link(this_connection, interface, latency, latency_variation=10, packet_loss=0):
    """Set packet loss and latency on a connection/interface"""
    
    if latency == '0' and packet_loss == '0':
        return this_connection.run(f'sudo tc qdisc del root dev {interface}')
    elif packet_loss == '0':
        return this_connection.run(f'sudo tc qdisc replace dev {interface} root netem delay {latency}ms')
    elif latency == '0':
        return this_connection.run(f'sudo tc qdisc replace dev {interface} root netem loss {packet_loss}%')
    else:
        return this_connection.run(f'sudo tc qdisc replace dev {interface} root netem loss {packet_loss}% delay {latency}ms {latency_variation}ms distribution normal')


def configure_network():
    """Configure latencies and packet loss rates to internal and external networks"""

    internal_latency = input('Set latency to internal network (ms): ')
    internal_packet_loss = input('Set packet loss percentage to internal network: ')

    shape_link(connection['up-cl'], 'eth3', internal_latency, 3, internal_packet_loss)

    external_latency = input('Set latency to external network (ms): ')
    external_packet_loss = input('Set packet loss percentage to external network: ')

    shape_link(connection['up-cl'], 'eth2', external_latency, 10, external_packet_loss)


def reset_nfd():
    """Restarts the NDN forwarding daemon."""
    for c in connection.values():
        c.run('nfd-stop')
        c.run('nfd-start')


def get_input(prompt, options):
    input_string = input(prompt)
    while input_string not in options:
        print("Please enter a valid option.")
        input_string = input(prompt)
    return input_string


# TODO: figure out bandwidth adjustment
def set_bandwidth(this_connection, interface, bandwidth):
    """Sets the bandwidth of a provided interface."""
    return this_connection.run(f'tc qdisc add dev {interface} root tbf rate 1mbit burst 32kbit latency 400ms')


# setup faces, nlsr, and ping servers if user specifies 'y'
if input('Is the network being set up for the first time? (y/n) ') == 'y':
    install_dtach()
    create_faces()
    start_nlsr()
    start_ping_servers()
elif input('Do any faces or routes need to be reconfigured? (y/n) ') == 'y':
    create_faces()
    start_nlsr()
    start_ping_servers()


# reconfigure packet loss and latency settings if requested
if input('Do you want to reconfigure packet loss and latency? (y/n) ') == 'y':
    configure_network()

if input('Would you like to reset the network? (y/n) ') == 'y':
    reset_nfd()

for c in connection.values():
    c.close()
