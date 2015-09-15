from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types


class EventHostTimeout(event.EventBase):
    def __init__(self, host):
        super(EventHostTimeout, self).__init__()
        self.host = host

class HostLib(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _EVENTS = [EventHostTimeout]

    def __init__(self, *args, **kwargs):
        super(HostLib, self).__init__(*args, **kwargs)
        self.port_infos = {}
        hub.spawn(self.port_request_loop)


   	@set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_event_handler(self, ev):
    	pass

    def port_request_loop(self):
        time.sleep(5)

        while True:
            hosts = topo_api.get_all_host(self)
            ports = [host.port for host in hosts]

            for port in ports:
            	dpid = port.dpid
            	switch = topo_api.get_switch(self, dpid)
            	dp = switch.dp
                parser = dp.ofproto_parser
                ofproto = dp.ofproto
                msg = parser.OFPPortStatsRequest(dp, 0, port.port_no)
                dp.send_msg(msg)

            time.sleep(1)




