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

    def dfs(self, node, port = 'None'):
        key, value = node
        l = self.cp.length()
        self.cp.append(node, port)


        if l > 1:
            if  'client' == self.cp.get_type(0):
                if 'aaa' == self.cp.get_type(l):
                    self.p3.append(self.cp.formated_path())

                if 'server' == self.cp.get_type(l):
                    self.p2.append(self.cp.formated_path())
                    flag = False
                    for i in [1, l - 1]:
                        if 'dpi' == self.cp.get_type(i):
                            flag = True
                    if flag:
                        self.p1.append(self.cp.formated_path())

        for edge in self.edges.values():
            src = edge['src']
            if len(src) > 23:
                src = src[0:23]

            dst = edge['dst']
            if len(dst) > 23:
                dst = dst[0:23]

            if src == key and not self.cp.has(dst):
                t = dst, self.nodes[dst]
                self.dfs(t, edge['src'][24:])

        self.cp.pop()

    def set_topology(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges
        
        self.cp = Path()
        self.p1 = []
        self.p2 = []
        self.p3 = []

        for node in self.nodes.items():
            self.dfs(node)

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
        symbol_h = 'http_uri' + str(pkt)
        symbol_a = 'authenticated' + pkt.sip
        if symbol_a in self.sa and self.sa[symbol_a] == 'true':
            if symbol_h in self.sa and self.sa[symbol_h] == "www.xyz.com":
                for p in self.p2:
                    l = p.length() - 1
                    if p.get(0) == pkt.sport and p.get(l) == pkt.dip:
                        r = p
                self.table.add_rules([["2", pkt.sip, pkt.dip, pkt.sport, pkt.dport, pkt.ipproto, r], ["2", pkt.dip, pkt.sip, pkt.dport, pkt.sport, pkt.ipproto, r.reverse()]])
            else:
                for p in self.p1:
                    l = p.length() - 1
                    if p.get(0) == pkt.sport and p.get(l) == pkt.dip:
                        r = p
                self.table.add_rules([["2", pkt.sip, pkt.dip, pkt.sport, pkt.dport, pkt.ipproto, r], ["2", pkt.dip, pkt.sip, pkt.dport, pkt.sport, pkt.ipproto, r.reverse()]])
        else:
            for p in self.p3:
                r = p
            self.table.add_rules([["1", pkt.sip, '*', '*', '*', '*', r], ["1", '*', pkt.sip, '*', '*', '*', r.reverse()]])
        
    def generate_table(self):
        self.ctx.packets.append(pkt)

        self.table = Table(['sip', 'dip', 'sport', 'dport', 'ipproto'], ['Path'])
        for pkt in self.ctx.packets:
            genearate_rule(pkt)
        return self.table
