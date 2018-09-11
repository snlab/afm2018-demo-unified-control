from nccontainer.tunnel.ncctunnel_pb2 import nccontainer

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

from .utils import of_field_str2val


class Operation:
    ADD = 0
    MOD = 1
    DEL = 2

    def __init__(self, type, dpid, priority, match, action):
        """
        Operation encapsulation
        :param type: ADD,MOD,DEL
        :param dpid: dpid
        :param priority:
        :param match: {"src":1}
        :param action: {"output":[]}
        """
        self.type = type
        self.dpid = dpid
        self.priority = priority
        self.match = match
        self.action = action

    def to_ofmsg(self):
        # TODO openflow version
        flow_mod = FM13()
        flow_mod.command = FMC.OFPFC_ADD if self.type == Operation.ADD else (
            FMC.OFPFC_MODIFY if self.type == Operation.MOD else
            FMC.OFPFC_DELETE
        )
        flow_mod.priority = self.priority
        for f, v in self.match.items():
            field = of_field_str2val.get(f)
            assert field is not None  # TODO
            assert isinstance(v, bytes)  # TODO value type
            flow_mod.match.oxm_match_fields.append(OxmTLV(oxm_field=field, oxm_value=v))
        # Port13.OFPP_CONTROLLER
        if None not in self.action['output']:
            inst = InstructionApplyAction(actions=[AO13(port=p) for p in self.action['output']])
            flow_mod.instructions.append(inst)
        return flow_mod.pack()


def _id_generator():
    id = 0
    while True:
        yield id
        id += 1


class DependencyNode:
    INIT = 0
    EXECED = 1
    WAIT = 2
    __id_gen = _id_generator()

    def __init__(self, op):
        self.id = next(DependencyNode.__id_gen)
        self.op = op
        self.acquire = []
        self.release = []
        self.status = DependencyNode.INIT


class DependencyGraph:
    def __init__(self):
        self.nodes = []

    def __node2cid(self, node):
        # return str(node.op.dpid)+"-"+str(node.id)
        return str(self._tmpmap[node.op.dpid])+":"+str(node.id)

    def __dep2logicstr(self, dep_nodes):
        return "&".join(self.__node2cid(n) for n in dep_nodes)

    # def convert_to_container(self):
    #     cont_list = []
    #     for n in self.nodes:
    #         cont = nccontainer()
    #         cont.switch = n.op.dpid
    #         cont.op_id = self.__node2cid(n)
    #         cont.instruction = "TEST"
    #         cont.ack_from = self.__dep2logicstr(n.acquire)
    #         cont.ack_to = self.__dep2logicstr(n.release)
    #         cont.entry = n.op.to_ofmsg()
    #         cont_list.append(cont)
    #     return cont_list

    def convert_to_container(self, dpid2info):
        self._tmpmap = dpid2info
        from nccontainer.common.container import Container
        cont_list = []
        for n in self.nodes:
            dpid = n.op.dpid
            op_id = self.__node2cid(n)
            ack_from = self.__dep2logicstr(n.acquire)
            ack_to = self.__dep2logicstr(n.release)
            entry = n.op.to_ofmsg()
            cont_list.append(Container(dpid,op_id,ack_from,ack_to,entry))
        return cont_list

    def construct(self, priority, match, path1, path2):
        """
        construct black-hole-free dependency graph
        :param path1: path list before update, can be None or empty list []
        :param path2: path list after update, can be None or empty list []
        :return: dependency graph
        """
        dep = self
        node_map = self.__diff_path(priority, match, path1, path2)
        # dep.nodes = list(node_map.values())
        # return dep
        if not path1:
            if path2:
                first = node_map[path2[0][0]]
                for p,o in path2[1:]:
                    node = node_map[p]
                    node.acquire.append(first)
                    first.release.append(node)
                dep.nodes = list(node_map.values())
        else:
            if path2:
                firstmod = None
                for n, p in path2:
                    if n not in node_map:
                        continue
                    node = node_map[n]
                    if node.op.type == Operation.MOD:
                        if firstmod is not None:
                            node.release.append(firstmod)
                            firstmod.acquire.append(node)
                        firstmod = node
                    elif node.op.type == Operation.ADD:
                        if firstmod is not None:
                            node.release.append(firstmod)
                            firstmod.acquire.append(node)
                    else:
                        raise Exception("unexpected operation")
                for n, p in path1:
                    if n not in node_map:
                        continue
                    node = node_map[n]
                    if node.op.type == Operation.MOD:
                        firstmod = node
                    elif node.op.type == Operation.DEL:
                        if firstmod is not None:
                            node.acquire.append(firstmod)
                            firstmod.release.append(node)
                    else:
                        raise Exception("unexpected operation")
                dep.nodes = list(node_map.values())
            else:
                first = node_map[path1[0][0]]
                for p,o in path1[1:]:
                    node = node_map[p]
                    node.acquire.append(first)
                    first.release.append(node)
                dep.nodes = list(node_map.values())
        return dep

    def __diff_path(self, priority, match, path1, path2):
        node_map = {}
        path1_map = dict(path1) if path1 else {}
        path2_map = dict(path2) if path2 else {}
        for n, p in path2_map.items():
            if n in path1_map:
                if p != path1_map[n]:
                    node_map[n] = DependencyNode(Operation(
                        Operation.MOD,
                        n,
                        priority,
                        match,
                        {"output": p}
                    ))
            else:
                node_map[n] = DependencyNode(Operation(
                    Operation.ADD,
                    n,
                    priority,
                    match,
                    {"output": p}
                ))
        for n, p in path1_map.items():
            if n not in path2_map:
                node_map[n] = DependencyNode(Operation(
                    Operation.DEL,
                    n,
                    priority,
                    match,
                    {"output": p}
                ))
        return node_map
