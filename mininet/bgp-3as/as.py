#!/usr/bin/env python
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel

'''
h1 -- r1 -- r2 -- r3 -- h3
            |
            h2
h1 - r1 : 10.0.1.0/24
h2 - r2 : 10.0.2.0/24
h3 - r3 : 10.0.3.0/24

r1 - r2 : 192.168.1.0/24
r2 - r3 : 192.168.2.0/24
'''

if '__main__' == __name__:
    setLogLevel('debug')
    net = Mininet(controller=None)
    h1 = net.addHost('h1', ip="10.0.1.1/24")
    h2 = net.addHost('h2', ip="10.0.2.1/24")
    h3 = net.addHost('h3', ip="10.0.3.1/24")

    r1 = net.addHost('r1')
    r2 = net.addHost('r2')
    r3 = net.addHost('r3')

    net.addLink(r1, r2)
    net.addLink(r2, r3)

    net.addLink(h1, r1)
    net.addLink(h2, r2)
    net.addLink(h3, r3)

    net.build()
    # default route for hosts
    h1.cmd('ip r add 0.0.0.0/0 via 10.0.1.254')
    h2.cmd('ip r add 0.0.0.0/0 via 10.0.2.254')
    h3.cmd('ip r add 0.0.0.0/0 via 10.0.3.254')

    # remove default ip address
    r1.cmd('ip a del 10.0.0.4/8 dev r1-eth0')
    r2.cmd('ip a del 10.0.0.5/8 dev r2-eth0')
    r3.cmd('ip a del 10.0.0.6/8 dev r3-eth0')

    # ip for router facing hosts
    r1.cmd('ip a add 10.0.1.254/24 dev r1-eth1')
    r2.cmd('ip a add 10.0.2.254/24 dev r2-eth2')
    r3.cmd('ip a add 10.0.3.254/24 dev r3-eth1')

    # subnet between r1 and r2
    r1.cmd('ip a add 192.168.1.1/24 dev r1-eth0')
    r2.cmd('ip a add 192.168.1.2/24 dev r2-eth0')

    # subnet between r2 and r3
    r2.cmd('ip a add 192.168.2.1/24 dev r2-eth1')
    r3.cmd('ip a add 192.168.2.2/24 dev r3-eth0')

    # quagga
    r1.cmd('/usr/lib/quagga/zebra -d -f zebra-r1.conf -z /var/run/quagga/zebra-r1.api -i /var/run/quagga/zebra-r1.pid')
    r1.cmd('/usr/lib/quagga/bgpd -d -f r1.conf -z /var/run/quagga/zebra-r1.api -i /var/run/quagga/bgpd-r1.pid')

    r2.cmd('/usr/lib/quagga/zebra -d -f zebra-r2.conf -z /var/run/quagga/zebra-r2.api -i /var/run/quagga/zebra-r2.pid')
    r2.cmd('/usr/lib/quagga/bgpd -d -f r2.conf -z /var/run/quagga/zebra-r2.api -i /var/run/quagga/bgpd-r2.pid')

    r3.cmd('/usr/lib/quagga/zebra -d -f zebra-r3.conf -z /var/run/quagga/zebra-r3.api -i /var/run/quagga/zebra-r3.pid')
    r3.cmd('/usr/lib/quagga/bgpd -d -f r3.conf -z /var/run/quagga/zebra-r3.api -i /var/run/quagga/bgpd-r3.pid')

    CLI(net)

    # kill bgpd and zebra
    r1.cmd('killall bgpd zebra')
    r2.cmd('killall bgpd zebra')
    r3.cmd('killall bgpd zebra')
    net.stop()
