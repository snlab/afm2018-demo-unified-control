"""Main module of snlab/trident_server Kytos Network Application.

trident server
"""

from kytos.core import KytosNApp, log

from napps.snlab.trident_server import settings
from kytos.core.helpers import listen_to


from gevent import spawn

class Main(KytosNApp):
    """Main class of snlab/trident_server NApp.

    This class is the entry point for this napp.
    """

    def run_trident_server(self):
        from napps.snlab.trident_server.trident import server as S
        S.trident.set_controller(self.controller)
        S.http_server.serve_forever()

    def setup(self):
        """Replace the '__init__' method for the KytosNApp subclass.

        The setup method is automatically called by the controller when your
        application is loaded.

        So, if you have any setup routine, insert it here.
        """
        self.nodes = {}
        self.edges = {}
        self.topology_not_set = True
        log.info('trident server start')

    def execute(self):
        """This method is executed right after the setup method execution.

        You can also use this method in loop mode if you add to the above setup
        method a line like the following example:

            self.execute_as_loop(30)  # 30-second interval.
        """
        spawn(self.run_trident_server)
        log.info('trident server execute')

    @listen_to('.*.reachable.mac')
    def handle_reachable_mac(self, event):
        switch = event.content['switch']
        port = event.content['port']
        reachable_mac = event.content['reachable_mac']
        log.info('find rm switch: ' + str(switch.id))
        log.info('find rm port: ' + str(port.port_number))
        log.info('find rm reachable_mac: ' + str(reachable_mac))

    @listen_to('.*.switch.interface.link_up')
    def handle_interface_link_up(self, event):
        interface = event.content['interface']
        log.info('interface link up: ' + str(interface.switch.dpid) + ":" +
                 str(interface.port_number))

    @listen_to('.*.switch.interface.link_down')
    def handle_interface_link_down(self, event):
        interface = event.content['interface']
        log.info("interface link down: " + str(interface.switch.dpid) + ":" +
                 str(interface.port_number))

    @listen_to('kytos/topology.updated')
    def handle_topology_update(self, event):
        topology = event.content['topology']
        if self.topology_not_set:
            self.set_nodes(topology)
            self.set_edges(topology)

            S.trident.ctx.set_topology(self.nodes, self.edges)

            S.trident.ctx.test()

    def set_nodes(self, topology):
        switches = topology.switches
        for key in switches:
            switch_dpid = key
            self.nodes[str(switch_dpid)] = {"role": "sw"}

    def set_edges(self, topology):
        links = topology.links
        for key in links:
            link = links[key]
            endpoint_a = link['endpoint_a']
            endpoint_a_id = endpoint_a['id']

            endpoint_b = link['endpoint_b']
            endpoint_b_id = endpoint_b['id']

            link_id_ab = str(endpoint_a_id) + "+" + str(endpoint_b_id)
            link_id_ba = str(endpoint_b_id) + "+" + str(endpoint_a_id)

            self.edges[link_id_ab] = {"src": str(endpoint_a_id), "dst":
                                      str(endpoint_b_id)}
            self.edges[link_id_ba] = {"src": str(endpoint_b_id), "dst":
                                      str(endpoint_a_id)}


    def shutdown(self):
        """This method is executed when your napp is unloaded.

        If you have some cleanup procedure, insert it here.
        """
        pass
