"""Main module of snlab/trident_server Kytos Network Application.

trident server
"""
from flask import jsonify, request
from struct import *

import threading

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

from napps.snlab.trident_server.trident.server_hard import TridentServer
from napps.snlab.trident_server.trident.objects import Packet as TridentPacket
from napps.snlab.trident_server.settings import CONFIG_LARK, HOST_ROLE

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
        # self.nodes = dict(settings.HOST_NODE)
        # self.edges = dict(settings.HOST_EDGE)
        # self.topology_not_set = True
        self.trident = TridentServer()
        self.trident.set_ctx_controller(self.controller)
        sa_name ='authenticated'
        # pkt = TridentPacket('10.0.0.2', '*', 0, 0, '*')
        # self.trident.update_sa(sa_name, pkt, 'Accept')
        # self.interface2DirLink = {}

        self.debug = False
        # self._system_ready = False
        self.lock = threading.Lock()
        self.sw_nodes = {}
        self.sw_links = {}  # {(swid, port):(swid, port)}

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
            if not self.debug:
                pass #trident.submit(CONFIG_LARK, program)
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
        log.info("SA_NAME"+sa_name)
        if sa_name == 'auth':
            sa_name = 'authenticated'
            sip = pkt[1:-1]
            pkt = TridentPacket(sip, '*', 0, 0, '*')
        # if sa_name == 'http_host':
        #     sa_name = 'http_uri'
        if sa_name == 'http_uri':
            flow = pkt[1:-1]
            sip,dip,sport,dport,proto = flow.split(',')
            sport = int(sport)
            dport = int(dport)
            pkt = TridentPacket(sip,dip,sport,dport,proto)
            
        value = request.args.get('value')
        if not self.debug:
            trident.update_sa(sa_name, pkt, value)
        log.info("Trident update_kv "+str(sa_name) + " " + str(pkt) + " " + str(value))
        return 'ok'


    ##############Packet In###############
    @listen_to('kytos/of_core.v0x0[14].messages.in.ofpt_packet_in')
    def packet_in(self, event):
        self.lock.acquire()

        from pyof.v0x04.asynchronous.packet_in import PacketIn
        msg = event.content['message']
        assert isinstance(msg, PacketIn)
        eth = Ethernet()
        eth.unpack(msg.data.value)
        #log.info('ethernet type=%s'%str(eth.ether_type))
        switch = event.source.switch
        in_port = msg.in_port
        # if eth.ether_type != 35020:
        #     log.info('ethernet type=%s'%str(eth.ether_type))
        if eth.ether_type == EtherType.IPV4:
            ipv4 = IPv4()
            ipv4.unpack(eth.data.value)

            if ipv4.destination == '10.0.0.254':
                pass
                #only for host locate
                # role = HOST_ROLE[ipv4.source]
                # self.nodes[ipv4.source] = {'role': role}
                #
                # h_id = ipv4.source
                # s_id = str(switch.dpid) + ":" + str(in_port)
                #
                # h2s_id = h_id + "+" + s_id
                # s2h_id = s_id + "+" + h_id
                # self.edges[h2s_id] = {'src': h_id, 'dst': s_id}
                # self.edges[s2h_id] = {'src': s_id, 'dst': h_id}
                # #TODO: need to handle host mobility
                # print(self.nodes)
                # print(self.edges)
                # if not self.debug:
                #     pass # self.trident.set_topology(self.nodes, self.edges)
            else:
                sip = ipv4.source
                dip = ipv4.destination
                ipproto = ipv4.protocol
                sport = None
                dport = None
                # allow_ip = ["10.0.0.1","10.0.0.2","10.0.0.3"]
                # if sip not in allow_ip:
                #     return
                # if dip not in allow_ip:
                #     return
                allow_pair =[("10.0.0.2","10.0.0.3"),("10.0.0.2","10.0.0.1")]
                if (sip,dip) not in allow_pair:
                    self.lock.release()
                    return
                if ipproto == 6:
                    ipproto = "tcp"
                elif ipproto == 17:
                    ipproto = "udp"
                else:
                    ipproto = "unknown"

                if ipproto == "tcp":
                    tcph = unpack('!HHLLBBHHH' , eth.data.value[20:40])
                    sport = tcph[0]
                    dport = tcph[1]
                elif ipproto == "udp":
                    udph = unpack('!HHHH', eth.data.value[20:28])
                    sport = udph[0]
                    dport = udph[1]
                else:
                    self.lock.release()
                    return
                    
                log.info("sip:" + str(sip) + "dip:" + str(dip) + str(ipproto) + "sport" + str(sport) + "dport" + str(dport))
                pkt = TridentPacket(sip, dip, sport, dport, ipproto)
                if not self.debug:
                    log.info('start to call trident new_pkt')
                    self.trident.new_pkt(pkt)
        self.lock.release()


    @listen_to('.*.switch.interface.down')
    def handle_interface_link_down(self, event):
        self.lock.acquire()

        log.debug("-----------LINK DOWN----------")
        interface = event.content['interface']
        log.debug("interface link down: " + str(interface.switch.dpid) + ":" +
                     str(interface.port_number))
        i = (interface.switch.dpid, interface.port_number)
        if i in self.sw_links:
            p1 = i
            p2 = self.sw_links[p1]
            log.info("handle_interface_link_down %s <--> %s"%(str(p1),str(p2)))
            self.sw_links.pop(p1)
            self.sw_links.pop(p2)
            self._reexec()


        self.lock.release()

    @listen_to('.*.interface.is.nni')
    def handle_new_link(self, event):
        self.lock.acquire()

        log.debug("--------handle_new_link-------------")
        interface_a = event.content['interface_a']
        a = (interface_a.switch.dpid, interface_a.port_number)
        interface_b = event.content['interface_b']
        b = (interface_b.switch.dpid, interface_b.port_number)
        need_update = False
        if a not in self.sw_links:
            assert b not in self.sw_links, "b in sw_links"
            log.info("handle_new_link %s <->%s"%(str(a),str(b)))
            self.sw_links[a]=b
            self.sw_links[b]=a
            self.__add_switch(a)
            self.__add_switch(b)
            self._reexec()
        if b not in self.sw_links:
            assert a not in self.sw_links, "a in sw_links"

        self.lock.release()

    def __add_switch(self, id):
        if id not in self.sw_nodes:
            self.sw_nodes[id]={'role': 'sw'}

    @listen_to('.*.switch.(new|reconnected)')
    def handle_new_switch(self, event):
        self.lock.acquire()

        switch = event.content['switch']
        log.debug('Switch %s added to the Topology.', switch.id)
        i = str(switch.id)
        if i not in self.sw_nodes:
            self.sw_nodes[i]= {'role': 'sw'}

        self.lock.release()

    @listen_to('.*.connection.lost')
    def handle_connection_lost(self, event):
        self.lock.acquire()

        switch = event.content['source'].switch
        if switch:
            log.debug('Switch %s removed from the Topology.', switch.id)
            i = str(switch.id)
            if i not in self.sw_nodes:
                log.error("i not in sw_nodes")
            else:
                self.sw_nodes.pop(i)
                changed = False
                for f,t in list(self.sw_links.items()):
                    if f[0]==i:
                        self.sw_links.pop(f)
                        changed=True
                    if t[0]==i:
                        self.sw_links.pop(f)
                        changed =True
                if changed:
                    self._reexec()

        self.lock.release()

    def __linkpairtostr(self, a):
        return str(a[0])+":"+str(a[1])

    def _reexec(self):
        log.info("reexec")
        for sw,port  in settings.HOST_ENDPOINT.values():
            if sw not in self.sw_nodes:
                log.warn("reexec %s not in %s"%(sw,str(self.sw_nodes)))
                return

        nodes = dict(self.sw_nodes)
        nodes.update(settings.HOST_NODE)
        links = { }
        for a,b in self.sw_links.items():
            astr = self.__linkpairtostr(a)
            bstr = self.__linkpairtostr(b)
            links[astr+"+"+bstr]={"src":astr, "dst":bstr}
        links.update(settings.HOST_EDGE)
        self.trident.update_topology(nodes, links)

    # @listen_to('.*.reachable.mac')
    # def handle_reachable_mac(self, event):
    #     switch = event.content['switch']
    #     port = event.content['port']
    #     reachable_mac = event.content['reachable_mac']
    #     log.info('find rm switch: ' + str(switch.id))
    #     log.info('find rm port: ' + str(port.port_number))
    #     log.info('find rm reachable_mac: ' + str(reachable_mac))

    # @listen_to('.*.interface.is.nni')
    # def handle_new_link(self, event):
    #     # if not self._system_ready:
    #     #     return
    #     log.info("--------handle_new_link-------------")
    #
    #
    #     interface_a = event.content['interface_a']
    #     interface_a_id = str(interface_a.switch.dpid) + ":" + str(interface_a.port_number)
    #     interface_b = event.content['interface_b']
    #     interface_b_id = str(interface_b.switch.dpid) + ":" + str(interface_b.port_number)
    #     linkId_ab = interface_a_id + "+" + interface_b_id
    #     linkId_ba = interface_b_id + "+" + interface_a_id
    #     need_update = False
    #
    #     if linkId_ab not in self.edges:
    #         self.edges[linkId_ab] = {'src': interface_a_id, 'dst': interface_b_id}
    #         self.interface2DirLink[interface_a_id] = linkId_ab
    #         need_update = True
    #
    #     if linkId_ba not in self.edges:
    #         self.edges[linkId_ba] = {'src': interface_b_id, 'dst': interface_a_id}
    #         self.interface2DirLink[interface_b_id] = linkId_ba
    #         need_update = True
    #
    #     if need_update:
    #         log.info("new link")
    #         # print(self.edges)
    #         if not self.debug:
    #             self.trident.set_topology(self.nodes, self.edges)



    #@listen_to('.*.switch.interface.link_up')
    #def handle_interface_link_up(self, event):
    #    interface = event.content['interface']
    #    log.info('interface link up: ' + str(interface.switch.dpid) + ":" +
    #             str(interface.port_number))




    # @listen_to('.*.switch.interface.link_down')
    # def handle_interface_link_down(self, event):
    #
    #     log.info("-----------LINK DOWN----------")
    #
    #     # if not self._system_ready:
    #     #     return
    #     interface = event.content['interface']
    #     log.info("interface link down: " + str(interface.switch.dpid) + ":" +
    #              str(interface.port_number))
    #     interfaceId = str(interface.switch.dpid) + ":" +str(interface.port_number)
    #     linkId = self.interface2DirLink[interfaceId]
    #     self.edges.pop(linkId)
    #     self.interface2DirLink.pop(interfaceId)
    #
    #     log.info("-----------LINK DOWN----------")
    #     print(self.edges)
    #
    #     if not self.debug:
    #         self.trident.set_topology(self.nodes, self.edges)

    # useless
    # @listen_to('.*.switch.port.deleted')
    # def handle_port_deleted(self, event):
    #     switch = event.content['switch']
    #     port = event.content['port']
    #
    #     interfaceId = str(switch.dpid) + ":" + str(port)
    #     linkId = self.interface2DirLink[interfaceId]
    #     self.edges.pop(linkId)
    #     self.interface2DirLink.pop(interfaceId)
    #
    #     print('port deleted')
    #     print(self.edges)
    #
    #     if not self.debug:
    #         self.trident.set_topology(self.nodes, self.edges)

    # @listen_to('kytos/topology.updated')
    # def handle_topology_update(self, event):
    #     topology = event.content['topology']
    #     if self.topology_not_set:
    #         self.set_nodes(topology)
    #         self.set_edges(topology)
    #
    #         print("topology update")
    #         print(self.nodes)
    #         print(self.edges)
    #
    #         if not self.debug:
    #             self.trident.set_topology(self.nodes, self.edges)
    #
    #         self.topology_not_set = False

    # def set_nodes(self, topology):
    #     switches = topology.switches
    #     for key in switches:
    #         switch_dpid = key
    #         self.nodes[str(switch_dpid)] = {"role": "sw"}
    #
    # def set_edges(self, topology):
    #     links = topology.links
    #     for key in links:
    #         link = links[key]
    #         endpoint_a = link.endpoint_a
    #         endpoint_a_id = str(endpoint_a.switch.dpid) + ":" + str(endpoint_a.port_number)
    #
    #         endpoint_b = link.endpoint_b
    #         endpoint_b_id = str(endpoint_b.switch.dpid) + ":" + str(endpoint_b.port_number)
    #
    #         link_id_ab = str(endpoint_a_id) + "+" + str(endpoint_b_id)
    #         link_id_ba = str(endpoint_b_id) + "+" + str(endpoint_a_id)
    #
    #         self.edges[link_id_ab] = {"src": str(endpoint_a_id), "dst":
    #                                   str(endpoint_b_id)}
    #         self.edges[link_id_ba] = {"src": str(endpoint_b_id), "dst":
    #                                   str(endpoint_a_id)}
    #
    #         self.interface2DirLink[str(endpoint_a_id)] = link_id_ab
    #         self.interface2DirLink[str(endpoint_b_id)] = link_id_ba


    def shutdown(self):
        """This method is executed when your napp is unloaded.

        If you have some cleanup procedure, insert it here.
        """
        pass
