from napps.snlab.trident_server.trident.tridentlib_hard import TridentContext
from napps.snlab.trident_server.trident.convertformat import convert_format
from kytos.core import KytosEvent

import logging


class TridentServer(object):
    def __init__(self):
        pass

    def set_ctx_controller(self, controller):
        self.ctx = TridentContext(controller)
        # self.test()

    def update_table(self, table):
        logging.info("update\n")
        logging.info(str(table))

        table = convert_format(table)
        logging.info("converted")
        logging.info(table)
        event = KytosEvent(name = 'snlab/ddp/setup', content = table)
        self.ctx.controller.buffers.app.put(event)

    def new_pkt(self, pkt):
        print('server_hard: new_pkt')
        self.ctx.set_pkt(pkt)
        print('server_hard: after ser_pkt')
        self.update_table(self.ctx.generate_table())

    def update_sa(self, sa_name, pkt, value):
        self.ctx.set_sa(sa_name, pkt, value)
        self.update_table(self.ctx.generate_table())

    def set_topology(self, nodes, edges):
        self.ctx.set_topology(nodes, edges)

    # def test(self):
    #     self.ctx.set_topology(None,None)

    def update_topology(self, nodes, edges):
        self.set_topology(nodes, edges)
        self.update_table(self.ctx.generate_table())
