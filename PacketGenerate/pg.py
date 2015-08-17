from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ipv4, udp
from ryu.lib.packet import ether_types

'''
To test this code

1. Create "single" topology

h1 -- s1 -- h2

2. start xterm for both h1 and h2 and run nc:

h1:
nc -u 10.0.0.2 8000

h2:
nc -u -l 8000

3. send packet from h1 to h2, and h2 will 
receive "Hellooooooooo~~~~~~~~~" string
'''


class PacketGenApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(PacketGenApp, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

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

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        pkt = packet.Packet()

        pkt.add_protocol(ethernet.ethernet(ethertype=0x0800, dst='00:00:00:00:00:02', src='00:00:00:00:00:01'))

        pkt.add_protocol(ipv4.ipv4(dst='10.0.0.2', src='10.0.0.1', proto=17))
        pkt.add_protocol(udp.udp(src_port=1000, dst_port=8000))

        payload = b'Hellooooooooo~~~~~~~~~'
        pkt.add_protocol(payload)

        # Packet serializing
        pkt.serialize()

        data = pkt.data

        msg = ev.msg
        dp = msg.datapath
        ofproto = dp.ofproto
        actions = [dp.ofproto_parser.OFPActionOutput(2)]

        out = dp.ofproto_parser.OFPPacketOut(
            datapath=dp, buffer_id=ofproto.OFP_NO_BUFFER, in_port=msg.match['in_port'],
            actions=actions, data=data)

        dp.send_msg(out)


        
