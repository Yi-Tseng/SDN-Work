#!/usr/bin/python
# -*- coding: utf-8 -*-
# file: MyTopo.py

from mininet.topo import Topo

class Square(Topo):
    ''' Simple topology example '''

    def __init__(self):
        Topo.__init__(self)
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')

        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        self.addLink(s1, s2)
        self.addLink(s1, s3)
        self.addLink(s2, s4)
        self.addLink(s2, h1)
        self.addLink(s3, s4)
        self.addLink(s4, h2)

class Router(Topo):
    '''test'''

    def __init__(self):
        Topo.__init__(self)
        s1 = self.addSwitch('s1')
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')

        self.addLink(s1, h1)
        self.addLink(s1, h2)
        self.addLink(s1, h3)



topos = {'square': (lambda: Square()), 'router': (lambda: Router())}

