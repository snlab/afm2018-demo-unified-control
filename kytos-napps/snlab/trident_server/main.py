"""Main module of snlab/trident_server Kytos Network Application.

trident server
"""
from flask import jsonify, request

from kytos.core import KytosNApp, log, rest
from kytos.core.helpers import listen_to

from pyof.foundation.network_types import Ethernet, EtherType, IPv4
from pyof.foundation.basic_types import DPID, UBInt16, UBInt32
from pyof.foundation.basic_types import IPAddress
from pyof.foundation.network_types import LLDP, Ethernet, EtherType, VLAN
from pyof.v0x01.common.action import ActionOutput as AO10
from pyof.v0x01.common.phy_port import Port as Port10
from pyof.v0x01.controller2switch.flow_mod import FlowMod as FM10
from pyof.v0x01.controller2switch.flow_mod import FlowModCommand as FMC
from pyof.v0x01.controller2switch.packet_out import PacketOut as PO10
from pyof.v0x04.common.action import ActionOutput as AO13
from pyof.v0x04.common.flow_instructions import InstructionApplyAction
from pyof.v0x04.common.flow_match import OxmOfbMatchField, OxmTLV, VlanId
from pyof.v0x04.common.port import PortNo as Port13
from pyof.v0x04.controller2switch.flow_mod import FlowMod as FM13
from pyof.v0x04.controller2switch.packet_out import PacketOut as PO13

from napps.snlab.trident_server import settings

# from napps.snlab.trident_server.trident import server as S
# from gevent import spawn

from napps.snlab.trident_server.trident.tridentlib import TridentServer
from napps.snlab.trident_server.settings import CONFIG_LARK

class Main(KytosNApp):
    """Main class of snlab/trident_server NApp.

    This class is the entry point for this napp.
    """

    # def run_trident_server(self):
    #     log.info('start to run')
    #     S.trident.set_ctx_controller(self.controller)
    #     S.http_server.serve_forever()

    def setup(self):
        """Replace the '__init__' method for the KytosNApp subclass.

        The setup method is automatically called by the controller when your
        application is loaded.

        So, if you have any setup routine, insert it here.
        """
        self.nodes = {}
        self.edges = {}
        self.topology_not_set = True
        self.trident = TridentServer()
        self.trident.set_ctx_controller(self.controller)
        log.info('Main setup')

    def execute(self):
        """This method is executed right after the setup method execution.

        You can also use this method in loop mode if you add to the above setup
        method a line like the following example:

            self.execute_as_loop(30)  # 30-second interval.
        """
        # spawn(self.run_trident_server)
        log.info('Main execute')


    ###########RESTful API##########

    # http://127.0.0.1:8181/api/snlab/trident_server/v1/index
    @rest('v1/index')
    def index(self):
        return "Hello World"


    @rest('v1/submit', methods=['POST'])
    def submit_program(self):
        trident = self.trident
        program = request.data
        try:
            trident.submit(CONFIG_LARK, program)
            return 'ok'
        except Exception as e:
            raise e

    @rest('v1/ast')
    def read_program(self):
        trident = self.trident
        return trident.ctx.ast.pretty()   

    @rest('v1/tridentkv')
    def update_kv(self):
        trident = self.trident
        pkt = request.args.get('flow')
        sa_name = request.args.get('key')
        value = request.args.get('value')
        trident.update_sa(sa_name, pkt, value)
        return 'ok'


    ##############Packet In###############
    @listen_to('kytos/of_core.v0x0[14].messages.in.ofpt_packet_in')
    def packet_in(self, event):
        from pyof.v0x04.asynchronous.packet_in import PacketIn
        msg = event.content['message']
        assert isinstance(msg, PacketIn)
        eth = Ethernet()
        eth.unpack(msg.data.value)
        log.info('ethernet type=%s'%str(eth.ether_type))
        if eth.ether_type == EtherType.IPV4:
            ipv4 = IPv4()
            ipv4.unpack(eth.data.value)
            log.info(ipv4.source)
            log.info(ipv4.destination)

            # TODO add filter
            # TODO: the format of packet
            # trident.new_pkt(ipv4)    


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

            self.trident.ctx.set_topology(self.nodes, self.edges)

            self.trident.ctx.test()

    def set_nodes(self, topology):
        switches = topology.switches
        for key in switches:
            switch_dpid = key
            self.nodes[str(switch_dpid)] = {"role": "sw"}

    def set_edges(self, topology):
        links = topology.links
        for key in links:
            link = links[key]
            endpoint_a = link.endpoint_a
            endpoint_a_id = str(endpoint_a.switch.dpid) + ":" + str(endpoint_a.port_number)

            endpoint_b = link.endpoint_b
            endpoint_b_id = str(endpoint_b.switch.dpid) + ":" + str(endpoint_b.port_number)

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
