# -*- coding: utf-8 -*-
import logging
import networkx as nx
from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.topology import event
from ryu.topology import api
from ryu.topology.switches import LLDPPacket
from ryu.lib.packet import packet, ethernet, lldp
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER

import local_lib


LOG = logging.getLogger('local_app')
OFPPC_NO_FLOOD = 1 << 4

class LocalControllerApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'local_lib': local_lib.LocalControllerLib}


    def __init__(self, *args, **kwargs):
        super(LocalControllerApp, self).__init__(*args, **kwargs)
        self.local_lib = kwargs['local_lib']
        self.local_lib.start_serve()
        self.global_port = {}
        self.route_list = []
        self.graph = None
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):

        msg = ev.msg
        datapath = msg.datapath
        try:
            # src: from other switch
            src_dpid, src_port_no = LLDPPacket.lldp_parse(msg.data)
            # dst: this switch
            dst_dpid, dst_port_no = datapath.dpid, msg.match['in_port']
            switch = api.get_switch(src_dpid)

            # not this topology switch
            if len(switch) != 0:
                return

            # send cross domain link add
            self.local_lib.send_cross_domain_link(dst_dpid, dst_port_no, src_dpid, src_port_no)

            # add global port
            self.global_port[dst_dpid].set_default([])
            self.global_port[dst_dpid].append(dst_port_no)

            return
        except LLDPPacket.LLDPUnknownFormat:
            # This handler can receive all the packtes which can be
            # not-LLDP packet. Ignore it silently
            pass

        # non-LLDP
        # local routing
        dpid = datapath.id
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst = eth.dst

        if dst not in self.local_lib.hosts:
            # can't find host in local topology
            # ask global and let this msg queued
            self.route_list.append((dst, msg))
            self.local_lib.get_route(dst)
            return

        # found in local, do local routing
        # two case:
        # 1. In same switch
        # 2. Not in same switch
        host = self.local_lib.hosts[dst]

        
        if host[0] == dpid:
            # same switch
            out_port = host[1]
            self._packet_out(msg, out_port)

        else:
            # not same switch
            # calculate path
            g = nx.Graph()
            links = api.get_all_link(self)

            for link in links:
                src = int(link.src.dpid)
                dst = int(link.dst.dpid)
                g.add_edge(src, dst)
            src = int(dpid)
            dst = int(host[0])
            path = None

            if nx.has_path(g, src, dst):
                path = nx.shortest_path(g, src, dst)

            if path == None:
                return
            out_port = self._get_out_port(src, dst)
            self._packet_out(msg, out_port)

    def _get_out_port(self, src, dst):
        '''
        get output port from src switch to dst switch
        return
        '''
        links = api.get_all_link(self)

        for link in links:

            if int(link.src.dpid) == src and \
                int(link.dst.dpid) == dst:
                return int(link.src.port_no)


    def _flood_packet(self, msg):
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        data = None

        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out_port = ofproto.OFPP_FLOOD
        actions = [parser.OFPActionOutput(out_port)]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions,
                                  data=data)
        datapath.send_msg(out)

    def _packet_out(self, msg, out_port):
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        data = None

        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        actions = [parser.OFPActionOutput(out_port)]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions,
                                  data=data)
        datapath.send_msg(out)

    @set_ev_cls(local_lib.EventRouteResult, MAIN_DISPATCHER)
    def route_result_handler(self, ev):
        pass

    @set_ev_cls(local_lib.EventAskDpid, MAIN_DISPATCHER)
    def ask_dpid_handler(self, ev):
        dpid = ev.dpid
        switch = api.get_switch(str(dpid))

        if len(switch) != 0:
            self.local_lib.response_dpid(dpid)


    @set_ev_cls(local_lib.EventAskHost, MAIN_DISPATCHER)
    def ask_host_handler(self, ev):
        host_mac = ev.host

        if host_mac in self.local_lib.hosts:
            self.local_lib.response_host(host_mac)

    @set_ev_cls(local_lib.EventHostDiscovery, MAIN_DISPATCHER)
    def host_discovery_handler(self, ev):
        pass
