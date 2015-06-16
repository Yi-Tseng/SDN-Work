# -*- coding: utf-8 -*-
import logging

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
        self.global_port = {}
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):

        msg = ev.msg
        datapath = msg.datapath
        try:
            # src: from other switch
            src_dpid, src_port_no = LLDPPacket.lldp_parse(msg.data)
            # dst: this switch
            dst_dpid, dst_port_no = datapath.dpid, msg.match['in_port']
            switch = api.get_switch(src_dpid)[0]

            # not this topology switch
            if switch != None:
                return

            # send cross domain link add
            self.local_lib.send_cross_domain_link(dst_dpid, dst_port_no, src_dpid, src_port_no)

            # add global port
            self.global_port[dst_dpid].set_default([])
            self.global_port[dst_dpid].append(dst_port_no)

            return
        except LLDPPacket.LLDPUnknownFormat as e:
            # This handler can receive all the packtes which can be
            # not-LLDP packet. Ignore it silently
            pass

        # non-LLDP

    @set_ev_cls(local_lib.EventRouteResult, MAIN_DISPATCHER)
    def route_result_handler(self, ev):
        pass

    @set_ev_cls(local_lib.EventAskDpid, MAIN_DISPATCHER)
    def ask_dpid_handler(self, ev):
        pass

    @set_ev_cls(local_lib.EventAskHost, MAIN_DISPATCHER)
    def ask_host_handler(self, ev):
        pass

    @set_ev_cls(local_lib.EventHostDiscovery, MAIN_DISPATCHER)
    def host_discovery_handler(self, ev):
        pass
