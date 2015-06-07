#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import contextlib
import json
from ryu.lib import hub
from ryu.lib.hub import StreamServer

LOG = logging.getLogger('load_balance_global')



class GlobalController(object):

    def __init__(self, *args):
        super(GlobalController, self).__init__()
        self.agents = []
        self.server = StreamServer(('0.0.0.0', 10807), self._connection_factory)

    def _serve_loop(self):
        # calculate load for each agent and send role to them.
        while True:
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
        self.send_q = hub.Queue(32)
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
            pass

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
