#!/usr/bin/python

# This file is fork from p4factory/mininet/swl_l2.py

##############################################################################
# Topology with two switches and two hosts (static macs, no loops, no STP)
#
#                      172.16.10.0/24
#  h1 -------- sw1(p4) -------------- sw2(ovs)  --------h2
#  .1                                                   .2
##############################################################################

from mininet.net import Mininet, VERSION
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from distutils.version import StrictVersion
from p4_mininet import P4DockerSwitch
from time import sleep
import sys

def main():
    net = Mininet( controller = None )

    # add hosts
    h1 = net.addHost( 'h1', ip = '172.16.10.1/24' )
    h2 = net.addHost( 'h2', ip = '172.16.10.2/24' )

    # add switch 1
    sw1 = net.addSwitch( 'sw1', target_name = "p4dockerswitch",
            cls = P4DockerSwitch, config_fs = './startup_config.sh',
            pcap_dump = True )

    # add switch 2
    sw2 = net.addSwitch('sw2')

    # add links
    if StrictVersion(VERSION) <= StrictVersion('2.2.0') :
        net.addLink( sw1, h1, port1 = 1 )
        net.addLink( sw1, sw2, port1 = 2, port2 = 2 )
        net.addLink( sw2, h2, port1 = 1 )
    else:
        net.addLink( sw1, h1, port1 = 1, fast=False )
        net.addLink( sw1, sw2, port1 = 2, port2 = 2, fast=False )
        net.addLink( sw2, h2, port1 = 1, fast=False )

    net.start()
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    main()

