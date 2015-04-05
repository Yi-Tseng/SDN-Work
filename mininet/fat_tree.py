#!/usr/bin/env python
'''
Fat tree topology create by mininet
Author : Yi Tseng
'''
import logging

from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import Link, Intf, TCLink
from mininet.topo import Topo
from mininet.util import dumpNodeConnections


LOG = logging.getLogger('FatTreeTopo')

class FatTreeTopo(Topo):
    core_switches = []
    pods = []

    def __init__(self, k):
        self.num_pods = k
        self.num_cores = (k/2)**2
        self.num_aggres = (k**2)/2
        self.num_aggres_per_pod = self.num_aggres / self.num_pods
        self.num_edges = (k**2)/2
        self.num_edges_per_pod = self.num_edges / self.num_pods
        self.num_host_per_edge = k/2

        Topo.__init__(self)


    def create_core(self):
        '''
        Create core switches
        '''
        for i in range(0, self.num_cores):
            switch_name = 'C%d' % (i, )
            self.core_switches.append(self.addSwitch(switch_name))


    def create_pods(self):
        '''
        Create pods
        '''
        for pi in range(0, self.num_pods):
            pods[pi] = {'aggr': [], 'edge': []}

            # create aggregation layer
            for ai in range(0, self.num_aggres_per_pod):
                switch_name = 'P%dA%d' % (pi, ai, )
                pods[pi]['aggr'].append(self.addSwitch(switch_name))

            # create edge layer
            for ei in range(0, self.num_edges_per_pod):
                switch_name = 'P%dE%d' % (pi, ei, )
                pods[pi]['edge'].append(self.addSwitch(switch_name))

            # link aggregation and edge
            for aggr_switch in pods[pi]['aggr']:

                for edge_switch in pods[pi]['edge']:
                    self.addLink(aggr_switch, edge_switch)


    def link_core_to_pods(self):
        '''
        link aggregation layer to core layer
        aggregation switch can link to core switch directly
        pod number doesn't matter
        ex:
        k = 8
        4 aggregation switch in a pod
        A0 -> C0~C3
        A1 -> C4~C7
        A2 -> C8~C11
        A3 -> C12~C15
        '''
        num_cores_per_aggr = self.num_cores / self.num_aggres_per_pod

        for pod in self.pods:

            for ai in range(0, self.num_aggres_per_pod): # ai for aggregation index
                cis = ai * num_cores_per_aggr # start index
                cie = ai * num_cores_per_aggr + num_cores_per_aggr # end index

                for ci in range(cis, cie): # ci for core index
                    aggr_switch = pod['aggr'][ai]
                    core_switch = self.core_switches[ci]
                    self.addLink(aggr_switch, core_switch)

    def set_protocols_to_all_switch(self, protocols):

        def set_protocol(switch):
            protocols_str = ','.join(protocols)
            command = 'ovs-vsctl set Bridge %s protocols=%s' % (switch, protocols_str)
            switch.cmd(command.split(' '))

        for core_switch in self.core_switches:
            set_protocol(core_switch)
            

        for pod in self.pods:

            for aggr_switch in pod['aggr']:
                set_protocol(aggr_switch)

            for edge_switch in pod['edge']:
                set_protocol(edge_switch)

    def init_fat_tree(self):
        self.create_core()
        self.create_pods()
        self.link_core_to_pods()
        self.set_protocols_to_all_switch(['OpenFlow13'])

if __name__ == '__main__':
    fat_tree = FatTreeTopo()
    fat_tree.init_fat_tree()
    net = Mininet(topo=fat_tree)
    net.addController('controller', controller=RemoteController, ip='127.0.0.1',port=6633)
    net.start()
 
    CLI(net)
    net.stop() 
