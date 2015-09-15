#!/usr/bin/env python

from mininet.cli import CLI
from mininet.link import Link
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch


def ofp_version(switch, protocols):
    protocols_str = ','.join(protocols)
    command = 'ovs-vsctl set Bridge %s protocols=%s' % (switch, protocols_str)
    switch.cmd(command.split(' '))


if '__main__' == __name__:
    net = Mininet(switch=OVSSwitch)

    c0 = RemoteController('c0', '127.0.0.1', 6633)
    c1 = RemoteController('c1', '127.0.0.1', 6632)
    net.addController(c0)
    net.addController(c1)

    s1 = net.addSwitch('s1')

    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    h3 = net.addHost('h3')

    Link(s1, h1)
    Link(s1, h2)
    Link(s1, h3)

    net.build()

    c0.start()
    c1.start()
    s1.start([c0, c1])

    ofp_version(s1, ['OpenFlow13'])

    CLI(net)

    net.stop()
