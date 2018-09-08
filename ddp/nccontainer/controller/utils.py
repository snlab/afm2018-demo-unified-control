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

of_field_str = ["eth_type",
                "ip_proto",
                "ip_src",
                "ip_dst",
                "tcp_src",
                "tcp_dst",
                "udp_src",
                "udp_dst"]
of_field_val = [OxmOfbMatchField.OFPXMT_OFB_ETH_TYPE,
                OxmOfbMatchField.OFPXMT_OFB_IP_PROTO,
                OxmOfbMatchField.OFPXMT_OFB_IPV4_SRC,
                OxmOfbMatchField.OFPXMT_OFB_IPV4_DST,
                OxmOfbMatchField.OFPXMT_OFB_TCP_SRC,
                OxmOfbMatchField.OFPXMT_OFB_TCP_DST,
                OxmOfbMatchField.OFPXMT_OFB_UDP_SRC,
                OxmOfbMatchField.OFPXMT_OFB_UDP_DST]

of_field_str2val = dict(zip(of_field_str, of_field_val))


def make_flow_key(priority, match):
    assert isinstance(match, dict)
    for f in match:
        assert f in of_field_str
    # TODO make default
    return (priority,) + tuple(match.get(f) for f in of_field_str)
