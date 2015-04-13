from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.controller import dpset
from ryu.topology import api
from ryu.lib.packet import arp
from ryu.ofproto import ofproto_v1_3


class GetSwitches(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    switches = []
    def __init__(self, *args, **kwargs):
        super(GetSwitches, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):

        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        in_port = msg.match['in_port']
        actions = [ofp_parser.OFPActionOutput(ofp.OFPP_FLOOD)]
        out = ofp_parser.OFPPacketOut(
            datapath=dp, 
            buffer_id=msg.buffer_id, 
            in_port=in_port,  
            actions=actions)

        dp.send_msg(out)

    @set_ev_cls(dpset.EventDP, MAIN_DISPATCHER)
    def datapath_change_handler(self, ev):

        if ev.enter:
            print "Datapath entered, id %s" % ev.dp.id
            switch = api.get_switch(self, ev.dp.id)[0]
            self.switches.append(switch)
            ports = switch.ports

            print "Switch : %s" % switch
            print "Ports :"
            for port in ports:
                print port.to_dict()
            
            print "Links :"
            links = api.get_link(self, ev.dp.id)
            for link in links:
                print link.to_dict()



     
