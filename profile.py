"""A base profile for experimenting with NDN.

Instructions:
Wait for the profile instance to start, and then log into either VM via the ssh ports specified below.
"""

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as elab


class GLOBALS(object):
    """useful constant values for setting up a powder experiment"""
    SITE_URN = "urn:publicid:IDN+emulab.net+authority+cm"
    # standard Ubuntu release
    UBUNTU18_IMG = "urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU18-64-STD"
    PNODE_D740 = "d740"  # 24 cores, 192 GB RAM TODO: figure out the proper amount of ram, docs are incorrect
    PNODE_D840 = "d840"  # 64 cores, 768 GB RAM


# define network parameters
portal.context.defineParameter("latency_external", "Latency to external data network", portal.ParameterType.LATENCY, 40.0)
portal.context.defineParameter("bandwidth_external", "Bandwidth to external data network", portal.ParameterType.BANDWIDTH, 110000.0)
portal.context.defineParameter("packet_loss_external", "Packet loss rate to external data network", portal.ParameterType.STRING, '0.0')

portal.context.defineParameter("latency_internal", "Latency to internal data network", portal.ParameterType.LATENCY, 2.0)
portal.context.defineParameter("bandwidth_internal", "Bandwidth to internal data network", portal.ParameterType.BANDWIDTH, 110000.0)
portal.context.defineParameter("packet_loss_internal", "Packet loss rate to internal data network", portal.ParameterType.STRING, '0.0')

# retrieve the values the user specifies during instantiation
params = portal.context.bindParameters()

#  check parameter validity
if params.latency_external < 0 or params.latency_internal < 0:
    portal.context.reportError(portal.ParameterError("Latency cannot be negative."))

if params.bandwidth_external < 0 or params.bandwidth_internal < 0:
    portal.context.reportError(portal.ParameterError("Bandwidth cannot be negative."))

try:
    if float(params.packet_loss_external) > 1 or float(params.packet_loss_external) < 0:
        portal.context.reportError(portal.ParameterError("Packet loss rate must be a number between 0 and 1."))
except ValueError:
    portal.context.reportError(portal.ParameterError("Packet loss rate must be a number between 0 and 1."))

try:
    if float(params.packet_loss_internal) > 1 or float(params.packet_loss_internal) < 0:
        portal.context.reportError(portal.ParameterError("Packet loss rate must be a number between 0 and 1."))
except ValueError:
    portal.context.reportError(portal.ParameterError("Packet loss rate must be a number between 0 and 1."))


def mkVM(name, image, instantiateOn, cores, ram):
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
    """Allocates and runs an install script on a specified number of VM nodes.

    Returns a list of nodes.
    """

    nodes = []
    # index nodes by their proper number (not zero-indexed)
    nodes.append(None)

    # create each VM
    for i in range(1, count + 1):
        nodes.append(mkVM('node' + str(prefix) + '-' + str(i), GLOBALS.UBUNTU18_IMG, instantiateOn=instantiateOn, cores=cores, ram=ram))

    # run client install script on each vm to install client software
    for node in nodes:
        if node is not None:
            node.addService(pg.Execute(shell="sh", command="chmod +x /local/repository/install_ndn_client.sh"))
            node.addService(pg.Execute(shell="sh", command="/local/repository/install_ndn_client.sh"))

    return nodes


def create_routers(names, instantiateOn='pnode', cores=4, ram=8):
    """Allocates and runs an install script on virtualized routers.

    Returns a list of routers.
    """

    routers = dict()

    for name in names:
        routers[name] = mkVM(name, GLOBALS.UBUNTU18_IMG, instantiateOn=instantiateOn, cores=cores, ram=ram)

        # run appropriate install scripts based on name of router
        if name == 'up_cl':
            routers['up_cl'].addService(pg.Execute(shell="sh", command="chmod +x /local/repository/setup/up_cl.sh"))
            routers['up_cl'].addService(pg.Execute(shell="sh", command="/local/repository/setup/up_cl.sh"))

        if name == 'external_dn':
            routers['external_dn'].addService(pg.Execute(shell="sh", command="chmod +x /local/repository/setup/external_dn.sh"))
            routers['external_dn'].addService(pg.Execute(shell="sh", command="/local/repository/setup/external_dn.sh"))

        if name == 'internal_dn':
            routers['internal_dn'].addService(pg.Execute(shell="sh", command="chmod +x /local/repository/setup/internal_dn.sh"))
            routers['internal_dn'].addService(pg.Execute(shell="sh", command="/local/repository/setup/internal_dn.sh"))

    return routers


# begin creating request
pc = portal.Context()
request = pc.makeRequestRSpec()

# declare a dedicated VM host
pnode = request.RawPC('pnode')
pnode.hardware_type = GLOBALS.PNODE_D740

# create nodes on dedicated host
routers = create_routers(names=['up_cl', 'external_dn', 'internal_dn'])
UEs = create_UEs(count=2, prefix=1)

# set up the UE to UP_CL connection
LAN1 = request.LAN("LAN1")
LAN1.addInterface(routers['up_cl'].addInterface())
for UE in UEs:
    if UE is not None:
        LAN1.addInterface(UE.addInterface())

# set up router links
external_dn_link = request.Link(members=[routers['up_cl'], routers['external_dn']])
internal_dn_link = request.Link(members=[routers['up_cl'], routers['internal_dn']])

# shape external link
external_dn_link.bandwidth = params.bandwidth_external
external_dn_link.latency = params.latency_external
# no exception catching is needed as validity has already been checked
external_dn_link.plr = float(params.packet_loss_external) 

# shape internal link
internal_dn_link.bandwidth = params.bandwidth_internal
internal_dn_link.latency = params.latency_internal
internal_dn_link.plr = float(params.packet_loss_internal) 

# output request
pc.printRequestRSpec(request)
