# -*- coding: utf-8 -*-
import logging

from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.topology import event
from ryu.topology import api
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER


LOG = logging.getLogger('local_app')

class LocalControllerApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(LoadBalanceApp, self).__init__(*args, **kwargs)

    