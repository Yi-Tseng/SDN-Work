import networkx as nx
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.topology import api as ryu_api

class FastFailover(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    DEFAULT_FLOW_PRIORITY = 32767
    DEFAULT_BUCKET_WEIGHT = 10

    def __init__(self, *args, **kwargs):
        super(FastFailover, self).__init__()
        self.hosts = {}
        self.num_groups = 0
        self.mac_to_gid = {}
        self.gid_to_mac = {}

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def get_dp(self, dpid):
        switches = ryu_api.get_all_switch(self)

        for switch in switches:
            if switch.dp.id == dpid:
                return switch.dp

        return None

    def get_nx_graph(self):
        links = ryu_api.get_all_link(self)
        g = nx.DiGraph()

        for link in links:
            src = link.src
            dst = link.dst
            g.add_edge(src.dpid, dst.dpid, src_port=src.port_no, dst_port=dst.port_no)

    def is_edge_port(self, dpid, port_no):
        links = ryu_api.get_all_link(self)

        for link in links:
            if link.src.dpid == dpid and link.src.port_no == port_no:
                return False

        return True

    def install_group_flow_entries(self, gid, match):
        switches = ryu_api.get_all_switch(self)

        for switch in switches:
            dp = switch.dp
            group_action = parser.OFPActionGroup(group_id=gid)
            self.add_flow(dp, DEFAULT_FLOW_PRIORITY, match, group_action)

    def modify_group_bucket_list(self, dp, gid, new_bucket_list):
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        gp_mod_msg = parser.OFPGroupMod(datapath, ofproto.OFPGC_ADD, ofproto.OFPGT_FF, group_id, new_bucket_list)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        '''
        L2 shortest path routing
        '''
        msg = ev.msg
        dp = msg.dp
        dpid = dp.id
        ofproto = dp.ofproto
        of_parser = dp.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        src = eth.src
        dst = eth.dst

        if self.is_edge_port(dpid, in_port):
            # add host record
            self.hosts[src] = (dpid, in_port)

            if src not in self.mac_to_gid
                self.mac_to_gid[src] = self.num_groups
                self.gid_to_mac[self.num_groups = src]
                self.num_groups += 1

            _match = of_parser.OFPMatch(in_port=in_port, eth_dst=src)
            self.install_group_flow_entries(self.mac_to_gid[src], _match)

        if dst not in self.hosts:
            # can't find host, drop it
            return

        dst_dpid, dst_port = self.hosts[dst]

        dst_gid = self.mac_to_gid.get(dst, -1)

        if dst_gid == -1:
            # can't find gid, drop
            return

        g = self.get_nx_graph()
        all_paths = nx.all_shortest_paths(g, dpid, dst_dpid)

        '''
        to_install:
        for example, topology like
            /2\ /5\
        h1-1   4   7-h2
            \3/ \6/
        all path from h1 to h2
        [1, 2, 4, 5, 7]
        [1, 2, 4, 6, 7]
        [1, 3, 4, 5, 7]
        [1, 3, 4, 6, 7]
        data of to_install will be:
        {
            1: [2, 3],
            2: [4],
            3: [4],
            4: [5, 6],
            5: [7],
            6: [7],
            7: []
        }
        '''
        to_install = {}

        for path in all_paths:
            for _i in range(0, len(path)):
                to_install.setdfault(path[_i], [])

                if path[_i] == dst_dpid:
                    continue

                if path[_i + 1] not in to_install[_i]:
                    to_install[_i].append(path[_i + 1])

        # gnerate all buckets and actions and install to switch
        for _dpid, _next_dpid_list in to_install.items():
            _dp = self.get_dp(_dpid)

            if not _dp:
                continue

            if _dpid == dst_dpid:
                actions = [of_parser.OFPActionOutput(port=dst_port)]
                buckets = [of_parser.OFPBucket(DEFAULT_BUCKET_WEIGHT, dst_port, dst_gid, actions)]
                gmod = of_parser.OFGroupMod(dp, ofproto.OFPGC_ADD, ofproto.OFPGT_FF, dst_gid, buckets)
                _dp.send_msg(gmod)

            else:
                buckets = []

                for _next_dpid in _next_dpid_list:
                    _out_port = g.edge[_dpid][_next_dpid]['src_port']
                    actions = [of_parser.OFPActionOutput(port=_out_port)]
                    buckets.append(of_parser.OFPBucket(DEFAULT_BUCKET_WEIGHT, _out_port, dst_gid, actions))

                gmod = of_parser.OFGroupMod(dp, ofproto.OFPGC_ADD, ofproto.OFPGT_FF, dst_gid, buckets)
                _dp.send_msg(gmod)
