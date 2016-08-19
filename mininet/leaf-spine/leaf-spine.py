#!/usr/bin/env python

from mininet.cli import CLI
from mininet.node import Link
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.term import makeTerm
from functools import partial



if '__main__' == __name__:
    net = Mininet()
    num_spine = 2
    num_leaf = 2

    spine_switches = []
    leaf_switches = []

    for i in range(num_spine):
        name = 's1%02d' % (i)
        sw = net.addSwitch(name)
        spine_switches.append(sw)

    for i in range(num_leaf):
        name = 's2%02d' % (i)
        sw = net.addSwitch(name)
        leaf_switches.append(sw)

    for ss in spine_switches:
        for ls in leaf_switches:
            net.addLink(ss, ls)

    hid = 0
    for ls in leaf_switches:
        h1 = net.addHost('h%03d' % (hid, ))
        h2 = net.addHost('h%03d' % (hid + 1, ))
        hid += 2
        net.addLink(ls, h1)
        net.addLink(ls, h2)

    c0 = RemoteController('c0', '127.0.0.1', 6653)
    net.build()
    c0.start()

    for ss in spine_switches:
        ss.start([c0])

    for ls in leaf_switches:
        ls.start([c0])

    CLI(net)

    net.stop()
