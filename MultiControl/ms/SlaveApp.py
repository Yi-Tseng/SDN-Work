'''
Slave App, testing for slave controller
'''
# -*- encoding: utf-8 -*-
# file: MasterApp.py

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import HANDSHAKE_DISPATCHER
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet
from ryu.controller import dpset
from ryu.ofproto import ofproto_v1_3
import socket
from threading import Thread


class SlaveApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    def __init__(self, *args, **kwargs):
        super(SlaveApp, self).__init__(*args, **kwargs)
        self.datapaths = []
        print 'preparing echo client'
        echo_client = ClientThread('127.0.0.1', 7999, self)
        print 'starting echo client...'
        echo_client.start()
        print 'echo client started'

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def on_packet_in(self, ev):
        msg = ev.msg
        pkt = packet.Packet(msg.data)
        #print 'get a packet: %s' % (pkt)

    @set_ev_cls(dpset.EventDP, MAIN_DISPATCHER)
    def on_dp_change(self, ev):

        if ev.enter:
            dp = ev.dp
            dpid = dp.id
            ofp = dp.ofproto
            ofp_parser = dp.ofproto_parser
            self.datapaths.append(dp)

            print 'dp entered, id is %s' % (dpid)
            self.send_role_request(dp, ofp.OFPCR_ROLE_SLAVE, 0)


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
        gen_id = msg.generation_id

        if role == ofp.OFPCR_ROLE_EQUAL:
            print 'now is equal'
        elif role == ofp.OFPCR_ROLE_MASTER:
            print 'now is master'
        elif role == ofp.OFPCR_ROLE_SLAVE:
            print 'now is slave'
        print ''

    def send_role_request(self, datapath, role, gen_id):
        ofp_parser = datapath.ofproto_parser
        msg = ofp_parser.OFPRoleRequest(datapath, role, gen_id)
        datapath.send_msg(msg)

    def on_master_down(self):
        print 'master is down, trying to change priority to master'
        for dp in self.datapaths:
            ofp = dp.ofproto
            self.send_role_request(dp, ofp.OFPCR_ROLE_MASTER, 0)



class ClientThread(Thread):

    def __init__(self, master_ip, master_port, slave_app):
        Thread.__init__(self)
        self.master_ip = master_ip
        self.master_port = master_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.slave_app = slave_app

    def run(self):
        c_socket = self.client_socket
        ip = self.master_ip
        port = self.master_port
        c_socket.connect((ip, port))
        try:
            while True:
                master_data = c_socket.recv(1024)
                # print 'receive master message: %s' % (master_data)
                c_socket.send('hello')
        except Exception, e:
            self.slave_app.on_master_down()
