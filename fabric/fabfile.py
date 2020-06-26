from fabric import Connection


ADDRESS_BEGINNING = 'pc07-fortvm-'
ADDRESS_END = '.emulab.net'
USERNAME = 'ike091'

HOSTS = {'UE1': '3', 
                'UE2': '4',
                'up-cl': '5',
                'external-dn': '1',
                'internal-dn': '2'
                }

connection = {}
for host, number in HOSTS.items():
    connection[host] = Connection(USERNAME + '@' + ADDRESS_BEGINNING + str(number) + ADDRESS_END)
    print('Connection added to: ' + USERNAME + '@' + ADDRESS_BEGINNING + str(number) + ADDRESS_END)


def create_faces():
    connection['up-cl'].run('nfdc face create udp4://10.10.3.2')
    connection['up-cl'].run('nfdc face create udp4://10.10.2.2')
    connection['external-dn'].run('nfdc face create udp4://10.10.2.1')
    connection['internal-dn'].run('nfdc face create udp4://10.10.3.1')


def start_nlsr():
    connection['up-cl'].run('nlsr -f ~/nlsr/nlsr.conf &')
    #  connection['external-dn'].run('nlsr -f ~/nlsr/nlsr.conf &')
    #  connection['internal-dn'].run('nlsr -f ~/nlsr/nlsr.conf &')


def start_ping_servers():
    connection['up-cl'].run('ndnpingserver /ndn/up-cl/ping &')
    connection['external-dn'].run('ndnpingserver /ndn/external/ping &')
    connection['internal-dn'].run('ndnpingserver /ndn/internal/ping &')


start_nlsr()
#  start_ping_servers()

