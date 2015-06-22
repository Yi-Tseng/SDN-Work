#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import contextlib
import json
import networkx as nx
from ryu.lib import hub
from ryu.lib.hub import StreamServer

logging.basicConfig()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)

MAX_AGENTS = 1024


class GlobalController(object):

    def __init__(self, *args):
        super(GlobalController, self).__init__()
        self.agents = {}
        self.server = StreamServer(('0.0.0.0', 10807), self._connection_factory)
        self.cross_domain_links = [] # ex: [{src: {dpid: 4, port: 3}, dst: {dpid: 1, port: 1} }]
        self.hosts = {} # host -> domain number


    def _connection_factory(self, socket, address):
        print 'connected socket:%s address:%s' % (socket, address)

        with contextlib.closing(GlobalAgent(socket, address)) as agent:
            agent.global_ctrn = self
            agent_id = len(self.agents)

            while agent_id in self.agents:
                agent_id = (agent_id + 1) % MAX_AGENTS

            agent.set_agent_id(agent_id)
            self.agents[agent_id] = agent
            agent.serve()
            LOG.info('Remove agent %d', agent_id)
            del self.agents[agent_id]


    def start(self):
        
        LOG.info('Waiting for connection.....')
        self.server.serve_forever()

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

        for _link in self.cross_domain_links:

            if _link['src']['dpid'] == src['dpid'] and \
                _link['src']['port'] == src['port']:
                _link['src']['agent_id'] = agent_id
                break

            if _link['dst']['dpid'] == src['dpid'] and \
                _link['dst']['port'] == src['port']:
                _link['dst']['agent_id'] = agent_id
                break

        else:
            self.cross_domain_links.append(link)
            self.cross_domain_links.append(link_rev)
        

            

    def broad_cast(self, msg):

        for agent in self.agents.itervalues():
            agent.send(msg)

    def get_route(self, dst_host, agent):
        '''
            dst_host: mac address
            agent: source domain(lc) agent
        '''

        if dst_host not in self.hosts:
            msg = json.dumps({
                'cmd': 'route_result',
                'dpid': -1,
                'port': -1,
                'host': dst_host
                })
            LOG.debug('Unknown host %s', dst_host)
            agent.send(msg)
            return

        
        # get source and destination
        # from a? to a? (cross doamin)
        dst_agent = self.hosts[dst_host]
        src_agent_id = agent.agent_id
        src = 'a%d' % (src_agent_id, )
        dst = 'a%d' % (dst_agent.agent_id, )

        # generate link between agents
        links = self._get_agent_links()

        # generate graph
        g = nx.Graph()
        g.add_edges_from(links)

        path = []
        if nx.has_path(g, src, dst):
            path = nx.shortest_path(g, src, dst)

        # we only need first two element and get output port
        glink = self._get_agent_link(path[0], path[1])

        # find output dpid and port
        output_dpid = glink['src']['dpid']
        output_port = glink['src']['port']

        # send route result
        msg = json.dumps({
            'cmd': 'route_result',
            'dpid': output_dpid,
            'port': output_port,
            'host': dst_host
        })
        LOG.debug('send route result to agent %d, %d:%d %s', 
                 agent.agent_id, output_dpid,
                 output_port, dst_host)
        agent.send(msg)


    def _get_agent_link(self, src, dst):
        # convert a? to ?
        src_agent_id = int(src[1:])
        dst_agent_id = int(dst[1:])

        for glink in self.cross_domain_links:
            src = glink['src']
            dst = glink['dst']
            if src['agent_id'] == src_agent_id and \
                dst['agent_id'] == dst_agent_id:
                return glink

        return None

    def _get_agent_links(self):
        '''
            link: ('a1', 'a2')
        '''
        links = []

        for glink in self.cross_domain_links:
            src = glink['src']
            dst = glink['dst']

            if 'agent_id' in src and 'agent_id' in dst:
                src = 'a%d' % (src['agent_id'], )
                dst = 'a%d' % (dst['agent_id'], )
                links.append((src, dst))

        return links


    def response_host(self, host, agent):
        '''
            actually, it use for get route
        '''
        self.hosts[host] = agent
        LOG.debug('Add host %s to self.hosts', host)


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

            while self.is_active:
                buf = self.send_q.get()
                self.socket.sendall(buf)
                hub.sleep(0.1)

        finally:
            q = self.send_q
            self.send_q = None

            try:

                while q.get(block=False):
                    pass

            except hub.QueueEmpty:
                pass

    def recv_loop(self):

        while self.is_active:
            try:
                _buf = self.socket.recv(128)

                if len(_buf) == 0:
                    LOG.info('connection fail, close')
                    self.is_active = False
                    break

                while '\n' != _buf[-1]:
                    _buf += self.socket.recv(128)

                bufs = _buf.split('\n')

                for buf in bufs:

                    if len(buf) == 0:
                        continue
                    msg = json.loads(buf)
                    LOG.debug('receive : %s', msg)
                    if msg['cmd'] == 'add_cross_domain_link':
                        LOG.debug('receive cross domain link message')
                        src = msg['src']
                        dst = msg['dst']
                        LOG.debug('src: %d, dst: %d', src, dst)
                        self.global_ctrn.add_cross_domain_link(src, dst, self.agent_id)

                    elif msg['cmd'] == 'response_host':
                        host = msg['host']
                        self.global_ctrn.response_host(host, self)

                    elif msg['cmd'] == 'get_route':
                        dst_host = msg['dst']
                        self.global_ctrn.get_route(dst_host, self)

                    elif msg['cmd'] == 'response_dpid':
                        dpid = msg['dpid']
                        self.global_ctrn.response_dpid(dpid, self.agent_id)

                hub.sleep(0.1)
            except ValueError:
                LOG.warning('Value error for %s, len: %d', buf, len(buf))
            

    def serve(self):
        thr = hub.spawn(self.send_loop)
        thr2 = hub.spawn(self.recv_loop)
        hub.joinall([thr, thr2])

    def have_host(self, mac='00:00:00:00:00:00', ip='0.0.0.0'):
        '''
        for cache
        '''
        pass

    def close(self):
        self.is_active = False
        self.socket.close()


# main function of global controller
def main():
    GlobalController().start()

if __name__ == '__main__':
    main()
