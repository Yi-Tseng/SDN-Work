#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info, debug
from mininet.node import Host, RemoteController

# Must exist and be owned by quagga user (quagga:quagga by default on Ubuntu)
QUAGGA_RUN_DIR = '/var/run/quagga'
QCONFIG_DIR = 'configs'
ZCONFIG_DIR = 'configs'


class SdnIpHost(Host):
    def __init__(self, name, ip, route, *args, **kwargs):
        Host.__init__(self, name, ip=ip, *args, **kwargs)

        self.route = route

    def config(self, **kwargs):
        Host.config(self, **kwargs)

        debug("configuring route %s" % self.route)

        self.cmd('ip route add default via %s' % self.route)


class Router(Host):
    def __init__(self, name, quaggaConfFile, zebraConfFile, intfDict, *args, **kwargs):
        Host.__init__(self, name, *args, **kwargs)

        self.quaggaConfFile = quaggaConfFile
        self.zebraConfFile = zebraConfFile
        self.intfDict = intfDict

    def config(self, **kwargs):
        Host.config(self, **kwargs)
        self.cmd('sysctl net.ipv4.ip_forward=1')

        for intf, attrs in self.intfDict.items():
            self.cmd('ip addr flush dev %s' % intf)

            # setup mac address to specific interface
            if 'mac' in attrs:
                self.cmd('ip link set %s down' % intf)
                self.cmd('ip link set %s address %s' % (intf, attrs['mac']))
                self.cmd('ip link set %s up ' % intf)

            # setup address to interfaces
            for addr in attrs['ipAddrs']:
                self.cmd('ip addr add %s dev %s' % (addr, intf))

        self.cmd('zebra -d -f %s -z %s/zebra%s.api -i %s/zebra%s.pid' % (self.zebraConfFile, QUAGGA_RUN_DIR, self.name, QUAGGA_RUN_DIR, self.name))
        self.cmd('bgpd -d -f %s -z %s/zebra%s.api -i %s/bgpd%s.pid' % (self.quaggaConfFile, QUAGGA_RUN_DIR, self.name, QUAGGA_RUN_DIR, self.name))

    def terminate(self):
        self.cmd("ps ax | egrep 'bgpd%s.pid|zebra%s.pid' | awk '{print $1}' | xargs kill" % (self.name, self.name))

        Host.terminate(self)


class SdnIpTopo(Topo):

    def build(self):
        zebraConf = '{}/zebra.conf'.format(ZCONFIG_DIR)

        s1 = self.addSwitch('s1', dpid='0000000000000001', failMode="standalone")

        # Quagga 1
        bgpEth0 = {
            'mac': '00:00:00:00:00:01',
            'ipAddrs': [
                '10.0.1.1/24',
            ]
        }

        bgpIntfs = {
            'bgp-q1-eth0': bgpEth0
        }

        bgpq1 = self.addHost("bgp-q1", cls=Router,
                             quaggaConfFile='{}/quagga1.conf'.format(QCONFIG_DIR),
                             zebraConfFile=zebraConf,
                             intfDict=bgpIntfs)

        self.addLink(bgpq1, s1)

        # Quagga 2
        bgpEth0 = {
            'mac': '00:00:00:00:00:02',
            'ipAddrs': [
                '10.0.2.1/24',
            ]
        }

        bgpIntfs = {
            'bgp-q2-eth0': bgpEth0
        }

        bgpq2 = self.addHost("bgp-q2", cls=Router,
                             quaggaConfFile='{}/quagga2.conf'.format(QCONFIG_DIR),
                             zebraConfFile=zebraConf,
                             intfDict=bgpIntfs)

        self.addLink(bgpq2, s1)


topos = {'sdnip': SdnIpTopo}

if __name__ == '__main__':
    setLogLevel('debug')
    topo = SdnIpTopo()

    net = Mininet(topo=topo)

    net.start()

    CLI(net)

    net.stop()

    info("done\n")
