"""Main module of snlab/DDP Kytos Network Application.

DDP with Update Algebra on Kytos
"""

from flask import jsonify, request

from kytos.core import KytosNApp, log, rest, KytosEvent
from napps.snlab.DDP import settings
from kytos.core.helpers import listen_to
from pyof.foundation.network_types import Ethernet, EtherType, IPv4
from pyof.foundation.basic_types import DPID, UBInt16, UBInt32
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

from nccontainer.controller.controller_plugin import ControllerPlugin


class Main(KytosNApp):
    """Main class of snlab/DDP NApp.

    This class is the entry point for this napp.
    """

    def setup(self):
        """Replace the '__init__' method for the KytosNApp subclass.

        The setup method is automatically called by the controller when your
        application is loaded.

        So, if you have any setup routine, insert it here.
        """
        self.plugin = ControllerPlugin()
        self.plugin.start()

    def execute(self):
        """This method is executed right after the setup method execution.

        You can also use this method in loop mode if you add to the above setup
        method a line like the following example:

            self.execute_as_loop(30)  # 30-second interval.
        """
        pass

    def shutdown(self):
        """This method is executed when your napp is unloaded.

        If you have some cleanup procedure, insert it here.
        """
        self.plugin.stop()

    @listen_to('kytos/of_core.handshake.completed')
    def install_default_flow(self, event):
        try:
            of_version = event.content['switch'].connection.protocol.version
        except AttributeError:
            of_version = None

        flow_mod = self._build_default_flow_mod(of_version)

        if flow_mod:
            name = 'kytos/of_lldp.messages.out.ofpt_flow_mod'
            content = {'destination': event.content['switch'].connection,
                       'message': flow_mod}
            event_out = KytosEvent(name=name, content=content)
            self.controller.buffers.msg_out.put(event_out)

    def _build_default_flow_mod(self, version):
        if version == 0x01:
            flow_mod = FM10()
            flow_mod.command = FMC.OFPFC_ADD
            flow_mod.priority = 0
            # flow_mod.match.dl_type = EtherType.LLDP
            flow_mod.actions.append(AO10(port=Port10.OFPP_CONTROLLER))
        elif version == 0x04:
            flow_mod = FM13()
            flow_mod.command = FMC.OFPFC_ADD
            flow_mod.priority = 0
            # match_lldp = OxmTLV()
            # match_lldp.oxm_field = OxmOfbMatchField.OFPXMT_OFB_ETH_TYPE
            # match_lldp.oxm_value = EtherType.LLDP.to_bytes(2, 'big')
            # flow_mod.match.oxm_match_fields.append(match_lldp)
            instruction = InstructionApplyAction()
            instruction.actions.append(AO13(port=Port13.OFPP_CONTROLLER))
            flow_mod.instructions.append(instruction)
        else:
            flow_mod = None
        return flow_mod

    @rest('v1/setup', methods=['POST'])
    def on_setup_rest(self):
        parm = request.get_json()
        log.info("on_setup_rest %s"%str(parm))
        return jsonify("Not support now"), 404

    @listen_to('snlab/ddp/setup')
    def on_setup(self, event):
        log.info("on_setup %s"%str(event.content))
        self.__setup_path(*event.content)

    @listen_to('kytos/topology.updated')
    def on_topology_update(self, event):
        from kytos.core.switch import Switch
        from kytos.core.link import Link
        from napps.kytos.topology.models import Topology
        topo = event.content['topology']
        log.info('topology update')

    def __setup_path(self, priority, match, path):
        self.plugin.setupPath(priority, match, path)

    @listen_to('kytos/of_core.v0x0[14].messages.in.ofpt_packet_in')
    def test(self, event):
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


