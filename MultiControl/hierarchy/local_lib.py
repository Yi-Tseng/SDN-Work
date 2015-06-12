# -*- coding: utf-8 -*-
import socket
import logging
import json

from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
from ryu.controller import event


class EventRouteResult(event.EventBase):

    def __init__(self, dpid, port, host):
        super(EventRouteResult, self).__init__()
        self.dpid = dpid
        self.port = port
        self.host = host

class EventAskDpid(event.EventBase):

    def __init__(self, dpid):
        super(EventAskDpid, self).__init__()
        self.dpid = dpid

LOG = logging.getLogger('local_lib')
class EventAskHost(event.EventBase):

    def __init__(self, host):
        '''
        host: host mac address
        '''
        super(EventAskHost, self).__init__()
        self.host = host


class LocalControllerLib(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, server_addr, server_port, *args, **kwargs):
        super(LocalControllerLib, self).__init__(*args, **kwargs)
        self.agent_id = -1
        self.server_addr = server_addr
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start_serve(self):

        try:
            self.socket.connect((self.server_addr, self.server_port))
            hub.spawn(self._serve_loop)
        except Exception, ex:
            raise ex

    def _serve_loop(self):
        
        while True:
            buf = self.socket.recv(128)
            msg = json.dumps(buf)
            ev = None

            if msg['cmd'] == 'set_agent_id':
                self.agent_id = msg['agent_id']

            elif msg['cmd'] == 'ask_host':
                host = msg['host']
                ev = EventAskHost(host)

            elif msg['cmd'] == 'ask_dpid':
                dpid = msg['dpid']
                ev = EventAskDpid(dpid)

            elif msg['cmd'] == 'route_result':
                dpid = msg['dpid']
                port = msg['port']
                host = msg['host']
                ev = EventRouteResult(dpid, port, host)

            if ev != None:
                self.send_event_to_observers(ev)                


    def send_cross_domain_link(self, local_dpid, local_port, out_dpid, out_port):
        pass

    def response_host(self, host_mac):
        pass

    def response_dpid(self, dpid):
        pass

    def get_route(self, dst_mac):
        pass
