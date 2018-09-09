import networkx as nx
# FIXME add it back before push
#from kytos.core import KytosEvent

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

    def set_parser(self, parser):
        self.parser = parser

    def set_compiler(self, compiler):
        self.compiler = compiler

    def set_runtime(self, runtime):
        self.runtime = runtime

    def set_topology(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

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

class TridentServer(object):
    def __init__(self):
        self.program = ""
        self.ctx = None

    def set_ctx_controller(self, controller):
        self.ctx = TridentContext(controller)

    def submit(self, lark, program, debug=False):
        self.program = program

        from napps.snlab.trident_server.trident.parser import LarkParser
        self.ctx.set_parser(LarkParser(lark))
        self.ctx.parse(program)

        from napps.snlab.trident_server.trident.compiler import TridentCompiler
        self.ctx.set_compiler(TridentCompiler())
        if debug:
            print(self.ctx.ast.pretty())
        self.ctx.compile()

        # self.ctx.set_runtime(LvSystem)

    def new_pkt(self, pkt):
        self.ctx.runtime.new_pkt(pkt)
        # TODO Hardcode stub 1/3 onPacket: fake table with update_table() 

    def update_sa(self, sa_name, pkt, value):
        self.ctx.runtime.update_sa(sa_name, pkt, value)
        # TODO Hardcode stub 2/3 State update: fake table with update_table()

    def set_topology(self, nodes, edges):
        self.ctx.set_topology(nodes, edges)

    def update_topology(self, nodes, edges):
        # TODO Hardcode stub 3/3 Topology change: fake table with update_table()
        self.set_topology(nodes, edges)
        self.ctx.runtime.update_topology()
