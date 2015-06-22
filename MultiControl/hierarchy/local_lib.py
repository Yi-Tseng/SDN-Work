# -*- coding: utf-8 -*-
import socket
import logging
import json


from ryu.base import app_manager
from ryu.controller import event
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.topology import api
from ryu.lib.packet import packet, ethernet
from ryu.ofproto import ofproto_v1_0, ofproto_v1_2, ofproto_v1_3
from ryu.lib import hub
from ryu.topology.switches import LLDPPacket

LOG = logging.getLogger(__name__)

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


class EventAskHost(event.EventBase):

    def __init__(self, host):
        '''
        host: host mac address
        '''
        super(EventAskHost, self).__init__()
        self.host = host

class EventHostDiscovery(event.EventBase):

    def __init__(self, dpid, port, host):
        super(EventHostDiscovery, self).__init__()
        self.dpid = dpid
        self.port = port
        self.host = host

LOG = logging.getLogger('local_lib')
class LocalControllerLib(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(LocalControllerLib, self).__init__(*args, **kwargs)
        self.name = 'local_lib'
        self.server_addr = None
        self.server_port = None
        self.is_active = False
        self.agent_id = -1
        self.send_q = hub.Queue(16)
        self.hosts = {}
        self.cross_domain_links = []
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        try:
            msg = ev.msg
            LLDPPacket.lldp_parse(msg.data)
            return
        except LLDPPacket.LLDPUnknownFormat:
            # it's host
            dpid = msg.datapath.id
            port = -1

            if msg.datapath.ofproto.OFP_VERSION == ofproto_v1_0.OFP_VERSION:
                port = msg.in_port
            elif msg.datapath.ofproto.OFP_VERSION >= ofproto_v1_2.OFP_VERSION:
                port = msg.match['in_port']

            if port >= 1024:
                # hack: ignore some strange port
                return

            # ignore global host
            for link in self.cross_domain_links:

                if link['src']['dpid'] == dpid and \
                    link['src']['port'] == port:
                    return

            # TODO, check again if host already in global port

            pkt = packet.Packet(msg.data)
            eth = pkt.get_protocols(ethernet.ethernet)[0]
            mac = eth.src

            if mac not in self.hosts and port != -1 and \
                not self._host_exist_in_port(dpid, port) and \
                not self._is_switch_port_to_port(dpid, port):
                LOG.debug('Add host %s to %d:%d', mac, dpid, port)
                self.hosts[mac] = (dpid, port)
                self.response_host(mac)
                ev = EventHostDiscovery(dpid, port, mac)
                self.send_event_to_observers(ev)

    def _is_switch_port_to_port(self, dpid, port):
        links = api.get_all_link(self)

        for link in links:

            if link.src.dpid == dpid and \
                link.src.port_no == port:
                return True

        return False

    def _host_exist_in_port(self, dpid, port):

        for (d, p) in self.hosts.itervalues():
            if d == dpid and p == port:
                return True

        return False

    def start_serve(self, server_addr, server_port):

        try:
            self.server_addr = server_addr
            self.server_port = server_port
            self.socket.connect((self.server_addr, self.server_port))
            self.is_active = True
            hub.spawn(self._serve_loop)
            hub.spawn(self._send_loop)

        except Exception, ex:
            raise ex

    def _send_loop(self):

        try:

            while self.is_active:
                buf = self.send_q.get()
                buf += '\n'
                self.socket.sendall(buf)

        finally:
            q = self.send_q
            self.send_q = None

            try:

                while q.get(block=False):
                    pass

            except hub.QueueEmpty:
                pass

    def _serve_loop(self):
        
        while self.is_active:
            buf = self.socket.recv(128)

            if len(buf) == 0:
                LOG.info('connection fail, close')
                self.is_active = False
                break
            LOG.debug('Receive: %s', buf)
            try:
                msg = json.loads(buf)
            except ValueError:
                LOG.warning('Error to decode to json: %s', buf)
                continue

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

    def send(self, msg):

        if self.send_q != None:
            self.send_q.put(msg)

    def send_cross_domain_link(self, local_dpid, local_port, out_dpid, out_port):

        link = {
            'src': {'dpid': local_dpid, 'port': local_port},
            'dst': {'dpid': out_dpid, 'port': out_port}
        }

        if link in self.cross_domain_links:
            return
        self.cross_domain_links.append(link)
        msg = json.dumps({
            'cmd': 'add_cross_domain_link',
            'src': {'dpid': local_dpid, 'port': local_port},
            'dst': {'dpid': out_dpid, 'port': out_port}
            })
        LOG.info('Sending cross doamin link from %s:%d to %s:%d', local_dpid, local_port, out_dpid, out_port)
        self.send(msg)

    def response_host(self, host_mac):
        msg = json.dumps({
            'cmd': 'response_host',
            'host': host_mac
        })
        LOG.debug('Sending response host %s', host_mac)
        self.send(msg)

    def response_dpid(self, dpid):
        msg = json.dumps({
            'cmd': 'response_dpid',
            'dpid': dpid
        })
        LOG.debug('Sending response dpid %d', dpid)
        self.send(msg)

    def get_route(self, dst_mac):
        msg = json.dumps({
            'cmd': 'get_route',
            'dst': dst_mac
        })
        LOG.debug('Sending get route %s', dst_mac)
        self.send(msg)

