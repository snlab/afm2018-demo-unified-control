import struct
import asyncio

from pyof.utils import unpack, UnpackException
from pyof.v0x01.common.header import Type
from .container import Container
from .proxy import *
from  nccontainer.proto import dataplane_pb2


class TunnelHeader:
    LENGTH = 8

    def __init__(self, length=None, type=None):
        self.length = length
        self.type = type

    @classmethod
    def unpack(cls, data):
        length, type = struct.unpack('!2I',data)
        return TunnelHeader(length, type)

    def pack(self):
        return struct.pack('!2I', self.length, self.type)


class TunnelMsg:
    TYPE_PASS = 0
    TYPE_CTRL = 1
    TYPE_INFO = 2

    def __init__(self, header, body):
        assert isinstance(header, TunnelHeader)
        self.header = header
        self.type = header.type
        self.body = body
        if self.type==TunnelMsg.TYPE_PASS:
            assert isinstance(body, bytes)
        elif self.type==TunnelMsg.TYPE_CTRL:
            assert isinstance(body, Container) #TODO

    @classmethod
    def unpack(cls, data):
        header = TunnelHeader.unpack(data[:TunnelHeader.LENGTH])
        body = data[TunnelHeader.LENGTH:]
        if header.type==TunnelMsg.TYPE_CTRL:
            body = Container.unpack(body)
        return TunnelMsg(header, body)

    @classmethod
    def construct(cls, type, body):
        if type==TunnelMsg.TYPE_PASS or type==TunnelMsg.TYPE_INFO:
            assert isinstance(body, bytes)
            l = len(body) + TunnelHeader.LENGTH
            return TunnelMsg(TunnelHeader(l, type), body)
        elif type==TunnelMsg.TYPE_CTRL:
            assert isinstance(body, Container)
            l = len(body.pack()) + TunnelHeader.LENGTH
            return TunnelMsg(TunnelHeader(l, type), body)
        else:
            raise Exception()

    def pack(self):
        hb = self.header.pack()
        if self.type==TunnelMsg.TYPE_PASS or self.type==TunnelMsg.TYPE_INFO:
            return hb+self.body
        elif self.type==TunnelMsg.TYPE_CTRL:
            return hb+self.body.pack()
        else:
            raise Exception()


class DPMsg:
    TYPE_PUSH = 0
    TYPE_PULL = 1

    def __init__(self, type, dp_id, op_id):
        self.type = type
        self.dp_id = dp_id
        self.op_id = op_id

    def __str__(self):
        return "type=%d, dp_id=%s, op_id=%s"%(self.type, self.dp_id, self.op_id)

    @classmethod
    def unpack(cls, data):
        proto = dataplane_pb2.DPMsg()
        proto.ParseFromString(data)
        if proto.type == dataplane_pb2.PUSH:
            type=DPMsg.TYPE_PUSH
        elif proto.type == dataplane_pb2.PULL:
            type=DPMsg.TYPE_PULL
        else:
            raise Exception()
        return DPMsg(type, proto.dp_id, proto.op_id)

    def pack(self):
        proto = dataplane_pb2.DPMsg()
        proto.dp_id = self.dp_id
        proto.op_id = self.op_id
        if self.type == DPMsg.TYPE_PUSH:
            proto.type = dataplane_pb2.PUSH
        elif self.type == DPMsg.TYPE_PULL:
            proto.type = dataplane_pb2.PULL
        else:
            raise Exception()
        return proto.SerializeToString()


class Tunnel2OFHandler(BoundProtocolForwarder):

    def get_header_length(self):
        return TunnelHeader.LENGTH

    def get_body_length(self, header_data):
        header = TunnelHeader.unpack(header_data)
        return header.length - TunnelHeader.LENGTH

    async def on_msg(self, msg_data):
        logger = self._connection.logger
        try:
            msg = TunnelMsg.unpack(msg_data)
        except Exception:
            logger.error("can not unpack Tunnel Message")
        else:
            if msg.type == TunnelMsg.TYPE_PASS:
                await self._on_pass_msg(msg)
            elif msg.type == TunnelMsg.TYPE_CTRL:
                await self._on_ctrl_msg(msg)
            elif msg.type == TunnelMsg.TYPE_INFO:
                await self._on_info_msg(msg)
            else:
                raise Exception("Unknown msg type")

    async def _on_pass_msg(self, msg):
        raise NotImplementedError("_on_pass_msg")

    async def _on_ctrl_msg(self, msg):
        raise NotImplementedError("_on_ctrl_msg")

    async def _on_info_msg(self, msg):
        raise NotImplementedError("_on_info_msg")


class OF2TunnelHandler(BoundProtocolForwarder):

    def get_header_length(self):
        return 4

    def get_body_length(self, header_data):
        return int.from_bytes(header_data[2:4], byteorder='big')-4

    async def on_msg(self, msg_data):
        try:
            of_msg = unpack(msg_data)
        except UnpackException:
            self._connection.logger.warn("can not unpack OpenFlow Message, %s",str(msg_data))
            msg = TunnelMsg.construct(TunnelMsg.TYPE_PASS,msg_data)
            self._writer.write(msg.pack())
            await self._writer.drain()
        else:
            await self._on_of_msg(of_msg, msg_data)

    async def _on_of_msg(self, of_msg, msg_data):
        raise NotImplementedError("_on_of_msg")