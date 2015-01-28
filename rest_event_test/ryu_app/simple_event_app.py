from ryu.controller import ofp_event
from ryu.base import app_manager
import simple_event_lib
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3


class SimpleEventApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'evlib': simple_event_lib.SimpleEventLib}

    def __init__(self, *args, **kwargs):
        super(SimpleEventApp, self).__init__(*args, **kwargs)
        self.evlib = kwargs['evlib']
        self.evlib.start_sock_server()

    @set_ev_cls(simple_event_lib.SimpleEvent, MAIN_DISPATCHER)
    def simple_event_handler(self, ev):
        print "Get simple event"
        print "Message:", ev.msg

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        pass
