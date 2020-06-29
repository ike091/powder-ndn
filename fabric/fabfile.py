""" 
This script handles various tasks for the powder-ndn profile 

"""
from fabric import Connection


# set up ssh addresses
ADDRESS_BEGINNING = 'pc06-fortvm-'
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




# start main scripting here


