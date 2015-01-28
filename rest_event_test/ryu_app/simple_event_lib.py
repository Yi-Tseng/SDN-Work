import os
from ryu.lib import hub
from ryu.base import app_manager
from ryu.controller import event
import json

SOCKFILE = '/tmp/hello_sock'

class SimpleEvent(event.EventBase):

    def __init__(self, msg):
        super(SimpleEvent, self).__init__()
        self.msg = msg

class SimpleEventLib(app_manager.RyuApp):
    def __init__(self):
        super(SimpleEventLib, self).__init__()
        self.sock = None

    def recv_loop(self):

        while True:
            data = self.sock.recv(1024)
            msg = json.loads(data)
            self.send_event_to_observers(SimpleEvent(msg))

    def start_sock_server(self):
        if os.path.exists(SOCKFILE):
            os.unlink(SOCKFILE)

        self.sock = hub.socket.socket(hub.socket.AF_UNIX, hub.socket.SOCK_DGRAM)
        self.sock.bind(SOCKFILE)
        hub.spawn(self.recv_loop)
