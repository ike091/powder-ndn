""" 
This script handles setup for the powder-ndn profile 

"""
from fabric import Connection



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


def install_dtach():
    for c in connection.values(): 
        c.run('sudo apt install dtach')


def run_bg(this_connection, cmd, sockname='dtach'):
    return this_connection.run('dtach -n `mktemp -u /tmp/%s.XXXX` %s' % (sockname, cmd))


def create_faces():
    connection['up-cl'].run('nfdc face create udp4://10.10.3.2')
    connection['up-cl'].run('nfdc face create udp4://10.10.2.2')
    connection['external-dn'].run('nfdc face create udp4://10.10.2.1')
    connection['internal-dn'].run('nfdc face create udp4://10.10.3.1')


def start_nlsr():
    run_bg(connection['up-cl'], 'nlsr -f ~/nlsr/nlsr.conf')
    run_bg(connection['external-dn'], 'nlsr -f ~/nlsr/nlsr.conf')
    run_bg(connection['internal-dn'], 'nlsr -f ~/nlsr/nlsr.conf')


def start_ping_servers():
    run_bg(connection['up-cl'], 'ndnpingserver /ndn/up-cl/ping')
    run_bg(connection['external-dn'], 'ndnpingserver /ndn/external/ping')
    run_bg(connection['internal-dn'], 'ndnpingserver /ndn/internal/ping')


def set_latency(this_connection, interface, latency):
    return this_connection.run(f'sudo tc qdisc replace dev {interface} root netem delay {latency}ms')


# start main scripting here

install_dtach()
create_faces()
start_nlsr()
start_ping_servers()

# set latencies
external_latency = input('Set latency to external network: ')
set_latency(connection['up-cl'], 'eth3', external_latency)

internal_latency = input('Set latency to internal network: ')
set_latency(connection['up-cl'], 'eth3', internal_latency)

# set packet loss rates 
external_latency = input('Set latency to external network: ')
set_latency(connection['up-cl'], 'eth3', external_latency)

internal_latency = input('Set latency to internal network: ')
set_latency(connection['up-cl'], 'eth3', internal_latency)

