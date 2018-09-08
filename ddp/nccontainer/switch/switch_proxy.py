import select
import socket
import struct
import threading
import time
from datetime import datetime

from pyof.utils import unpack, UnpackException
from pyof.v0x01.common.header import Type

from nccontainer.common.logger import logger
from nccontainer.tunnel import ncctunnel_pb2, spcomunication_pb2

headerSize = 12
ack_fromQueue = set()
pendingBackAck = []


class com_end():
    def __init__(self, ip_addr, ip_port):
        self.addr = ip_addr
        self.port = ip_port


class backAck():
    def __init__(self, server, data):
        self.sender = server
        self.data = data


class operation_entry():
    def __init__(self, type, switch_addr, container_id):
        '''
        PUSH = 0
        PULL = 1
        MAP = 2
        '''
        self.type = type
        self.switch_addr = switch_addr
        self.container_id = container_id


class container():
    def __init__(self, container_id, container_op, switch_addr, entry, ack_from, ack_to):
        """
        :param container_id: "00:00:00:00:00:00:00:00-12345"
        :param container_op: "TEST" or other
        :param switch_addr: "00:00:00:00:00:00:00:00"
        :param entry: b'openflowmsg'
        :param ack_from: "a&b|c"
        :param ack_to: "d&e|f"
        """
        self.id = container_id
        self.optype = container_op
        self.switch_addr = switch_addr
        self.entry = entry
        self.ack_from = ack_from
        self.ack_to = ack_to
        self.ack_from_list = self.__parse_ack(ack_from)
        self.ack_to_list = self.__parse_ack(ack_to)
        self.state = False
        self.__update_state()
        # self.linkfailure = False

    def __parse_ack(self, logic_str):
        return [{cid:False for cid in and_str.split('&') if len(cid)>24}
                for and_str in logic_str.split('|')]

    def __str__(self):
        return "id='%s'; dpid='%s'; ack_from='%s'; ack_to='%s'" % (self.id, self.switch_addr, self.ack_from, self.ack_to)

    def receive_ack(self):
        self.__update_state()

    def get_ack_to_sw(self):
        if self.ack_to_list:
            return [cid[0:23] for cid in self.ack_to_list[0]]
        else:
            return []

    def __update_state(self):
        if not self.ack_from_list:
            self.state=True
            return
        ackList = set()
        for item in ack_fromQueue:
            ackList.add(str(item.container_id))
        for and_map in self.ack_from_list:
            for cid in and_map:
                if cid in ackList:
                    and_map[cid]=True
        self.state = any(all(and_map.values()) for and_map in self.ack_from_list)


