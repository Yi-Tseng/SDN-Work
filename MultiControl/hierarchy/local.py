# -*- coding: utf-8 -*-
import logging
import networkx as nx
from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.topology import api
from ryu.topology.switches import LLDPPacket
from ryu.lib.packet import packet, ethernet
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER

import local_lib


LOG = logging.getLogger('local_app')
OFPPC_NO_FLOOD = 1 << 4

class LocalControllerApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    


    def __init__(self, *args, **kwargs):
        super(LocalControllerApp, self).__init__(*args, **kwargs)
        self.local_lib = local_lib.LocalControllerLib('127.0.0.1', 10807)
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
            dst_dpid, dst_port_no = datapath.id, msg.match['in_port']

            if int(src_dpid) > 1024 or int(dst_dpid) > 1024:
                # hack: ignote illegal switch
                return

            switch = api.get_switch(self, str(src_dpid))

            # not this topology switch
            if len(switch) != 0:
                return

            # send cross domain link add
            LOG.info('Sending cross doamin link from %s:%d to %s:%d', src_dpid, src_port_no, dst_dpid, dst_port_no)
            self.local_lib.send_cross_domain_link(dst_dpid, dst_port_no, src_dpid, src_port_no)

            # add global port
            self.global_port.setdefault(dst_dpid, [])
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

        # host[0] -> dpid
        # host[1] -> port
        if host[0] == dpid:
            # same switch
            out_port = host[1]
            self._packet_out(msg, out_port)

        else:
            # not same switch
            # calculate path
            self._packet_out_to(msg, host[0], host[1])


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

    def _packet_out_to(self, msg, dst_dpid, dst_out_port):
        dp = msg.datapath
        src_dpid = int(dp.id)

        # same dp
        if src_dpid == dst_dpid:
            self._packet_out(msg, dst_out_port)

        else:
            g = nx.Graph()
            links = api.get_all_link(self)

            for link in links:
                src = int(link.src.dpid)
                dst = int(link.dst.dpid)
                g.add_edge(src, dst)
            src = int(src_dpid)
            dst = int(dst_dpid)
            path = None

            if nx.has_path(g, src, dst):
                path = nx.shortest_path(g, src, dst)

            if path == None:
                return
            out_port = self._get_out_port(path[0], path[1])
            self._packet_out(msg, out_port)

    @set_ev_cls(local_lib.EventRouteResult, MAIN_DISPATCHER)
    def route_result_handler(self, ev):
        dpid = ev.dpid
        port = ev.port
        host = ev.host
        remove_list = []
        if dpid == -1:
            # global routing failed
            # do broad cast
            
            for route_req in self.route_list:

                if route_req[0] != host:
                    continue
                self._flood_packet(route_req[1])
                remove_list.append(route_req)

        else:
            # global routing not failed
            pass

        for remove_item in remove_list:

            try:
                index = self.route_list.index(remove_item)
                del self.route_list[index]

            except ValueError:
                pass

    @set_ev_cls(local_lib.EventAskDpid, MAIN_DISPATCHER)
    def ask_dpid_handler(self, ev):
        dpid = ev.dpid
        switch = api.get_switch(self, str(dpid))

        if len(switch) != 0:
            self.local_lib.response_dpid(dpid)


    @set_ev_cls(local_lib.EventAskHost, MAIN_DISPATCHER)
    def ask_host_handler(self, ev):
        host_mac = ev.host

        if host_mac in self.local_lib.hosts:
            self.local_lib.response_host(host_mac)

    @set_ev_cls(local_lib.EventHostDiscovery, MAIN_DISPATCHER)
    def host_discovery_handler(self, ev):
        LOG.info('Discover host %s on %s, port %d', ev.host, ev.dpid, ev.port)
        self.local_lib.response_host(ev.host)



