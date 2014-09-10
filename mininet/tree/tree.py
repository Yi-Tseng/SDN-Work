#!/usr/bin/env python

from mininet.cli import CLI
from mininet.link import Link
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.term import makeTerm
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

  h1 = net.addHost('h1')
  h2 = net.addHost('h2')
  h3 = net.addHost('h3')
  h4 = net.addHost('h4')

  Link(s1, h1)
  Link(s2, h2)
  Link(s5, h3)
  Link(s6, h4)

  Link(s1, s2)
  Link(s2, s3)
  Link(s2, s4)
  Link(s4, s5)
  Link(s4, s6)

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


