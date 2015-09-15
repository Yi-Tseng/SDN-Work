# -*- coding: utf-8 -*-
import socket
import struct
import psutil
import logging

from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
from ryu.controller import event

HeaderStruct = struct.Struct('!B')
DPStruct = struct.Struct('!I')
UtilStruct = struct.Struct('!BB')
RoleStruct = struct.Struct('!IB')

LOG = logging.getLogger('load_balance_lib')


def get_cpu_ultilization():
    return psutil.cpu_percent(interval=1)


def get_ram_ultilization():
    ram = psutil.virtual_memory()
    return ram.percent


class LBEventRoleChange(event.EventBase):
    def __init__(self, dpid, role):
        super(LBEventRoleChange, self).__init__()
        self.dpid = dpid
        self.role = role


class LoadBalancer(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, server_addr='127.0.0.1', server_port=10807, *args, **kwargs):
        super(LoadBalancer, self).__init__(*args, **kwargs)

        self.server_addr = kwargs['server_addr']
        self.server_port = kwargs['server_port']
        self.global_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start_serve(self):
        try:
            self.global_socket.connect((self.server_addr, self.server_port))
            hub.spawn(self._balance_loop)
        except Exception, e:
            raise e

    def add_dpid(self, dpid):
        # send header, 1 for adding dpid
        header_data = HeaderStruct.pack(1)
        self.global_socket.sendall(header_data)

        dp_data = DPStruct.pack(dpid)
        self.global_socket.sendall(dp_data)

    def _balance_loop(self):
        '''
        keep sending cpu usage and memory usage
        and receive global controller decision
        '''
        while True:
            cpu_util = get_cpu_ultilization()
            mem_util = get_ram_ultilization()

            # send header, 0 for load
            header_data = HeaderStruct.pack(0)
            self.global_socket.sendall(header_data)

            load_data = UtilStruct.pack(cpu_util << 8 | mem_util)
            self.global_socket.sendall(load_data)
            role_data = self.global_socket.recv(RoleStruct.size)
            dpid, role = RoleStruct.unpack(role_data)

            # Role:
            # [dpid][role]
            # 0: no change
            # 1: master
            # 2: slave

            if role == 0:
                LOG.debug('no need to change role.')
                continue

            else:
                role_event = LBEventRoleChange(dpid, role)
                self.send_event_to_observers(role_event)
