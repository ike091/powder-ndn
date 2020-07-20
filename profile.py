"""A profile for experimenting with NDN in an abstract 5G network.

Instructions:
Wait for the profile instance to start, and then log into the various VMs via the ssh ports specified below.
"""

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as elab


class GLOBALS(object):
    """Useful constant values for setting up a powder experiment

    d740 - 24 cores, 192 GB RAM TODO: figure out the proper amount of ram, docs are incorrect
    d840 - 64 cores, 768 GB RAM
    d820 - 32 cores, 128 GB RAM
    """
    SITE_URN = "urn:publicid:IDN+emulab.net+authority+cm"
    UBUNTU18_IMG = "urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU18-64-STD"
    PHYSICAL_NODE_TYPES = ["d740", "d840", "d820"]


# define network parameters
portal.context.defineParameter("physical_host_type", "Type of physical host (d740, d840, or d820)", portal.ParameterType.STRING, 'd740')

# retrieve the values the user specifies during instantiation
params = portal.context.bindParameters()

# check node type validity
if params.physical_host_type not in GLOBALS.PHYSICAL_NODE_TYPES:
    portal.context.reportError(portal.ParameterError("Invalid node type."))


def make_VM(name, image, instantiateOn, cores, ram):
    """Creates a VM with the specified parameters

    Returns that VM
    """
    node = request.XenVM(name)
    node.disk_image = image
    node.cores = cores
    node.ram = ram * 1024
    node.exclusive = True
    node.routable_control_ip = True
    node.InstantiateOn(instantiateOn)
    return node


def create_UEs(count=2, prefix=1, instantiateOn='pnode', cores=2, ram=4):
    """Allocates and runs an install script on a specified number of VM UE nodes.

    Returns a list of nodes.
    """

    nodes = []
    # index nodes at one
    nodes.append(None)

    # create each VM
    for i in range(1, count + 1):
        nodes.append(make_VM('node' + str(prefix) + '-' + str(i), GLOBALS.UBUNTU18_IMG, instantiateOn=instantiateOn, cores=cores, ram=ram))

    # run client install script on each vm to install client software
    for node in nodes:
        if node is not None:
            node.addService(pg.Execute(shell="sh", command="chmod +x /local/repository/setup/install_ndn_client.sh"))
            node.addService(pg.Execute(shell="sh", command="/local/repository/setup/install_ndn_client.sh"))

    return nodes


def create_routers(names, instantiateOn='pnode', cores=4, ram=8):
    """Allocates and runs an install script on virtualized routers.

    Returns a list of routers.
    """

    routers = dict()

    for name in names:
        routers[name] = make_VM(name, GLOBALS.UBUNTU18_IMG, instantiateOn=instantiateOn, cores=cores, ram=ram)

        # run base install script
        routers[name].addService(pg.Execute(shell="sh", command="chmod +x /local/repository/setup/router_install.sh"))
        routers[name].addService(pg.Execute(shell="sh", command="/local/repository/setup/router_install.sh"))

        # run appropriate install scripts based on name of router
        routers[name].addService(pg.Execute(shell="sh", command="chmod +x /local/repository/setup/" + name + ".sh"))
        routers[name].addService(pg.Execute(shell="sh", command="/local/repository/setup/" + name + ".sh"))

        # install pyndn client software
        routers[name].addService(pg.Execute(shell="sh", command="chmod +x /local/repository/setup/install_ndn_client.sh"))
        routers[name].addService(pg.Execute(shell="sh", command="/local/repository/setup/install_ndn_client.sh"))

    return routers


# begin creating request
pc = portal.Context()
request = pc.makeRequestRSpec()

# declare a dedicated VM host
pnode = request.RawPC('pnode')
pnode.hardware_type = params.physical_host_type

# create nodes on dedicated host
routers = create_routers(names=['up-cl', 'external-dn', 'internal-dn'])
UEs = create_UEs(count=1, prefix=1)

# set up the UE to UP-CL connection
LAN1 = request.LAN("LAN1")
LAN1.addInterface(routers['up-cl'].addInterface())
for UE in UEs:
    if UE is not None:
        LAN1.addInterface(UE.addInterface())

# set up router links
external_dn_link = request.Link(members=[routers['up-cl'], routers['external-dn']])
internal_dn_link = request.Link(members=[routers['up-cl'], routers['internal-dn']])

# output request
pc.printRequestRSpec(request)
