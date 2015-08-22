#!/usr/bin/env python3
# -*- coding: utf8 -*-
import json


# By John-Lin
colors = [
    '\033[94m',
    '\033[92m',
    '\033[93m',
    '\033[91m'
]
end_color = '\033[0m'
num_colors = len(colors)

switches = json.load(open('switches.json', 'r'))
links = json.load(open('links.json', 'r'))
hosts = json.load(open('hosts.json', 'r'))
tmp = []
for switch in switches:
    print('{}┐{:>8}'.format(switch['dpid'], ' '), end='')

    for t in tmp:
        cindex = tmp.index(t)
        if t == None:
            print(' ', end='')
        else:
            print('{}|{}'.format(colors[cindex % num_colors], end_color), end='')

    print()

    for port in switch['ports']:
        if port != switch['ports'][-1]:
            print('{:>17}{}'.format('├', port['port_no']), end='')

        else:
            print('{:>17}{}'.format('└', port['port_no']), end='')

        for link in links:
            if port['hw_addr'] == link['src']['hw_addr'] and\
               int(link['src']['dpid']) < int(link['dst']['dpid']):
                tmp.append(link)

        for t in tmp:
            cindex = tmp.index(t)
            dst_ports = [l['dst'] if l != None else None for l in tmp]
            if t == None and (port in dst_ports):
                dindex = dst_ports.index(port)
                print('{}-{}'.format(colors[dindex % num_colors], end_color), end='')

            elif t == None:
                print(' ', end='')

            elif port['hw_addr'] == t['src']['hw_addr']:
                print('{}┐{}'.format(colors[cindex % num_colors], end_color), end='')

            elif port['hw_addr'] == t['dst']['hw_addr']:
                print('{}┘{}'.format(colors[cindex % num_colors], end_color), end='')
                tmp[cindex] = None
            else:
                print('{}|{}'.format(colors[cindex % num_colors], end_color), end='')

        print()
