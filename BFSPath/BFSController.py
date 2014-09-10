'''
OF Controller
'''
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.controller import dpset
from ryu.lib.packet import ethernet
from ryu.lib.packet import packet
from ryu.lib.packet import arp
from ryu.lib.packet import ipv6
from ryu.ofproto import ether
from ryu.ofproto import ofproto_v1_3
from ryu.topology import api
from BFSCalculator import BFSCalculator

class BFSSwitch(app_manager.RyuApp):
    '''
    Using BFS to generate path.
    '''

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    dps = {}
    def __init__(self, *args, **kwargs):
        super(BFSSwitch, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        '''
        process input packet
        '''
        msg = ev.msg
        datapath = msg.datapath
        datapath_id = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # print 'Ether type : %X' % eth.ethertype

        if eth.ethertype == ether.ETH_TYPE_IPV6:
            # print 'Receive an ipv6 packet'
            ipv6_pkt = pkt.get_protocols(ipv6.ipv6)[0]
            # print 'Src: %s, Dst: %s' % (ipv6_pkt.src, ipv6_pkt.dst)

        if eth.ethertype == ether.ETH_TYPE_ARP:
            print 'Receive an ARP packet'
            arp_pkt = pkt.get_protocols(arp.arp)[0]
            self.process_arp(datapath, in_port, arp_pkt)

    @set_ev_cls(dpset.EventDP, MAIN_DISPATCHER)
    def datapath_change_handler(self, ev):

        if ev.enter:
            print "Datapath entered, id %s" % ev.dp.id

    def process_arp(self, datapath, in_port, arp_pkt):
        src_mac = arp_pkt.src_mac
        src_ip = arp_pkt.src_ip
        dst_mac = arp_pkt.dst_mac
        dst_ip = arp_pkt.dst_ip
        print '[arp] %s %s -> %s %s' % (src_mac, src_ip, dst_mac, dst_ip)

