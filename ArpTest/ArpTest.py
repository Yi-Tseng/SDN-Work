from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.controller import dpset
from ryu.topology import api
from ryu.lib.packet import ethernet
from ryu.lib.packet import packet
from ryu.lib.packet import arp
from ryu.lib.packet import ipv6
from ryu.ofproto import ether
from ryu.ofproto import ofproto_v1_3


class ArpTest(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    dps = {}

    def __init__(self, *args, **kwargs):
        super(ArpTest, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        datapath_id = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        print 'Ether type : %X' % eth.ethertype

        if eth.ethertype == ether.ETH_TYPE_IPV6:
            print 'Receive an ipv6 packet'
            ipv6_pkt = pkt.get_protocols(ipv6.ipv6)[0]
            print 'Src: %s, Dst: %s' % (ipv6_pkt.src, ipv6_pkt.dst)

        if eth.ethertype == ether.ETH_TYPE_ARP:
            print 'Receive an ARP packet'
            arp_pkt = pkt.get_protocols(arp.arp)[0]
            self.process_arp(datapath, in_port, arp_pkt)

        dst_mac = eth.dst
        src_mac = eth.src

        # print "From %s to %s, datapath_id : %s" % (str(src_mac), str(dst_mac), str(datapath_id))
        self.set_default_dp_port(datapath_id, port=in_port, mac=src_mac)

    @set_ev_cls(dpset.EventDP, MAIN_DISPATCHER)
    def datapath_change_handler(self, ev):

        if ev.enter:
            print "Datapath entered, id %s" % ev.dp.id
            # switch = api.get_switch(self, ev.dp.id)[0]
            dpid = ev.dp.id
            self.set_default_dp_port(dpid)
            # self.send_arp(datapath=ev.dp)

    def set_default_dp_port(self, dpid, port=None, mac=None):

        if dpid not in self.dps:
            self.dps[dpid] = {'dpid': dpid, 'ports': []}

        if port != None and mac != None:
            ports = self.dps[dpid]['ports']
            if mac not in ports:
                ports.append({'port': port, 'mac': mac})

    def process_arp(self, datapath, port, arp_pkt):
        src_mac = arp_pkt.src_mac
        src_ip = arp_pkt.src_ip
        dst_mac = arp_pkt.dst_mac
        dst_ip = arp_pkt.dst_ip
        print 'src : %s %s, dst : %s %s' % (src_mac, src_ip, dst_mac, dst_ip)

    def send_arp(self, datapath, port=None, src_mac=None, src_ip=None, dst_mac=None, dst_ip=None):
        eth_pkt = ethernet.ethernet(ether.ETH_TYPE_ARP)
        arp_pkt = arp.arp()
        ofp_parser = datapath.ofproto_parser
        ofp = datapath.ofproto
        flood = ofp_parser.OFPActionOutput(ofp.OFPP_FLOOD)
        actions = [flood]
        p = packet.Packet()
        p.add_protocol(arp_pkt)
        p.add_protocol(eth_pkt)
        p.serialize()
        out = ofp_parser.OFPPacketOut(
            datapath=datapath,
            in_port=datapath.ofproto.OFPP_CONTROLLER,
            actions=actions,
            buffer_id=0xffffffff,
            data=buffer(p.data))

        print 'sending arp'
        datapath.send_msg(out)
        print 'sent!'
