import networkx as nx

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.topology import api as ryu_api


class RouteApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(RouteApp, self).__init__(*args, **kwargs)

    def add_flow(self, datapath, match, actions):
        ofproto = datapath.ofproto

        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofproto.OFP_DEFAULT_PRIORITY,
            flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
        datapath.send_msg(mod)

    def find_host(self, mac_addr):
        hosts = ryu_api.get_all_host(self)
        for host in hosts:
            if host.mac == mac_addr:
                return host

        return None

    def flood_packet(self, dp, msg):
        ofproto = dp.ofproto
        out_port = ofproto.OFPP_FLOOD
        actions = [dp.ofproto_parser.OFPActionOutput(out_port)]
        data = None

        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = dp.ofproto_parser.OFPPacketOut(
            datapath=dp, buffer_id=msg.buffer_id, in_port=msg.in_port,
            actions=actions, data=data)
        dp.send_msg(out)

    def get_all_links(self):
        '''
        link form format:
        [(a.1, b.1), (b.2, c.1), (b.3, d.1)]
        x.k means dpid x and port no k
        a.1 means first port in switch "a"
        this topology should looks like:
        a.1 - 1.b.2 - 1.c
                3
                |
                1
                d

        '''

        all_links = ryu_api.get_all_link(self)
        result = []

        for link in all_links:
            src = '{}.{}'.format(link.src.dpid, link.src.port_no)
            dst = '{}.{}'.format(link.dst.dpid, link.dst.port_no)
            result.append((src, dst))

        # internal switch links
        all_switches = ryu_api.get_all_switch(self)
        link_to_add = []

        # O(n^3), such dirty!!
        for switch in all_switches:
            ports = switch.ports
            
            for port in ports:
                for _port in ports:
                    if port != _port:
                        src = '{}.{}'.format(port.dpid, port.port_no)
                        dst = '{}.{}'.format(_port.dpid, _port.port_no)
                        link_to_add.append((src, dst))

        result.extend(link_to_add)
        return result

    def cal_shortest_path(self, src_host, dst_host):
        src_port = src_host.port
        dst_port = dst_host.port

        all_links = self.get_all_links()

        graph = nx.Graph()
        graph.add_edges_from(all_links)

        src = '{}.{}'.format(src_port.dpid, src_port.port_no)
        dst = '{}.{}'.format(dst_port.dpid, dst_port.port_no)

        if nx.has_path(graph, src, dst):
            return nx.shortest_path(graph, src, dst)

        return None

    def get_dp(self, dpid):
        switch = ryu_api.get_switch(self, dpid)[0]
        return switch.dp

    def packet_out(self, dp, msg, out_port):
        ofproto = dp.ofproto
        actions = [dp.ofproto_parser.OFPActionOutput(out_port)]
        data = None

        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = dp.ofproto_parser.OFPPacketOut(
            datapath=dp, buffer_id=msg.buffer_id, in_port=msg.in_port,
            actions=actions, data=data)
        dp.send_msg(out)

    def install_path(self, match, path):
        for node in path:
            dpid = int(node.split('.')[0])
            port_no = int(node.split('.')[1])
            dp = self.get_dp(dpid)
            actions = [dp.ofproto_parser.OFPActionOutput(port_no)]
            self.add_flow(dp, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        dpid = dp.id
        ofproto = dp.ofproto

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        src = eth.src
        dst = eth.dst

        if dst.startswith('33:33'):
            # IP multicast, flood it....
            self.flood_packet(dp, msg)
            return

        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            # arp, flood it
            self.flood_packet(dp, msg)
            return

        if dst == 'ff:ff:ff:ff:ff:ff':
            self.flood_packet(dp, msg)
            return

        self.logger.info('From {} to {}'.format(src, dst))

        # find dst host location(dpid, port)
        dst_host = self.find_host(dst)

        # can't find dst, flood it.
        if not dst_host:
            self.logger.info('Can\'t find host {}'.format(dst))
            self.flood_packet(dp, msg)
            return

        src_host = self.find_host(src)

        # calculate shortest path
        shortest_path = self.cal_shortest_path(src_host, dst_host)

        # can't find path, flood it!
        if not shortest_path:
            self.logger.info('Can\'t find path')
            self.flood_packet(dp, msg)
            return

        self.logger.info('Shortest path : ')
        self.logger.info(shortest_path)

        # Now, insert flows to switches!
        # shortest_path example:
        # from dpid 7, port 2 to dpid 3 port 1
        # ['7.2', '7.3', '5.2', '5.3', '1.2', '1.1', '2.3', '2.1', '3.3', '3.1']

        # create match
        match = dp.ofproto_parser.OFPMatch(
            dl_dst=haddr_to_bin(dst))

        self.install_path(match, shortest_path[1::2])

        # create reverse path
        match = dp.ofproto_parser.OFPMatch(
            dl_dst=haddr_to_bin(src))

        self.install_path(match, shortest_path[2::2])

        # packet out this packet!
        node = shortest_path[1]
        dpid = int(node.split('.')[0])
        port_no = int(node.split('.')[1])
        self.packet_out(dp, msg, port_no)
        
