from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import HANDSHAKE_DISPATCHER
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet
from ryu.controller import dpset
from ryu.ofproto import ofproto_v1_3

import random


class ModStatusApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ModStatusApp, self).__init__(*args, **kwargs)
        self.gen_id = 0
        self.role_string_list = ['nochange', 'equal', 'master', 'slave', 'unknown']

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def on_packet_in(self, ev):
        msg = ev.msg
        pkt = packet.Packet(msg.data)

        print 'get a packet: %s' % (pkt)

    @set_ev_cls(dpset.EventDP, MAIN_DISPATCHER)
    def on_dp_change(self, ev):

        if ev.enter:
            dp = ev.dp
            dpid = dp.id
            ofp = dp.ofproto
            ofp_parser = dp.ofproto_parser

            print 'dp entered, id is %s' % (dpid)
            self.send_role_request(dp, ofp.OFPCR_ROLE_EQUAL, self.gen_id)

    @set_ev_cls(ofp_event.EventOFPErrorMsg,
                [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def on_error_msg(self, ev):
        msg = ev.msg
        print 'receive a error message: %s' % (msg)

    @set_ev_cls(ofp_event.EventOFPRoleReply, MAIN_DISPATCHER)
    def on_role_reply(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        role = msg.role

        # unknown role
        if role < 0 or role > 3:
            role = 4
        print ''
        print 'get a role reply: %s, generation: %d' % (self.role_string_list[role], msg.generation_id)

        # generate new generation id
        self.gen_id = random.randint(0, 10000)

        if role == ofp.OFPCR_ROLE_EQUAL:
            print 'now is equal, change to master'
            self.send_role_request(dp, ofp.OFPCR_ROLE_MASTER, self.gen_id)
        elif role == ofp.OFPCR_ROLE_MASTER:
            print 'now is master, change to slave'
            self.send_role_request(dp, ofp.OFPCR_ROLE_SLAVE, self.gen_id)
        elif role == ofp.OFPCR_ROLE_SLAVE:
            print 'now is slave, change to equal'
            self.send_role_request(dp, ofp.OFPCR_ROLE_EQUAL, self.gen_id)
        print ''

    def send_role_request(self, datapath, role, gen_id):
        ofp_parser = datapath.ofproto_parser
        print 'send a role change request'
        print 'role: %s, gen_id: %d' % (self.role_string_list[role], gen_id)
        msg = ofp_parser.OFPRoleRequest(datapath, role, gen_id)
        datapath.send_msg(msg)