class SwitchProxy:
    input_list = []
    ofchannelIndex = {}
    tunnelIndex = {}
    tun2IDX = {}
    tun2ofchannel = {}
    ofchannel2tun = {}
    tunnels = set()
    ofchannels = set()
    switch_addr2sproxy_addr = {}
    pending_container = []
    ackReceieved_list = []
    tun2buffer = {}
    ofchaneldata = {}
    senderdata = {}

    def __init__(self, host, port, forward_addr, forward_port,
                 buffer_size=65536, delay=0.0001, broadcast_port=1060, operation_port=1070):
        self.forward_addr = forward_addr
        self.forward_port = forward_port
        self.buffer_size = buffer_size
        self.delay = delay
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(5)
        self.host = host
        self.block = False

        # UDP broadcast sproxy-switch mapping relationship
        self.broadserver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadserver.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_port = broadcast_port
        self.broadclient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadclient.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadclient.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.broadclient.bind(("255.255.255.255", self.broadcast_port))

        # PUSH and PULL listen server
        self.operation_port = operation_port
        self.operation_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.operation_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.operation_server.bind((host, self.operation_port))
        self.s = None

    def main_loop(self):
        global pendingBackAck
        self.input_list.append(self.server)
        self.input_list.append(self.broadclient)
        self.input_list.append(self.operation_server)
        while True:
            time.sleep(self.delay)
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])
            senderdata = {}
            for item in pendingBackAck:
                if item.sender in senderdata.keys():
                    senderdata[item.sender] += item.data
                else:
                    senderdata[item.sender] = item.data
            for sender in senderdata.keys():
                sender.send(senderdata[sender])
            del pendingBackAck[:]

            for self.s in inputready:
                if self.s == self.server:
                    self.on_accept()
                else:
                    self.data = self.s.recv(self.buffer_size)
                    if self.s in self.tunnels:
                        if len(self.data) == 0:
                            self.on_close()
                            break

                        else:
                            if self.s not in self.tun2buffer.keys():
                                self.tun2buffer[self.s] = bytes()
                            self.tun2buffer[self.s] += self.data
                            while True:
                                if len(self.tun2buffer[self.s]) < headerSize:
                                    break
                                else:
                                    headPack = struct.unpack('!3I', self.tun2buffer[self.s][:headerSize])
                                    bodySize = headPack[1]
                                    if len(self.tun2buffer[self.s]) < headerSize + bodySize:
                                        logger.debug("not a complicated packet")
                                        break
                                    else:
                                        self.data = self.tun2buffer[self.s][headerSize:headerSize + bodySize]
                                        self.tun2buffer[self.s] = self.tun2buffer[self.s][headerSize + bodySize:]
                                        self.on_recv()
                    else:
                        if len(self.data) == 0:
                            self.on_close()
                            break
                        else:
                            self.on_recv()

    def on_accept(self):
        ofsock, clientaddr = self.server.accept()
        tunnel_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tunnel_sock.connect((self.forward_addr, self.forward_port))
            logger.info("establish successfully %s"%str(clientaddr))
        except:
            logger.error("can not estabilsh tunnel")
        self.ofchannel2tun[ofsock] = tunnel_sock
        self.tun2ofchannel[tunnel_sock] = ofsock
        self.tunnels.add(tunnel_sock)
        self.ofchannels.add(ofsock)
        self.input_list.append(ofsock)
        self.input_list.append(tunnel_sock)

    def on_recv(self):
        data = self.data
        if self.s in self.ofchannels:
            logger.debug("Push in tunnel")
            self.push_in_tunnel(data)
        elif self.s == self.broadclient:
            logger.debug("on_recv update_ovs2sp")
            self.update_ovs2sp(data.decode('utf-8'))
        elif self.s == self.operation_server:
            self.process_operationmsg(data)
        else:
            logger.debug("Pop out tunnel")
            self.pop_out_tunnel(data)

    def encapsulate(self, data):
        """
        encapsulate of_message with container_operation
        """
        nccontainer = ncctunnel_pb2.nccontainer()
        nccontainer.entry = data
        return nccontainer

    def push_in_tunnel(self, data):
        """
        of -> tunnel
        """
        global pendingBackAck

        if self.s in self.ofchaneldata.keys():
            self.ofchaneldata[self.s] += data
        else:
            self.ofchaneldata[self.s] = data
        lenth = int.from_bytes(self.ofchaneldata[self.s][2:4], byteorder='big')
        if lenth > len(self.ofchaneldata[self.s]):
            logger.debug("not complicated packet")
            return
        else:
            data = self.ofchaneldata[self.s][:lenth]
            self.ofchaneldata[self.s] = self.ofchaneldata[self.s][lenth:]
        try:
            of_msg = unpack(data)
            logger.debug("OpenFlow Message Type: %s" % of_msg.header.message_type)
            if of_msg.header.message_type == Type.OFPT_FEATURES_REPLY:
                logger.debug("accept Type.OFPT_FEATURES_REPLY")
                self.bind_tun_ofchannel(of_msg)
                self.broadcast_ovs2sp(of_msg.datapath_id.value)
            elif of_msg.header.message_type == Type.OFPT_PORT_STATUS:
                # self.receievePortStatus(data)
                logger.debug(" ingore port status ")
            elif of_msg.header.message_type == Type.OFPT_ERROR:
                logger.debug(of_msg.error_type)
        except:
            logger.debug("Non OpenFlow Message")

        nccontainer = self.encapsulate(data)
        self.ofchaneldata[self.s] = bytes()
        size = nccontainer.ByteSize()
        nccontainer = nccontainer.SerializeToString()
        ver = 1
        cmd = 101
        header = [ver, size, cmd]
        headPack = struct.pack("!3I", *header)

        data = headPack + nccontainer

        if len(pendingBackAck):
            senderdata = {}
            for item in pendingBackAck:
                if item.sender in senderdata.keys():
                    senderdata[item.sender] += item.data
                else:
                    senderdata[item.sender] = item.data
            for sender in senderdata.keys():
                if sender == self.ofchannel2tun[self.s]:
                    data += senderdata[sender]
                    pendingBackAck = [item for item in pendingBackAck if item.sender != self.s]
                    break
        self.ofchannel2tun[self.s].send(data)

    def pop_out_tunnel(self, tunneldata):
        """
        tunnel -> of
        """
        global pendingBackAck

        nccontainer = ncctunnel_pb2.nccontainer()
        nccontainer.ParseFromString(tunneldata)
        data = nccontainer.entry
        if nccontainer.instruction == "TEST":
            self.block = True
            logger.debug(str(datetime.now()))
            newcontainer = container(nccontainer.op_id, nccontainer.instruction, nccontainer.switch, nccontainer.entry,
                                     nccontainer.ack_from, nccontainer.ack_to)
            logger.info("new container "+str(newcontainer))
            self.pending_container.append(newcontainer)
            if newcontainer.state:
                self.__exec(newcontainer)

        # elif nccontainer.instruction == "Centralized":
        #     size = nccontainer.ByteSize()
        #     nccontainer = nccontainer.SerializeToString()
        #     ver = 1
        #     cmd = 101
        #     header = [ver,size, cmd]
        #     headPack = struct.pack("!3I", *header)
        #
        #     pendingBackAck.append(backAck(self.s,headPack+nccontainer))
        #     # self.s.send(headPack+nccontainer)
        else:
            if self.s in self.senderdata.keys():
                self.senderdata[self.s] += data
            else:
                self.senderdata[self.s] = data

            lenth = int.from_bytes(self.senderdata[self.s][2:4], byteorder='big')

            if lenth > len(self.senderdata[self.s]):
                logger.debug("not complicated packet")
                return
            else:
                data = self.senderdata[self.s][:lenth]
                self.senderdata[self.s] = self.senderdata[self.s][lenth:]  # NOTE buffer

            try:
                of_msg = unpack(data)
            except UnpackException:
                logger.debug("Non OpenFlow Message")
                self.tun2ofchannel[self.s].send(data)
            else:
                self.tun2ofchannel[self.s].send(data)

    def bind_tun_ofchannel(self, of_msg):
        switch_addr = of_msg.datapath_id.value
        self.ofchannelIndex[switch_addr] = self.s
        logger.debug("bind_tun_ofchannel %s" % switch_addr)
        self.tunnelIndex[switch_addr] = self.ofchannel2tun[self.s]
        self.tun2IDX[self.ofchannel2tun[self.s]] = switch_addr

    def broadcast_ovs2sp(self, switch_addr):
        logger.debug("broadcast_ovs2sp %s %s" % (self.server.getsockname()[0], self.server.getsockname()[1]))
        mapInfo = switch_addr + ' ' + self.host + ' ' + str(self.operation_port)
        self.update_ovs2sp(mapInfo)
        network = '<broadcast>'
        # self.broadserver.sendto(mapInfo.encode('utf-8'), (network,self.broadcast_port))

        def period_broadcast(data, addr):
            while True:
                self.broadserver.sendto(data, addr)
                logger.debug("period broadcast")
                time.sleep(4)

        threading.Thread(target=period_broadcast,
                         args=(mapInfo.encode('utf-8'), (network, self.broadcast_port))).start()

    def update_ovs2sp(self, mapInfo):
        logger.info("update_ovs2sp %s" % mapInfo)
        mapInfo = mapInfo.split(' ')
        switch_addr = mapInfo[0]
        sproxy_addr = mapInfo[1]
        sproxy_port = mapInfo[2]
        if switch_addr not in self.switch_addr2sproxy_addr.keys():
            self.switch_addr2sproxy_addr[switch_addr] = sproxy_addr + ' ' + sproxy_port

    def process_operationmsg(self, data):
        spmsg = spcomunication_pb2.spmsg()
        spmsg.ParseFromString(data)
        logger.info("process "+str(spmsg))
        ackentry = operation_entry(spmsg.type, spmsg.switch_addr, spmsg.operation_id)
        ack_fromQueue.add(ackentry)
        for containerItem in self.pending_container:
            containerItem.receive_ack()
            if containerItem.state:
                # fully satisfied
                self.__exec(containerItem)
                del containerItem  # TODO check it

    # def receievePortStatus(self,data):
    #     of_msg = unpack(data)
    #     '''
    #     #: The port was added
    #     OFPPR_ADD = 0
    #     #: The port was removed
    #     OFPPR_DELETE = 1
    #     #: Some attribute of the port has changed
    #     OFPPR_MODIFY = 2
    #     '''
    #     BACKUP = 5
    #     if of_msg.reason>0:
    #         for containerItem in self.pending_container:
    #             if containerItem.optype == BACKUP:
    #                containerItem.linkfailure = True
    #                containerItem.updateState()
    #                self.Pull(containerItem)
    #                if containerItem.state:
    #                    self.push(containerItem)  # TODO check this

    def __exec(self, container):
        logger.info("exec %s" % str(container))
        self.pending_container.remove(container)
        sock = self.ofchannelIndex[container.switch_addr]
        sock.sendall(container.entry)
        self.Push(container)

    def Push(self, container):
        dst_sproxy = []
        macList = container.get_ack_to_sw()
        for macAddr in macList:
            if macAddr not in self.switch_addr2sproxy_addr.keys():
                raise Exception("mapInfo is not complicated")
            else:
                mapInfo = self.switch_addr2sproxy_addr[macAddr].split(' ')
                sproxyAddr = com_end(mapInfo[0], int(mapInfo[1]))
                dst_sproxy.append(sproxyAddr)
        if not dst_sproxy:
            return
        pushinfo = spcomunication_pb2.spmsg()
        pushinfo.type = spcomunication_pb2.PUSH
        pushinfo.operation_id = str(container.id)
        pushinfo.switch_addr = container.switch_addr
        msg = pushinfo.SerializeToString()
        for dst in dst_sproxy:
            for i in range(1):  # TODO check it
                push_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                push_client.sendto(msg, (dst.addr, dst.port))

    # def Pull(self,container):
    #     data = container.entry
    #     switch_addr = container.switch_addr
    #     dst_sproxy = []
    #
    #     # parse ack_to to get dst_sproxy
    #     dst_sproxy = []
    #     macList = container.getSwitchMac(container.ack_to)
    #     for macAddr in macList:
    #         mapInfo = self.switch_addr2sproxy_addr[macAddr].split(' ')
    #         sproxyAddr = com_end(mapInfo[0],int(mapInfo[1]))
    #         dst_sproxy.append(sproxyAddr)
    #     pullinfo  =spcomunication_pb2.spmsg()
    #     pullinfo.type = spcomunication_pb2.PULL
    #     pullinfo.operation_id =container.id
    #     pullinfo.switch_addr = container.switch_addr
    #     msg = pullinfo.SerializeToString()
    #     for dst in dst_sproxy:
    #         pull_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #         pull_client.sendto(msg, (dst.addr,dst.port))
    #         '''
    #         pull_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         pull_client.connect((dst.addr,dst.port))
    #         pull_client.send(msg)
    #         pull_client.close()
    #         '''

    def on_close(self):
        logger.info("%s  has disconnected",  self.s.getpeername())
        self.input_list.remove(self.s)
        if self.s in self.tunnels:
            self.input_list.remove(self.tun2ofchannel[self.s])
            out = self.tun2ofchannel[self.s]
            out.close()
            self.s.close()
            del self.tun2ofchannel[self.s]
            del self.ofchannel2tun[out]
            self.tunnels.remove(self.s)
            self.tunnelIndex = {k: v for k, v in self.tunnelIndex.items() if v != self.s}
            self.ofchannelIndex = {k: v for k, v in self.ofchannelIndex.items() if v != out}
        else:
            self.input_list.remove(self.ofchannel2tun[self.s])
            out = self.ofchannel2tun[self.s]
            out.close()
            self.s.close()
            del self.ofchannel2tun[self.s]
            del self.tun2ofchannel[out]
            self.ofchannels.remove(self.s)
            self.tunnelIndex = {k: v for k, v in self.tunnelIndex.items() if v != out}
            self.ofchannelIndex = {k: v for k, v in self.ofchannelIndex.items() if v != self.s}
