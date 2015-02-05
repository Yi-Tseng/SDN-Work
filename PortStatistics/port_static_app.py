import time

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.controller import dpset
from static_updater import StaticUpdater

class PortStaticApp(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    _CONTEXTS = {
        'static_updater': StaticUpdater
    }

    def __init__(self, *args, **kwargs):
        super(PortStaticApp, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.dps = []
        self.port_infos = {}
        self.static_updater = kwargs["static_updater"]
        self.static_updater.set_ryu_app(self)
        self.static_updater.start()

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(dpset.EventDP, MAIN_DISPATCHER)
    def event_dp_handler(self, ev):

        if ev.enter:
            print "Datapath %X in" % (ev.dp.id)
            self.dps.append(ev.dp)


    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_event_handler(self, ev):

        print "Handling port stats event"

        for stat in ev.msg.body:
            dpid = ev.dp.id
            port_no = stat.port_no
            name = "%X-%d" % (dpid, port_no)
            current_time_milli = time.time() * 1000

            self.port_infos.setdefault(name, {"last_update":current_time_milli, "rx_bytes": 0, "tx_bytes": 0, "rx_band": 0, "tx_band": 0})
            port_info = self.port_infos[name]

            if port_info["last_update"] == current_time_milli:
                port_info["rx_bytes"] = stat.rx_bytes
                port_info["tx_bytes"] = stat.tx_bytes

            else:
                delta_time = current_time_milli - port_info["last_update"]
                port_info["rx_band"] = (stat.rx_bytes - port_info["rx_bytes"]) / delta_time
                port_info["tx_band"] = (stat.tx_bytes - port_info["tx_bytes"]) / delta_time
                port_info["rx_bytes"] = stat.rx_bytes
                port_info["tx_bytes"] = stat.tx_bytes
                port_info["last_update"] = current_time_milli

        print "Bandwidth informations"

        for name in self.port_infos:
            port_info = self.port_infos[name]
            print "[%s] rx: %f, tx: %f" % (name, port_info["rx_band"], port_info["tx_band"])




