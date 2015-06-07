# -*- coding: utf-8 -*-
import logging
import random

from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.topology import event
from ryu.topology import api
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER
from liblb import LBEventRoleChange, LoadBalancer

LOG = logging.getLogger('load_balance_app')

class LoadBalanceApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'load_balancer': LoadBalancer}

    def __init__(self, *args, **kwargs):
        super(LoadBalanceApp, self).__init__(*args, **kwargs)
        self.load_balancer = kwargs['load_balancer']
        switches = api.get_all_switch(self)

        # change to slave first
        for switch in switches:
            dp = switch.dp
            ofp = dp.ofproto
            ofp_parser = dp.ofproto_parser
            role = ofp.OFPCR_ROLE_SLAVE
            # generate new generation id
            gen_id = random.randint(0, 10000)
            msg = ofp_parser.OFPRoleRequest(dp, role, gen_id)
            dp.send_msg(msg)

        self.load_balancer.start_serve()

    @set_ev_cls(event.EventSwitchEnter, MAIN_DISPATCHER)
    def _event_switch_enter_handler(self, ev):
        dpid = ev.dp.id
        self.load_balancer.add_dpid(dpid)

    @set_ev_cls(LBEventRoleChange, MAIN_DISPATCHER)
    def _role_change_handler(self, ev):
        dpid = ev.dpid
        role = ev.role
        # Role:
        # 1: master
        # 2: slave

        switch = api.get_switch(self, dpid)

        if switch != None:
            dp = switch.dp
            ofp = dp.ofproto
            ofp_parser = dp.ofproto_parser

            if role == 1:
                role = ofp.OFPCR_ROLE_MASTER

            else:
                role = ofp.OFPCR_ROLE_SLAVE
            # generate new generation id
            gen_id = random.randint(0, 10000)
            msg = ofp_parser.OFPRoleRequest(dp, role, gen_id)
            dp.send_msg(msg)

app_manager.require_app('liblb.LoadBalancer')