from napps.snlab.trident_server.trident.tridentlib_hard import TridentContext
from kytos.core import KytosEvent

class TridentServer(object):
    def __init__(self):
        pass

    def set_ctx_controller(self, controller):
        self.ctx = TridentContext(controller)

    def update_table(self, table):
        event = KytosEvent(name = 'snlab/ddp/setup', content = table)
        self.ctx.controller.buffers.app.put(event)

    def new_pkt(self, pkt):
        self.ctx.set_pkt(pkt)
        self.update_table(self.ctx.generate_table())

    def update_sa(self, sa_name, pkt, value):
        self.ctx.set_sa(sa_name, pkt, value)
        self.update_table(self.ctx.generate_table())

    def set_topology(self, nodes, edges):
        self.ctx.set_topology(nodes, edges)

    def update_topology(self, nodes, edges):
        self.set_topology(nodes, edges)
        self.update_table(self.ctx.generate_table(), True)
