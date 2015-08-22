#!/usr/bin/env python3
# -*- coding: utf8 -*-
import json

switches = json.load(open('switches.json', 'r'))
links = json.load(open('links.json', 'r'))
hosts = json.load(open('hosts.json', 'r'))

for switch in switches:
    print('{}┐'.format(switch['dpid']))

    for port in switch['ports']:
        print('{}├{}'.format(len(switch['dpid']) * ' ', port['port_no']))
