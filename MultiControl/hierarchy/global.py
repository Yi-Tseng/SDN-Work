#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import contextlib
import json
from random import randint
from ryu.lib import hub
from ryu.lib.hub import StreamServer

LOG = logging.getLogger('load_balance_global')
MAX_AGENTS = 1024


class GlobalController(object):

    def __init__(self, *args):
        super(GlobalController, self).__init__()
        self.agents = {}
        self.server = StreamServer(('0.0.0.0', 10807), self._connection_factory)
        self.cross_domain_links = [] # ex: [{src: {dpid: 4, port: 3}, dst: {dpid: 1, port: 1} }]
        self.host_req_list = {} # host mac -> agent

    def _serve_loop(self):
        # calculate load for each agent and send role to them.
        while True:
            hub.sleep(1)

    def _connection_factory(self, socket, address):
        print('connected socket:%s address:%s', socket, address)

        with contextlib.closing(GlobalAgent(socket, address)) as agent:
            agent.global_ctrn = self
            agent_id = len(self.agents)

            while agent_id in self.agents:
                agent_id = (agent_id + 1) % MAX_AGENTS

            agent.set_agent_id(agent_id)
            self.agents[agent_id] = agent
            agent.serve()
            del self.agents[agent_id]


    def start(self):
        thr = hub.spawn(self._serve_loop)
        print 'Waiting for connection.....'
        self.server.serve_forever()
        
        hub.joinall([thr])

    def print_agents_status(self):

        for agent in self.agents:
            print "%s:%s" % (agent.address, agent.__str__(), )

    def add_cross_domain_link(self, src, dst, agent_id):
        src['agent_id'] = agent_id
        link = {'src': src, 'dst': dst}
        link_rev = {'src': dst, 'dst': src}

        # ask for dpid
        msg = json.dumps({
            'cmd': 'ask_dpid',
            'dpid': dst['dpid']
            })
        self.broad_cast(msg)

        if link not in self.cross_domain_links:
            self.cross_domain_links.append(link)
            self.cross_domain_links.append(link_rev)

    def broad_cast(self, msg):

        for agent in self.agents:
            agent.send(msg)

    def get_route(self, msg):
        pass

    def response_host(self, msg):
        pass

    def response_dpid(self, dpid, agent_id):

        for link in self.cross_domain_links:

            if link['src']['dpid'] == dpid:
                link['src']['agent_id'] = agent_id

            if link['dst']['dpid'] == dpid:
                link['dst']['agent_id'] = agent_id



class GlobalAgent(object):

    def __init__(self, socket, address):
        super(GlobalAgent, self).__init__()
        self.socket = socket
        self.address = address
        self.send_q = hub.Queue(32)
        self.is_active = True
        self.global_ctrn = None
        self.agent_id = -1

    def set_agent_id(self, agent_id):
        self.agent_id = agent_id
        msg = json.dumps({
            'cmd': 'set_agent_id',
            'agent_id': agent_id
            })
        self.send(msg)

    def send(self, msg):

        if self.send_q:
            self.send_q.put(msg)

    def send_loop(self):

        try:

            while True:
                buf = self.send_q.get()
                self.socket.sendall(buf)

        finally:
            q = self.send_q
            self.send_q = None

            try:

                while q.get(block=False):
                    pass

            except hub.QueueEmpty:
                pass

    def recv_loop(self):

        while True:
            buf = self.socket.recv(128)
            msg = json.loads(buf)

            if msg['cmd'] == 'add_cross_domain_link':
                src = msg['src']
                dst = msg['dst']
                self.global_ctrn.add_cross_domain_link(src, dst, self.agent_id)

            elif msg['cmd'] == 'reponse_host':
                pass

            elif msg['cmd'] == 'get_route':
                pass

            elif msg['cmd'] == 'response_dpid':
                dpid = msg['dpid']
                self.global_ctrn.response_dpid(dpid, self.agent_id)
            

    def serve(self):
        thr = hub.spawn(self.send_loop)
        self.recv_loop()
        hub.joinall([thr])

    def have_host(self, mac='00:00:00:00:00:00', ip='0.0.0.0'):
        pass

    def close(self):
        self.is_active = False
        self.socket.close()


# main function of global controller
def main():
    GlobalController().start()

if __name__ == '__main__':
    main()
