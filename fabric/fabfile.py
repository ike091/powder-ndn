""" 
This script handles various tasks for the powder-ndn profile 

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


def set_latency(this_connection, interface, latency):
    #  this_connection.run(f'sudo tc qdisc del dev {interface} root')
    return this_connection.run(f'sudo tc qdisc replace dev {interface} root netem delay {latency}ms')


def set_packet_loss(this_connection, interface, packet_loss):
    return this_connection.run(f'sudo tc qdisc add dev {interface} root netem loss {packet_loss}%')


# figure out bandwidth setting
#  def set_bandwidth(this_connection, interface, bandwidth):
    #  return this_connection.run(f'tc qdisc add dev {interface} root tbf rate 1mbit burst 32kbit latency 400ms')


# start main scripting here
set_latency(connection['up-cl'], 'eth3', 40)
set_latency(connection['up-cl'], 'eth1', 2)


