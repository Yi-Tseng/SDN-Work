import os
from mininet.topo import Topo
from mininet.node import Host, RemoteController, OVSSwitch

'''
Topology:
    red1  -`                             ,- red2
            +--- ovs1 -- tor -- ovs2 ---+
    blue1 -,                             `- blue2

IP of ovs1 is 192.168.10.1, ovs2 is 192.168.20.1
Use ovs as vtep
'''


class VXLANTopo(Topo):

    def __init__(self):
        Topo.__init__(self)
        tor = self.addSwitch('tor',
                             dpid='0000000000000010',
                             cls=OVSSwitch, failMode="standalone")
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        red1 = self.addHost('red1')
        red2 = self.addHost('red2')
        blue1 = self.addHost('blue1')
        blue2 = self.addHost('blue2')

        self.addLink(red1, s1)
        self.addLink(blue1, s1)

        self.addLink(red2, s2)
        self.addLink(blue2, s2)


if __name__ == '__main__':
    setLogLevel('debug')
    topo = VXLANTopo()

    net = Mininet(topo=topo, controller=None)

    net.start()
    c0 = net.addController(name='c0',
                           controller=RemoteController,
                           ip='127.0.0.1', port=6633)

    net.get('s1').start([c0])
    net.get('s2').start([c0])
    os.popen('ip addr add 192.168.10.1/16 dev s1')
    os.popen('ip addr add 192.168.20.1/16 dev s2')

    CLI(net)
    net.stop()
