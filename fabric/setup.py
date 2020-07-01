"""
This script handles setup for the powder-ndn profile

"""
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


def shape_link(this_connection, interface, latency, packet_loss=0, packet_loss_variation=10):
    """Set packet loss and latency on a connection/interface"""

    if packet_loss == '0':
        return this_connection.run(f'sudo tc qdisc replace dev {interface} root netem delay {latency}ms {packet_loss_variation}ms distribution normal')
    else:
        return this_connection.run(f'sudo tc qdisc replace dev {interface} root netem loss {packet_loss}% delay {latency}ms {packet_loss_variation}ms distribution normal')


def configure_network():
    """Configure latencies and packet loss rates to internal and external networks"""

    internal_latency = input('Set latency to internal network: ')
    internal_packet_loss = input('Set packet loss to internal network: ')

    shape_link(connection['up-cl'], 'eth3', internal_latency, internal_packet_loss, 3)

    external_latency = input('Set latency to external network: ')
    external_packet_loss = input('Set packet loss to external network: ')

    shape_link(connection['up-cl'], 'eth2', external_latency, external_packet_loss, 10)


# figure out bandwidth setting
def set_bandwidth(this_connection, interface, bandwidth):
    return this_connection.run(f'tc qdisc add dev {interface} root tbf rate 1mbit burst 32kbit latency 400ms')


# setup connection addresses

pc_number = input('Enter the host pc number: ')

# set up ssh addresses
ADDRESS_BEGINNING = f'pc{pc_number}-fortvm-'
ADDRESS_END = '.emulab.net'
USERNAME = 'ike091'

HOSTS = {'UE1': '3', 
                'UE2': '4',
                'up-cl': '5',
                'external-dn': '1',
                'internal-dn': '2'
                }

# establish connections
connection = {}
for host, number in HOSTS.items():
    connection[host] = Connection(USERNAME + '@' + ADDRESS_BEGINNING + str(number) + ADDRESS_END)
    print('Connection added to: ' + USERNAME + '@' + ADDRESS_BEGINNING + str(number) + ADDRESS_END)


# setup faces, nlsr, and ping servers if user specifies 'y'
if input('Is the network being set up for the first time? (y/n) ') == 'y':
    install_dtach()
    create_faces()
    start_nlsr()
    start_ping_servers()


# reconfigure packet loss and latency settings if requested
if input('Do you want to reconfigure packet loss and latency? (y/n) ') == 'y':
    configure_network()


for c in connection.values():
    c.close()
