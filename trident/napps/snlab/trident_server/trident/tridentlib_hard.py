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
        self.records = {}
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

    def set_topology(self, nodes, edges, DEBUG = True):
        self.nodes = nodes
        self.edges = edges
        
        self.cp = Path()
        self.p1 = []
        self.p2 = []
        self.p3 = []

        for node in self.nodes.items():
            self.dfs(node)

        if DEBUG:
            for p in self.p1:
                print(p)
                print("\n")

    def set_sa(self, name, pkt, value):
        if 'http_uri' == name:
            symbol = name + str(pkt)
        if 'authenticated' == name:
            symbol = name + pkt.sip 
        self.sa[symbol] = value

    def set_pkt(self, pkt):
        for t in self.packets:
            if str(t) == str(pkt):
                return
        self.packets.append(pkt)

    '''
    table = {rule}
    rule:
    priority = 10
    match = {"sip": "192.168.1.1", "dip": ..., "sport": 20} same with Packet
    path = [("00:00:00:00:00:00:00:01", 1), (...)]
    '''
    def generate_rule(self, pkt, topo_down = False):
        print('generate_rule')
        if topo_down and pkt in self.records.keys() and self.alive(self.records[pkt]):
            self.table.add_rules(self.records[pkt])
            return

        r = 'null'
        symbol_h = 'http_uri' + str(pkt)
        symbol_a = 'authenticated' + pkt.sip
        
        print('symbol_h' + symbol_h)
        print('stmbol_a' + symbol_a)
        print(str(self.sa))

        sp = 'null'
        if symbol_a in self.sa and self.sa[symbol_a] == 'true':
            if symbol_h in self.sa and self.sa[symbol_h] == "www.xyz.com":
                for p in self.p2:
                    l = len(p)
                    if p[0][0] == pkt.sip and p[l - 1][0] == pkt.dip:
                        if sp == 'null' or len(p) < len(sp):
                            sp = p      
                if not sp == 'null':
                    rules = [["2", pkt.sip, pkt.dip, pkt.sport, pkt.dport, pkt.ipproto, sp], ["2", pkt.dip, pkt.sip, pkt.dport, pkt.sport, pkt.ipproto, self.reverse(sp)]]
                    self.table.add_rules(rules)
                    self.records[pkt] = rules
            else:
                for p in self.p1:
                    l = len(p)
                    if p[0][0] == pkt.sip and p[l - 1][0] == pkt.dip:
                        if sp == 'null' or len(p) < len(sp):
                            sp = p
                if not sp == 'null':
                    rules = [["2", pkt.sip, pkt.dip, pkt.sport, pkt.dport, pkt.ipproto, sp], ["2", pkt.dip, pkt.sip, pkt.dport, pkt.sport, pkt.ipproto, self.reverse(sp)]]
                    self.table.add_rules(rules)
                    self.records[pkt] = rules
        else:
            for p in self.p3:
                if p[0][0] == pkt.sip:
                    if sp == 'null' or len(p) < len(sp):
                        sp = p
            if not sp == 'null':
                rules = [["1", pkt.sip, '*', '*', '*', '*', sp], ["1", '*', pkt.sip, '*', '*', '*', self.reverse(sp)]]
                self.table.add_rules(rules)
                self.records[pkt] = rules
        
    def generate_table(self, topo_down = False): 
        self.table = Table(['sip', 'dip', 'sport', 'dport', 'ipproto'], ['path'])
        print('tlib: generate_table')
        print(self.packets)
        for pkt in self.packets:
            self.generate_rule(pkt, topo_down)
        return self.table

    def alive(self, rules):
        p = rules[1][6]
        prv = 'null'
        for t in p:
            if not prv == 'null':
                flag = False
                for edge in self.edges.values():
                    src = edge['src']
                    if len(src) > 23:
                        src = src[0:23]

                    dst = edge['dst']
                    if len(dst) > 23:
                        dst = dst[0:23]

                    if src == prv and dst == t[0]:
                        flag = True
                        break
                if not flag: return False
            prv = t[0]

        return True

    def reverse(self, p): 
        t = []
        for x in range(len(p) - 1, -1, -1):
            k = p[x]
            if len(k[2]) > 1: # hardcode C -> DPI, S should be reversed to S -> DPI, C
                t.append([k[0], [k[2][0]], [k[1][0], k[2][1]]])
            else:
                t.append([k[0], k[2], k[1]])

        return t
