import random
import select
import socket
import struct
import threading
import time

from pyof.utils import unpack, UnpackException
from pyof.v0x01.common.header import Type

from nccontainer.common.logger import logger
from nccontainer.switch.switch_proxy import operation_entry
from nccontainer.tunnel import ncctunnel_pb2

cenfile = "LScentralized.txt"
disfile = "LSditributed.txt"
ack_fromQueue = []
headerSize = 12


class ControllerProxy():
    ofchannels = set()
    tun2ofchannel = {}
    tunnels = set()
    ofchannel2tun = {}
    ofchannelIndex = {}
    tunnelIndex = {}  # dpid : socket
    tunnelLock = {}  # socket : Lock
    tun2idx = {}
    pendingtable = []
    tun2buffer = {}
    oftunneldata = {}
    input_list = []

    def __init__(self, host, port, forward_addr, forward_port,
                 buffer_size=4096, delay=0.0001):
        """
        :param host: tunnel server address
        :param port: tunnel server port
        :param forward_addr: controller OpenFlow server address
        :param forward_port: controller OpenFlow server port
        :param buffer_size: default 4096
        :param delay: default 0.0001
        """
        self.forward_addr = forward_addr
        self.forward_port = forward_port
        self.buffer_size = buffer_size
        self.delay = delay
        self.start = False
        self.host = host
        self.count = 0
        self.echo = 0
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(5)
        self.s = None

    def main_loop(self):
        logger.info("start server at %s" % str(self.server.getsockname()))
        self.input_list.append(self.server)
        while True:
            time.sleep(self.delay)
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])
            for self.s in inputready:
                if self.s == self.server:
                    self.on_accept()
                else:
                    try:
                        self.data = self.s.recv(self.buffer_size)
                    except:
                        pass
                    else:
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
                                        # logger.debug("shorter than headerSize")
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
        ofchannel_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ofchannel_sock.connect((self.forward_addr, self.forward_port))
        self.ofchannels.add(ofchannel_sock)
        clientsock, clientaddr = self.server.accept()
        logger.info("accept from %s"%str(clientaddr))
        tunnel_sock = clientsock
        self.tunnels.add(tunnel_sock)
        self.tunnelLock[tunnel_sock] = threading.Lock()
        self.ofchannel2tun[ofchannel_sock] = tunnel_sock
        self.tun2ofchannel[tunnel_sock] = ofchannel_sock
        self.input_list.append(ofchannel_sock)
        self.input_list.append(tunnel_sock)

    def on_recv(self):
        data = self.data
        # here we can parse and/or modify the data before send forward
        # logger.debug("Recived %d bytes from %s to %s" % (len(data), self.s.getpeername(), self.s.getsockname()))
        if self.s in self.ofchannels:
            logger.debug("Push in tunnel")
            self.push_in_tunnel(data)
        else:
            logger.debug("Pop out tunnel")
            self.pop_out_tunnel(data)

    def on_close(self):
        try:
            logger.warn("%s has disconnected", self.s.getpeername())
        except:
            return
        # remove objects from input_list
        self.input_list.remove(self.s)
        if self.s in self.tunnels:
            self.input_list.remove(self.tun2ofchannel[self.s])
            out = self.tun2ofchannel[self.s]
            out.close()
            self.s.close()
            del self.tun2ofchannel[self.s]
            if self.s in self.tun2idx.keys():
                del self.tun2idx[self.s]
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
            if out in self.tun2idx.keys():
                del self.tun2idx[out]
            try:
                self.tunnels.remove(self.s)
            except:
                logger.info("has been removed")
            self.tunnelIndex = {k: v for k, v in self.tunnelIndex.items() if v != out}
            self.ofchannelIndex = {k: v for k, v in self.ofchannelIndex.items() if v != self.s}

    def encapsulate(self, data):
        """
        encapsulate of_message with container_operation
        """
        # TODO: encapsulate of_message with container_op
        nccontainer = ncctunnel_pb2.nccontainer()
        try:
            of_msg = unpack(data)
        except UnpackException:
            # logger.debug("Non OpenFlow Message")
            pass
        else:
            logger.debug("OpenFlow Message Type: %s" %
                         of_msg.header.message_type)
            if of_msg.header.message_type == Type.OFPT_FLOW_MOD:
                id = str(random.random())
                nccontainer.op_id = id
        nccontainer.entry = data
        return nccontainer

    def send_container(self, container):
        logger.info("send_container protobuf object:\n%s" % str(container))
        dpid = container.switch
        sock = self.tunnelIndex[dpid]
        self.__send_container_by_sock(sock, container)

    def push_in_tunnel(self, data):
        """
        of -> tunnel
        """
        nccontainer = self.encapsulate(data)
        self.__send_container_by_sock(self.ofchannel2tun[self.s], nccontainer)

    def __send_container_by_sock(self, tun_sock, nccontainer):
        size = nccontainer.ByteSize()
        nccontainer = nccontainer.SerializeToString()
        ver = 1
        cmd = 101
        header = [ver, size, cmd]
        headPack = struct.pack("!3I", *header)
        try:
            lock = self.tunnelLock[tun_sock]
            lock.acquire()
            tun_sock.sendall(headPack + nccontainer)
            lock.release()
        except:
            logger.debug("pipe is deleted")

    def pop_out_tunnel(self, data):
        '''
        tunnel->of
        '''
        nccontainer = ncctunnel_pb2.nccontainer()
        nccontainer.ParseFromString(data)
        data = nccontainer.entry
        if nccontainer.instruction == "Centralized":  # TODO
            self.echo += 1
            ack_fromQueue.append(operation_entry(1, nccontainer.switch, nccontainer.op_id))
            # self.checkPending()
        else:
            try:
                of_msg = unpack(data)
            except:
                logger.debug("Non OpenFlow Message" + str(len(data)))
            else:
                if of_msg.header.message_type == Type.OFPT_FEATURES_REPLY:
                    switch_addr = of_msg.datapath_id.value
                    self.tunnelIndex[switch_addr] = self.s
                    self.tun2idx[self.s] = switch_addr
                    self.ofchannelIndex[switch_addr] = self.tun2ofchannel[self.s]

            if self.s in self.tun2idx.keys():
                # logger.debug("datapath created id : %s" % self.tun2idx[self.s])
                pass
            try:
                self.tun2ofchannel[self.s].send(data)
            except:
                pass
