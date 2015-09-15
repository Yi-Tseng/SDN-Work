#!/usr/bin/env python

from mininet.cli import CLI
from mininet.node import Link
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.term import makeTerm
from functools import partial


def ofp_version(switch, protocols):
    protocols_str = ','.join(protocols)
    command = 'ovs-vsctl set Bridge %s protocols=%s' % (switch, protocols)
    switch.cmd(command.split(' '))

if '__main__' == __name__:
    net = Mininet(controller=partial(RemoteController, ip='10.42.0.27', port=6633))
    c0 = net.addController('c0')
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')
    s4 = net.addSwitch('s4')
    s5 = net.addSwitch('s5')
    s6 = net.addSwitch('s6')

    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    h3 = net.addHost('h3')
    h4 = net.addHost('h4')

    net.addLink(s1, h1)
    net.addLink(s2, h2)
    net.addLink(s5, h3)
    net.addLink(s6, h4)

    net.addLink(s1, s2)
    net.addLink(s2, s3)
    net.addLink(s2, s4)
    net.addLink(s4, s5)
    net.addLink(s4, s6)

    net.build()
    c0.start()
    s1.start([c0])
    s2.start([c0])
    s3.start([c0])
    s4.start([c0])
    s5.start([c0])
    s6.start([c0])

    ofp_version(s1, ['OpenFlow13'])
    ofp_version(s2, ['OpenFlow13'])
    ofp_version(s3, ['OpenFlow13'])
    ofp_version(s4, ['OpenFlow13'])
    ofp_version(s5, ['OpenFlow13'])
    ofp_version(s6, ['OpenFlow13'])

    CLI(net)

    net.stop()
