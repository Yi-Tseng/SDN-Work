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
    net = Mininet(controller=RemoteController)
    c0 = net.addController('c0')

    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')
    s4 = net.addSwitch('s4')
    s5 = net.addSwitch('s5')
    s6 = net.addSwitch('s6')
    s7 = net.addSwitch('s7')
    s8 = net.addSwitch('s8')

    net.addLink(s1, s2)
    net.addLink(s2, s3)
    net.addLink(s3, s4)
    net.addLink(s4, s1)

    net.addLink(s2, s5)
    net.addLink(s3, s6)
    net.addLink(s5, s6)

    net.addLink(s5, s7)
    net.addLink(s6, s8)
    net.addLink(s7, s8)

    net.build()
    c0.start()
    s1.start([c0])
    s2.start([c0])
    s3.start([c0])
    s4.start([c0])
    s5.start([c0])
    s6.start([c0])
    s7.start([c0])
    s8.start([c0])

    ofp_version(s1, ['OpenFlow13'])
    ofp_version(s2, ['OpenFlow13'])
    ofp_version(s3, ['OpenFlow13'])
    ofp_version(s4, ['OpenFlow13'])
    ofp_version(s5, ['OpenFlow13'])
    ofp_version(s6, ['OpenFlow13'])
    ofp_version(s7, ['OpenFlow13'])
    ofp_version(s8, ['OpenFlow13'])

    CLI(net)
    net.stop()
