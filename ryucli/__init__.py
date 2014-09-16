# coding: utf-8
# file: __init__.py
from threading import Thread
from ryu.topology import api

class RyuCLI(Thread):

    def __init__(self, ryu_app):
        Thread.__init__(self)
        self.ryu_app = ryu_app


    def run(self):
        cmd = raw_input('input command')
        if cmd == 'switchs':
            switches = api.get_all_switch(self.ryu_app)
            print switches
        elif cmd == 'links':
            links = api.get_all_links(self.ryu_app)
            print links
