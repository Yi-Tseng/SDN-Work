#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import contextlib
import liblb
import pdb

from ryu.lib import hub
from ryu.lib.hub import StreamServer

LOG = logging.getLogger('load_balance_global')


# define role
ROLE_SLAVE = 1
ROLE_MASTER = 2

# for calculate load score
ALPHA = 0.5
BETA = 1 - ALPHA

# overload threshold(0~1)
THRESHOLD = 0.7

class GlobalController(object):

    def __init__(self, *args):
        super(GlobalController, self).__init__()
        self.agents = []
        self.server = StreamServer(('0.0.0.0', 10807), self._connection_factory)

    def _find_free_agent(self, busy_agent):
        '''
        find free agent
        rule:
            less loading score
            less switch control
        '''
        free_agent = None
        agents = sorted(self.agents, key=lambda x: (x.load_score, x.controlled_switch))

        for agent in agents:

            if agent.load_score < THRESHOLD and agent is not busy_agent:
                free_agent = agent
                break

        return free_agent


    def _balance_agents(self, busy_agent, free_agent):
        '''
        move one switch from busy to free
        '''
        # find one dpid for move
        for dpid in busy_agent.dpid_to_role:

            if busy_agent.dpid_to_role[dpid] == ROLE_MASTER and dpid in free_agent.dpid_to_role:
                # move it
                # TODO: not finish.
                pass
                





    def _serve_loop(self):
        # calculate load for each agent and send role to them.
        while True:

            self.print_agents_status()

            for agent in self.agents:

                if not agent.is_active:
                    self.agents.remove(agent)

                # local controller is overloaded
                free_agent = None

                if agent.load_score > THRESHOLD:
                    free_agent = self._find_free_agent(agent)

                if free_agent != None:
                    # move some switch to free agent
                    self._balance_agents(agent, free_agent)

            hub.sleep(1)

    def _connection_factory(self, socket, address):
        print('connected socket:%s address:%s', socket, address)

        with contextlib.closing(GlobalAgent(socket, address)) as agent:
            self.agents.append(agent)
            agent.serve()

    def start(self):
        thr = hub.spawn(self._serve_loop)
        print 'Waiting for connection.....'
        self.server.serve_forever()
        
        hub.joinall([thr])

    def print_agents_status(self):

        for agent in self.agents:
            print "%s:%s" % (agent.address, agent.__str__(), )

class GlobalAgent(object):

    def __init__(self, socket, address):
        super(GlobalAgent, self).__init__()
        self.socket = socket
        self.address = address
        self.dpid_to_role = {}
        self.send_q = hub.Queue(32)
        self.cpu_load = 0
        self.mem_load = 0
        self.load_score = 0
        self.is_active = True

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
            header_data = self.socket.recv(liblb.HeaderStruct.size)
            header = liblb.HeaderStruct.unpack(header_data)[0]

            # add new dpid
            if header == 1:
                dp_data = self.socket.recv(liblb.DPStruct.size)
                dpid = liblb.DPStruct.unpack(dp_data)[0]

                if dpid not in self.dpid_to_role:
                    self.dpid_to_role[dpid] = ROLE_SLAVE

            # update loading
            else:
                load_data = self.socket.recv(liblb.UtilStruct.size)
                self.cpu_load, self.mem_load = liblb.UtilStruct.unpack(load_data)
                self.load_score = ALPHA * self.cpu_load + BETA * self.mem_load

    def serve(self):
        thr = hub.spawn(self.send_loop)
        self.recv_loop()
        hub.joinall([thr])

    def is_controling_dp(self, dpid):
        role = self.dpid_to_role.get(dpid, None)

        if role:
            return role == ROLE_MASTER

        return False

    def controlled_switch(self):
        '''
        number of master control
        '''
        result = 0

        for k in self.dpid_to_role:
            result += 1 if self.dpid_to_role[k] == ROLE_MASTER else 0

        return result

    def close(self):
        self.is_active = False
        self.socket.close()

    def __str__(self):
        return self.dpid_to_role.__str__()


# main function of global controller
def main():
    # pdb.set_trace()
    GlobalController().start()

if __name__ == '__main__':
    main()
