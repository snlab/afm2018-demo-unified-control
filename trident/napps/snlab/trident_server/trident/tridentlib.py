
import networkx as nx
from kytos.core import KytosEvent

from napps.snlab.trident_server.trident.runtime import LvSystem


class TridentContext(object):
    """
    A Trident context stores all the StreamAttribute schemas
    and gives access to network topology so that they can be
    used in a program.
    """
    def __init__(self, controller):
        self.parser = None
        self.interpreter = None
        self.runtime = None
        self.controller = controller

    def set_parser(self, parser):
        self.parser = parser

    def set_interpreter(self, interpreter):
        self.interpreter = interpreter

    def set_runtime(self, runtime):
        self.runtime = runtime

    '''
    ctx.nodes = { "s1": { "role": "sw"  }, "s2": { "role": "sw"  }, "h1": {
    "role": "client"  }, "h2": { "role": "server"  }, "dpi1": { "role": "dpi"
    }, "dpi2": { "role": "dpi"  }  }

    ctx.edges = { "e1": { "src": "s1:1", "dst": "h1:1", "capacity": 100  },
    "e2": { "src": "h1:1", "dst": "s1:1", "capacity": 100  }, "e3": { "src":
        "s2:1", "dst": "h2:1", "capacity": 10  }, "e4": { "src": "h2:1", "dst":
            "s2:1", "capacity": 10 }, "e5": { "src": "s1:2", "dst": "h2:2",
            "capacity": 100  }, "e6": { "src": "h2:1", "dst": "s1:2",
            "capacity": 100  }, "e7": { "src": "s2:2", "dst": "h1:2",
            "capacity": 10  }, "e8": { "src": "h1:2", "dst": "s2:2",
            "capacity": 10  }, "e9": { "src": "s1:3", "dst": "s2:3",
            "capacity": 10  }, "e10": { "src": "s2:3", "dst": "s1:3",
            "capacity": 10  }, "e11": { "src": "s1:4", "dst": "dpi1:1",
            "capacity": 10  }, "e12": { "src": "dpi1:1", "dst": "s1:4",
            "capacity": 10  }, "e13": { "src": "s2:4", "dst": "dpi2:1",
            "capacity": 10  }, "e14": { "src": "dpi2:1", "dst": "s2:4",
            "capacity": 10  }  }
    except: 1. without capacity; 2. s1 -> 00:00:00:00:00:00:00:01
    '''
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
    def update_table(self, table):
        event = KytosEvent(name = 'snlab/ddp/setup', content = table)
        self.controller.buffers.app.put(event)

    def parse(self, program):
        self.ast = self.parser.parse(program)

    def interpret(self):
        self.vgraph, self.vnodes = self.interpreter.interpret(self.ast)
        return self.vgraph, self.vnodes

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

        from parser import LarkParser
        from interpreter import LarkInterpreter

        self.ctx.set_parser(LarkParser(lark))
        self.ctx.set_interpreter(LarkInterpreter)
        self.ctx.set_runtime(LvSystem)

        self.ctx.parse(program)

        if debug:
            print(self.ctx.ast.pretty())
        self.ctx.interpret()

    def update_sa(self, sa_name, pkt, value):
        self.ctx.runtime.new_value(sa_name, pkt, value)

    def new_pkt(self, pkt):
        self.ctx.runtime.new_packet(pkt)

    def set_topology(self, nodes, edges):
        self.ctx.set_topology(nodes, edges)

    def update_topology(self, nodes, edges):
        pass

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
