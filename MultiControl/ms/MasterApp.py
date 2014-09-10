'''
Master App, testing for master controller
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
from threading import Thread
import socket
import time

class MasterApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    def __init__(self, *args, **kwargs):
        super(MasterApp, self).__init__(*args, **kwargs)
        print 'prepare server'
        master_server = MasterServer(7999)
        print 'starting server'
        master_server.start()
        print 'echo server started'

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
            self.send_role_request(dp, ofp.OFPCR_ROLE_MASTER, 0)


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


class ServerTask(Thread):

    def __init__(self, server, client_socket):
        Thread.__init__(self)
        self.server = server
        self.client_socket = client_socket

    def run(self):
        try:
            while True:
                self.client_socket.send('hello')
                client_data = self.client_socket.recv(1024)
                # print 'from client: %s' % (client_data)
                time.sleep(1)
        except Exception, e:
            print 'client break'
            client_sockets = self.server.client_sockets
            client_socket = self.client_socket
            client_sockets.remove(client_socket)
            print e

class MasterServer(Thread):
    '''
    server for master, shows that it is alive
    '''
    def __init__(self, port):
        Thread.__init__(self)
        self.client_sockets = []
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server_socket.bind(('127.0.0.1', port))

    def run(self):

        self.server_socket.listen(5)
        while True:
            (client_socket, addr) = self.server_socket.accept()
            self.client_sockets.append(client_socket)
            server_task = ServerTask(self, client_socket)
            server_task.start()

