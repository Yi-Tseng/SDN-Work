from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet


# h1 -> s1 -> h2 : drop
# h1 <- s1 <- h2 : pass

class StaticFlow(app_manager.RyuApp):

    def __init__(self, *args, **kwargs):
        super(StaticFlow, self).__init__(*args, **kwargs)
        self.mac_to_port = {}


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

        h1_ip = '10.0.0.1'
        h2_ip = '10.0.0.2'

        h1_mac = '00:00:00:00:00:01'
        h2_mac = '00:00:00:00:00:02'

        h1_port = 1

        # install static rule
        match_h1_to_h2_ip = parser.OFPMatch(eth_type=2048, ipv4_src=h1_ip, ipv4_dst=h2_ip)
        match_h2_to_h1_ip = parser.OFPMatch(eth_type=2048, ipv4_src=h2_ip, ipv4_dst=h1_ip)

        match_h1_to_h2_mac = parser.OFPMatch(eth_src=h1_mac, eth_dst=h2_mac)
        match_h2_to_h1_mac = parser.OFPMatch(eth_src=h2_mac, eth_dst=h1_mac)

        actions_forward = [parser.OFPActionOutput(h1_port)]
        actions_drop = [] # no actions to drop

        self.add_flow(datapath, 32767, match_h1_to_h2_mac, actions_drop)
        self.add_flow(datapath, 32767, match_h2_to_h1_mac, actions_forward)

        self.add_flow(datapath, 32767, match_h1_to_h2_ip, actions_drop)
        self.add_flow(datapath, 32767, match_h2_to_h1_ip, actions_forward)

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
