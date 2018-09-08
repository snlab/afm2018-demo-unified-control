
import networkx as nx
from runtime import LvSystem

class TridentContext(object):
    """
    A Trident context stores all the StreamAttribute schemas
    and gives access to network topology so that they can be
    used in a program.
    """
    def __init__(self, parser, interpreter, runtime, controller):
        self.parser = parser
        self.interpreter = interpreter
        self.runtime = runtime
        self.controller = controller

    def set_topology(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def parse(self, program):
        self.ast = self.parser.parse(program)

    def interpret(self):
        self.vgraph, self.vnodes = self.interpreter.interpret(self.ast)
        return self.vgraph, self.vnodes

    def launch(self):
        self.runtime.launch(self.vgraph, self.vnodes)

    def stop(self):
        self.runtime.stop()

class TridentServer(object):
    def __init__(self):
        self.program = ""
        self.ctx = None
        self.controller = None

    def set_controller(self, controller):
        self.controller = controller

    def submit(self, lark, program, debug=False):
        self.program = program

        from parser import LarkParser
        from interpreter import LarkInterpreter

        self.ctx = TridentContext(LarkParser(lark),
                                  LarkInterpreter(), LvSystem(),
                                  self.controller)

        self.ctx.parse(program)

        if debug:
            print(self.ctx.ast.pretty())
        self.ctx.interpret()

    def update_sa(self, sa_name, pkt, value):
        self.ctx.runtime.new_value(sa_name, pkt, value)

    def new_pkt(self, pkt):
        self.ctx.runtime.new_packet(pkt)

def test_lark(larkfile, progfile):
    trident = TridentServer()

    with open(progfile) as f:
        program = f.read()
    trident.submit(larkfile, program, debug=True)
    for v in trident.ctx.vnodes:
        print(v['var'])


if __name__ == '__main__':
    import sys
    lark, prog = sys.argv[1:]
    test_lark(lark, prog)
