from collections import deque
import pdb

class BFSCalculator(object):
    '''
    BFS Calculator
    '''

    def __init__(self, ryu_links):
        self.graph = {}
        if ryu_links != None:
            self.ryu_links = ryu_links
            for link in ryu_links:
                src = link.src
                dst = link.dst
                self.graph[src.dpid][dst.dpid] = True

    def add_link(self, ryu_link):
        '''
        add link by ryu link
        param:
            ryu_link: Link object from ryu.topology.switch.Link
        '''

        assert ryu_link != None
        src = ryu_link.src
        dst = ryu_link.dst

        assert src != None and dst != None

        if src.dpid not in self.graph:
            self.graph[src.dpid] = {}

        self.graph[src.dpid][dst.dpid] = True

        if dst.dpid not in self.graph:
            self.graph[dst.dpid] = {}

        self.graph[dst.dpid][src.dpid] = True

    def remove_link(self, src, dst):
        '''
        remove link from this graph
        param:
            src: dpid from source datapath
            dst: dpid from destination datapath
        '''

        assert src != None and dst != None
        if src in self.graph:
            if dst in self.graph[src]:
                self.graph[src][dst] = False

        if dst in self.graph:
            if src in self.graph[dst]:
                self.graph[dst][src] = False

    def is_linked(self, src, dst):
        '''
        check if two datapath is linked
        param:
            src: dpid from source datapath
            dst: dpid from destination datapath
        '''

        assert src != None and dst != None
        res = True
        res = res and (src in self.graph)

        if not res:
            return res

        res = res and (dst in self.graph[src])

        if not res:
            return res

        res = res and self.graph[src][dst]
        return res

    def get_port_to_port_info(self, src, dst):
        '''
        get port to port information
        for example:
        s1-port1 linked to s4-port5
        it will return
        {'src_port':'00000001', 'dst_port':'00000005'}
        param:
            src: dpid from source datapath
            dst: dpid from destination datapath
        '''

        result = []
        if not self.is_linked(src, dst): return result

        # filter to get links that source and dstination is matched
        def f(l):
            return l.src.dpid == src and l.dst.dpid == dst

        filtered_link = fliter(f, self.ryu_links)
        for fl in filtered_link:
            s_port = fl.src.port_no
            d_port = fl.dst.port_no
            result.append({'src_port':s_port, 'dst_port':d_port})

        return result

    def get_links(self, dpid):
        '''
        get links from datapath
        param:
            dpid: id from datapath
        return:
            a list that contains it's links
        '''

        assert dpid != None
        if dpid not in self.graph:
            return []

        links = []
        for n in self.graph[dpid]:
            if self.graph[dpid][n]:
                links.append(n)

        return links

    def get_short_path(self, src, dst):
        '''
        get shortest path by BFS
        param:
            src: dpid from source datapath
            dst: dpid from destination datapath
        return:
            a list of path, contains ports, for example:
            [
                {'dpid':'dpid1', 'in_port':None, 'out_port':'outport1'},
                {'dpid':'dpid2', 'in_port':'in_port2', 'out_port':'outport2'},
                ......
                {'dpid':'dpidn', 'in_port':'in_portn', 'out_port':None}
            ]
            if destination is not reachable, it'll return an empty list
        '''
        # pdb.set_trace()
        records = {src:0}
        node_queue = deque()
        node_queue.append(src)
        while len(node_queue) != 0:
            node = node_queue.popleft()

            if node == dst:
                break

            links = self.get_links(node)
            if node in records:
                for _dst in links:
                    if _dst not in records:
                        records[_dst] = records[node] + 1
                        node_queue.append(_dst)
            else:
                break

        if dst not in records or records[dst] == -1:
            return []

        # get shortst path...
        sorted_res = sorted(records.items(), key=lambda x:x[1], reverse=True)

        # remove unnecessary nodes
        dst_deepth = records[dst]
        need_to_remove = []
        for node in sorted_res:
            if node[0] != dst and node[1] == dst_deepth:
                need_to_remove.append(node)

        for node in need_to_remove:
            sorted_res.remove(node)

        deepth_set = {}
        for item in sorted_res:
            if item[1] not in deepth_set:
                deepth_set[item[1]] = []
            deepth_set[item[1]].append(item[0])

        result = [deepth_set[records[dst]][0]]
        self.get_short_path_rec(deepth_set, records[dst], result)

        return result


    def get_short_path_rec(self, deepth_set, deepth, result):
        '''get shotest path by using recursive method'''

        if deepth == 0:
            result = result.reverse()
            return True

        else:
            current_node = result[len(result)-1]
            pos_nodes = deepth_set[deepth - 1]

            for node in pos_nodes:
                res = False

                if self.is_linked(current_node, node):
                    result.append(node)
                    res = self.get_short_path_rec(deepth_set, deepth-1, result)
                    if res:
                        return True
                    result.pop()

        return False

