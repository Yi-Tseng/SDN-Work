#!/usr/bin/env python

from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch


def ofp_version(switch, protocols):
    protocols_str = ','.join(protocols)
    command = 'ovs-vsctl set Bridge %s protocols=%s' % (switch, protocols_str)
    switch.cmd(command.split(' '))


if '__main__' == __name__:
    net = Mininet(switch=OVSSwitch)


    controllers = []
    c0 = RemoteController('c0', '10.10.10.10', 6633)
    c1 = RemoteController('c1', '10.10.10.10', 6634)
    c2 = RemoteController('c2', '10.10.10.10', 6635)
    controllers.append(c0)
    controllers.append(c1)
    controllers.append(c2)

    net.addController(c0)
    net.addController(c1)
    net.addController(c2)

    switches = []
    for domain in range(0, 3):
        s1 = net.addSwitch('s%d' % (domain*3 + 1, ))
        s2 = net.addSwitch('s%d' % (domain*3 + 2, ))
        s3 = net.addSwitch('s%d' % (domain*3 + 3, ))
        net.addLink(s1, s2)
        net.addLink(s1, s3)
        h1 = net.addHost('h%d' % (domain*2 + 1, ))
        h2 = net.addHost('h%d' % (domain*2 + 2, ))
        net.addLink(s2, h1)
        net.addLink(s3, h2)
        switches.append(s1)
        switches.append(s2)
        switches.append(s3)

    # link gw sw
    net.addLink(switches[0], switches[3])
    net.addLink(switches[3], switches[6])

    net.build()

    c0.start()
    c1.start()
    c2.start()

    for domain in range(0, 3):
        switches[domain*3 + 0].start(controllers[domain])
        switches[domain*3 + 1].start(controllers[domain])
        switches[domain*3 + 2].start(controllers[domain])

    for sw in switches:
        ofp_version(sw, ['OpenFlow13'])

    CLI(net)

    net.stop()
