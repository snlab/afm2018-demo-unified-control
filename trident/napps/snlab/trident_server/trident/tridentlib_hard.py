from napps.snlab.trident_server.trident.objects import Packet, Table, Path

class TridentContext(object):
    """
    A Trident context stores all the StreamAttribute schemas
    and gives access to network topology so that they can be
    used in a program.
    """
    def __init__(self, controller):
        self.parser = None
        self.compiler = None
        self.runtime = None
        self.controller = controller
        
        self.packets = []
        self.sa = {}

    def set_parser(self, parser):
        self.parser = parser

    def set_compiler(self, compiler):
        self.compiler = compiler

    def set_runtime(self, runtime):
        self.runtime = runtime

    def dfs(self, node, sport = ''):
        key = node[0]
        
        self.cp.append(key, sport)
        p = self.cp.formated_path()
        l = len(p) - 1
        if l > 0 and 'client' == self.nodes[p[0][0]]['role']:
            if 'aaa' == self.nodes[p[l][0]]['role']:
                self.p3.append(p)

            if 'server' == self.nodes[p[l][0]]['role']:
                self.p2.append(p)

                for edge in self.edges.values():
                    dst = edge['dst']
                    if len(dst) > 23:
                        dst = dst[0:23]

                    if 'dpi' == self.nodes[dst]['role']:
                        if self.cp.has(dst):
                            self.p1.append(p)
                            break
                        else:
                            src = edge['src']
                            if len(src) > 23:
                                src = src[0:23]

                            for tup in p:
                                if src == tup[0]:
                                    self.cp.multi_cast(src, edge['src'][24:])
                                    self.p1.append(self.cp.formated_path())
                                    self.cp.canceal_mc(src)
                                    break
        self.cp.pop()
                        
        for edge in self.edges.values():
            src = edge['src']
            if len(src) > 23:
                src = src[0:23]

            dst = edge['dst']
            if len(dst) > 23:
                dst = dst[0:23]

            self.cp.append(key, sport, edge['src'][24:])
            if src == key and not self.cp.has(dst):
                t = dst, self.nodes[dst]
                self.dfs(t, edge['dst'][24:])
            self.cp.pop()

    def set_topology(self, nodes, edges, DEBUG = False):
        self.nodes = nodes
        self.edges = edges
        
        self.cp = Path()
        self.p1 = []
        self.p2 = []
        self.p3 = []

        for node in self.nodes.items():
            self.dfs(node)

        if DEBUG:
            for p in self.p2:
                print(p)
                print("\n")

    def set_sa(self, name, pkt, value):
        if 'http_uri' == name:
            symbol = name + str(pkt)
        if 'authenticated' == name:
            symbol = name + pkt.sip 
        self.sa[symbol] = value

    def set_pkt(self, pkt):
        self.packets.append(pkt)

    '''
    table = {rule}
    rule:
    priority = 10
    match = {"sip": "192.168.1.1", "dip": ..., "sport": 20} same with Packet
    path = [("00:00:00:00:00:00:00:01", 1), (...)]
    '''
    def generate_rule(self, pkt):
        r = 'null'
        symbol_h = 'http_uri' + str(pkt)
        symbol_a = 'authenticated' + pkt.sip
        if symbol_a in self.sa and self.sa[symbol_a] == 'true':
            if symbol_h in self.sa and self.sa[symbol_h] == "www.xyz.com":
                for p in self.p2:
                    l = len(p)
                    if int(p[1][1][0]) == pkt.sport and p[l - 1][0] == pkt.dip:
                        self.table.add_rules([["2", pkt.sip, pkt.dip, pkt.sport, pkt.dport, pkt.ipproto, p], ["2", pkt.dip, pkt.sip, pkt.dport, pkt.sport, pkt.ipproto, self.reverse(p)]])
                        break
            else:
                for p in self.p1:
                    l = len(p)
                    if int(p[1][1][0]) == pkt.sport and p[l - 1][0] == pkt.dip:
                        self.table.add_rules([["2", pkt.sip, pkt.dip, pkt.sport, pkt.dport, pkt.ipproto, p], ["2", pkt.dip, pkt.sip, pkt.dport, pkt.sport, pkt.ipproto, self.reverse(p)]])
                        break
       
        # WARNING: hardcode to add default rule
        for p in self.p3:
            if int(p[1][1][0]) == pkt.sport:
                self.table.add_rules([["1", pkt.sip, '*', '*', '*', '*', p], ["1", '*', pkt.sip, '*', '*', '*', self.reverse(p)]])
                break
        
    def generate_table(self): 
        self.table = Table(['sip', 'dip', 'sport', 'dport', 'ipproto'], ['path'])
        for pkt in self.packets:
            self.generate_rule(pkt)
        return self.table

    def reverse(self, p):
        t = []
        for x in range(len(p) - 1, -1, -1):
            k = p[x]
            t.append([k[0], k[2], k[1]])
        return t
