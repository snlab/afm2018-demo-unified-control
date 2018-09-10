from napps.snlab.trident_server.trident.objects import Packet, Table
# FIXME add it back before push
#from kytos.core import KytosEvent

class Path(object):
    def __init__(self):
        self.nodes = []

    def append(self, node):
        self.nodes.append(node)
    
    def pop(self):
        self.nodes.pop()

    def length(self):
        return len(self.nodes)

    def reverse(self):
        p = Path()
        for node in self.nodes:
            p.append(node)
        p.nodes.reverse()
        return p

    def get_type(self, pos):
        return self.nodes[pos] # FIXME

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

    def dfs(self, node):
        l = self.cp.len() - 1
        self.cp.append(node)

        if l > 0:
            if self.cp.get_type(0) == 'client':
                if self.cp.get_type(l) == 'aaa':
                    self.p3.append(self.cp)

                if self.cp.get_type(l) == 'server':
                    self.p2.append(self.cp)
                    flag = false
                    for i in [1, l - 1]:
                        if self.cp.get_type(i) == 'dpi':
                            flag = true
                    if flag:
                        self.p1.append(self.cp)
        
        for edge in edges:
            if edge[0] == node and not edge[1] in node:
                dfs(edge[1])
            if edge[1] == node and not edge[0] in node:
                dfs(edge[0])

        self.cp.pop()

    def set_topology(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges
        
        self.cp = Path()
        self.p1 = []
        self.p2 = []
        self.p3 = []
        for node in self.nodes:
            dfs(node)

    def set_sa(self, name, pkt, value):
        if 'http_uri' == name:
            symbol = name + ":" + str(pkt)
        if 'authenticated' == name:
            symbol = name + ":" + pkt.sip 
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
    #FIXME add it back before push
    #def update_table(self, table):
        #event = KytosEvent(name = 'snlab/ddp/setup', content = table)
        #self.controller.buffers.app.put(event)

    def parse(self, program):
        self.ast = self.parser.parse(program)

    def compile(self):
        self.tables = self.compiler.do_compile(self.ast)
        return self.tables

    def launch(self):
        self.runtime.launch(self.vgraph, self.vnodes)

    def stop(self):
        self.runtime.stop()

    def test(self):
        print(len(self.nodes))
        print(len(self.edges))

    def generate_rule(self, pkt):
        symbol_h = 'http_uri' + str(pkt)
        symbol_a = 'authenticated' + pkt.sip
        if symbol_a in self.sa:
            if symbol_h in self.sa and self.sa[symbol_h] == 'www.xyz.com':
                for p in self.p2:
                    l = p.length() - 1
                    if p.get(0) == pkt.sport and p.get(l) == pkt.dip:
                        r = p
                self.table.add_rules([["1", pkt.sip, pkt.dip, pkt.sport, pkt.dport, pkt.ipproto, r],
                                      ["1", pkt.dip, pkt.sip, pkt.dport, pkt.sport, pkt.ipproto, r.reverse()])
             else:
                for p in self.p1:
                    l = p.length() - 1
                    if p.get(0) == pkt.sport and p.get(l) == pkt.dip:
                        r = p
                self.table.add_rules([["1", pkt.sip, pkt.dip, pkt.sport, pkt.dport, pkt.ipproto, r],
                                      ["1", pkt.dip, pkt.sip, pkt.dport, pkt.sport, pkt.ipproto, r.reverse()])
        else:
            for p in self.p3:
                r = p
            self.table.add_rules([["1", pkt.sip, pkt.dip, pkt.sport, pkt.dport, pkt.ipproto, r],
                                  ["1", pkt.dip, pkt.sip, pkt.dport, pkt.sport, pkt.ipproto, r.reverse()])
        
    def generate_table(self):
        self.ctx.packets.append(pkt)

        self.table = Table(["sip", "dip", "sport", "dport", "ipproto"])
        for pkt in self.ctx.packets:
            genearate_rule(pkt)
        return self.table

class TridentServer(object):
    def __init__(self):
        self.program = ""
        self.ctx = None

    def set_ctx_controller(self, controller):
        self.ctx = TridentContext(controller)

    def submit(self, lark, program, debug=False):
        if not debug: # FIXME Hard-coded
            return 
        
        self.program = program

        from napps.snlab.trident_server.trident.parser import LarkParser
        self.ctx.set_parser(LarkParser(lark))
        self.ctx.parse(program)

        from napps.snlab.trident_server.trident.compiler import tc
        self.ctx.set_compiler(tc)
        if debug:
            print(self.ctx.ast.pretty())
        self.ctx.compile()
        # self.ctx.set_runtime(LvSystem)

    def new_pkt(self, pkt):
        # self.ctx.runtime.new_pkt(pkt)
        # Hardcode stub 1/3 onPacket: fake table with update_table() 
        self.ctx.set_pkt(pkt)
        return self.ctx.generate_table()

    def update_sa(self, sa_name, pkt, value):
        # Hardcode stub 2/3 State update: fake table with update_table()
        self.ctx.set_sa(sa_name, pkt, value)
        return self.ctx.generate_table()

    def set_topology(self, nodes, edges):
        self.ctx.set_topology(nodes, edges)

    def update_topology(self, nodes, edges):
        # Hardcode stub 3/3 Topology change: fake table with update_table()
        self.set_topology(nodes, edges)
        return self.ctx.generate_table()
