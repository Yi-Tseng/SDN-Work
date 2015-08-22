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


def print_topo(switches=[], links=[], hosts=[]):
    tlinks = []
    thosts = []

    for switch in switches:
        print('{}┐{:>8}'.format(switch['dpid'], ' '), end='')

        for t in tlinks:
            cindex = tlinks.index(t)
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

                    if None in tlinks:
                        nindex = tlinks.index(None)
                        tlinks[nindex] = link

                    else:
                        tlinks.append(link)

            for host in hosts:
                if port['hw_addr'] == host['port']['hw_addr']:
                    thosts.append(host)

            for t in tlinks:
                if len(thosts) > 0:
                    print('-' * (len(tlinks) + 1), end='')
                    print('-'.join([th['mac'] for th in thosts]), end='')
                    thosts = []
                    break

                cindex = tlinks.index(t)
                src_ports = [l['src'] if l != None else None for l in tlinks]
                dst_ports = [l['dst'] if l != None else None for l in tlinks]

                if t == None and (port in dst_ports):
                    dindex = dst_ports.index(port)
                    print('{}-{}'.format(colors[dindex % num_colors], end_color), end='')

                elif t == None and (port in src_ports):
                    sindex = src_ports.index(port)
                    print('{}-{}'.format(colors[sindex % num_colors], end_color), end='')

                elif t == None:
                    print(' ', end='')

                elif port['hw_addr'] == t['src']['hw_addr']:
                    print('{}┐{}'.format(colors[cindex % num_colors], end_color), end='')

                elif port['hw_addr'] == t['dst']['hw_addr']:
                    print('{}┘{}'.format(colors[cindex % num_colors], end_color), end='')
                    tlinks[cindex] = None

                    while len(tlinks) > 0 and tlinks[-1] == None:
                        del tlinks[-1]

                else:
                    print('{}|{}'.format(colors[cindex % num_colors], end_color), end='')

            print()


def main():
    switches = json.load(open('switches.json', 'r'))
    links = json.load(open('links.json', 'r'))
    hosts = json.load(open('hosts.json', 'r'))
    print_topo(switches, links, hosts)


if __name__ == '__main__':
    main()
