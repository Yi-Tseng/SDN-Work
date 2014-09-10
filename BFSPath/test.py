#!/usr/bin/python
# -*- encoding: utf-8 -*-
# file: test.py

'''BFSCalculator test'''

from BFSCalculator import BFSCalculator


class DP:
    ''' fake Ryu Datapath, just for test'''
    def __init__(self, dpid):
        self.dpid = dpid

class RyuLink:
    ''' fake RyuLink, just for test'''

    def __init__(self, src, dst):
        self.src = DP(src)
        self.dst = DP(dst)


def main():
    '''main function'''
    links = []
    calculator = BFSCalculator(links)
    calculator.add_link(RyuLink('a', 'b'))
    calculator.add_link(RyuLink('a', 'c'))
    calculator.add_link(RyuLink('b', 'd'))
    calculator.add_link(RyuLink('b', 'f'))
    calculator.add_link(RyuLink('c', 'f'))
    calculator.add_link(RyuLink('c', 'g'))
    calculator.add_link(RyuLink('d', 'e'))
    calculator.add_link(RyuLink('e', 'f'))
    calculator.add_link(RyuLink('f', 'g'))
    calculator.add_link(RyuLink('f', 'h'))

    from_node = 'a'
    to_node = 'h'
    res = calculator.get_short_path(from_node, to_node)
    print 'From %s to %s: ' % (from_node, to_node)
    print res

if __name__ == '__main__':
    main()
