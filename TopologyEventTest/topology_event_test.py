from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.topology import event as topo_event

'''
Test these topology events

EventHostAdd
EventLinkDelete
EventLinkAdd
EventPortModify
EventPortDelete
EventPortAdd
EventSwitchLeave
EventSwitchEnter

'''

class TopologyEventTestApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TopologyEventTestApp, self).__init__(*args, **kwargs)

    @set_ev_cls(topo_event.EventHostAdd, MAIN_DISPATCHER)
    def EventHostAdd_handler(self, ev):
        self.logger.info('Event %s', ev)

    @set_ev_cls(topo_event.EventLinkDelete, MAIN_DISPATCHER)
    def EventLinkDelete_handler(self, ev):
        self.logger.info('Event %s', ev)

    @set_ev_cls(topo_event.EventLinkAdd, MAIN_DISPATCHER)
    def EventLinkAdd_handler(self, ev):
        self.logger.info('Event %s', ev)

    @set_ev_cls(topo_event.EventPortModify, MAIN_DISPATCHER)
    def EventPortModify_handler(self, ev):
        self.logger.info('Event %s', ev)

    @set_ev_cls(topo_event.EventPortDelete, MAIN_DISPATCHER)
    def EventPortDelete_handler(self, ev):
        self.logger.info('Event %s', ev)

    @set_ev_cls(topo_event.EventPortAdd, MAIN_DISPATCHER)
    def EventPortAdd_handler(self, ev):
        self.logger.info('Event %s', ev)

    @set_ev_cls(topo_event.EventSwitchLeave, MAIN_DISPATCHER)
    def EventSwitchLeave_handler(self, ev):
        self.logger.info('Event %s', ev)

    @set_ev_cls(topo_event.EventSwitchEnter, MAIN_DISPATCHER)
    def EventSwitchEnter_handler(self, ev):
        self.logger.info('Event %s', ev)

