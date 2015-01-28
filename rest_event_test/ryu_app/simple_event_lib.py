import os
from ryu.lib import hub
from ryu.base import app_manager
from ryu.controller import event
import json
import pdb

SOCKFILE = '/tmp/hello_sock'

class SimpleEvent(event.EventBase):

    def __init__(self, msg):
        super(SimpleEvent, self).__init__()
        self.msg = msg

class SimpleEventLib(app_manager.RyuApp):
    def __init__(self):
        super(SimpleEventLib, self).__init__()
        self.name = 'simple_ev_lib'
        self.sock = None

    def recv_loop(self):

        print "start loop"
        while True:
            print 'wait for recev'
            data = self.sock.recv(1024)
            print 'get data:', data
            msg = json.loads(data)
            print 'msg is:', msg
            pdb.set_trace()
            if msg:
                self.send_event_to_observers(SimpleEvent(msg))
                print 'sent to ovservers'

    def start_sock_server(self):
        if os.path.exists(SOCKFILE):
            os.unlink(SOCKFILE)

        self.sock = hub.socket.socket(hub.socket.AF_UNIX, hub.socket.SOCK_DGRAM)
        self.sock.bind(SOCKFILE)
        hub.spawn(self.recv_loop)
