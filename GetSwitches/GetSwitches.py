from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.controller import dpset
from ryu.topology import api
from ryu.lib.packet import arp
from ryu.ofproto import ofproto_v1_3


class GetSwitches(app_manager.RyuApp):
    switches = []

    def __init__(self, *args, **kwargs):
        super(GetSwitches, self).__init__(*args, **kwargs)

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
