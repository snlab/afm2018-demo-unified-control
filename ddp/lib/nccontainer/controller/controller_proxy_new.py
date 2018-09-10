import asyncio
import select
import socket
import struct
import threading
import time
from datetime import datetime

from pyof.utils import unpack, UnpackException
from pyof.v0x01.common.header import Type

from nccontainer.common.logger import logger
from nccontainer.common.utils import *


class _Tunnel2OFHandler(Tunnel2OFHandler):
    def __init__(self, reader, writer, connection):
        super().__init__(reader, writer, connection)
        self._info = ""

    async def loop(self):
        await super().loop()
        self._connection.unregister_info()


    async def _on_pass_msg(self, msg):
        logger = self._connection.logger
        self._writer.write(msg.body)
        try:
            of_msg = unpack(msg.body)
        except UnpackException:
            logger.warn("can not unpack OpenFlow Message, %s",str(msg.body))
        else:
            if of_msg.header.message_type==Type.OFPT_FEATURES_REPLY:
                dpid = of_msg.datapath_id.value
                logger.info("get OFPT_FEATURES_REPLY, dpid=%s"%dpid)
                self._connection.register_info(dpid, self._info)
        await self._writer.drain()

    async def _on_info_msg(self, msg):
        logger = self._connection.logger
        logger.debug('get info msg')
        self._info = msg.body.decode()
        logger.info(self._info)


class _OF2TunnelHandler(OF2TunnelHandler):

    async def _on_of_msg(self, of_msg, msg_data):
        logger = self._connection.logger
        logger.debug("OpenFlow Message Type: %s" % of_msg.header.message_type)
        if of_msg.header.message_type == Type.OFPT_FEATURES_REQUEST:
            logger.info("accept Type.OFPT_FEATURES_REQUEST")
        elif of_msg.header.message_type == Type.OFPT_ERROR:
            logger.info(of_msg.error_type)
        msg = TunnelMsg.construct(TunnelMsg.TYPE_PASS, msg_data)
        tunnel = self._writer
        tunnel.write(msg.pack())
        await tunnel.drain()


class TunnelConnectHandler(ConnectHandler):
    def __init__(self, reader, writer, forward_addr, forward_port, proxy, c2s_handler_cls=Forwarder,
                 s2c_handler_cls=Forwarder):
        super().__init__(reader, writer, forward_addr, forward_port, proxy, c2s_handler_cls, s2c_handler_cls)
        self._dpid = None

    def register_info(self, dpid, info):
        self._dpid = dpid
        self._proxy.dpid_to_info_conn[dpid] = (info, self)

    def unregister_info(self):
        if self._dpid is not None:
            self._proxy.dpid_to_info_conn.pop(self._dpid)

    def send_container(self, container):
        msg = TunnelMsg.construct(TunnelMsg.TYPE_CTRL, container)
        self._writer.write(msg.pack())
        self.logger.debug("send success")


class ControllerProxy(Proxy):
    def __init__(self, host, port, tunnel_addr, tunnel_port):
        super().__init__(host, port, tunnel_addr, tunnel_port, logger=logger)
        self.dpid_to_info_conn = {}

    def get_connect_handler(self, reader, writer):
        return TunnelConnectHandler(
            reader, writer,
            self._forward_addr, self._forward_port,
            self,
            c2s_handler_cls=_Tunnel2OFHandler,
            s2c_handler_cls=_OF2TunnelHandler
        )

    def get_dpid2info_threadsafe(self):
        async def get_dpid2info():
            return {k:v[0] for k,v in self.dpid_to_info_conn.items()}
        future = asyncio.run_coroutine_threadsafe(get_dpid2info(), self.loop)
        result = future.result()
        return result

    def send_container(self, container):
        def _send_container(cont):
            dpid = cont.dp_id
            pair= self.dpid_to_info_conn.get(dpid)
            if pair:
                pair[1].send_container(cont)
            else:
                self.logger.error("error map")
        self.loop.call_soon_threadsafe(_send_container, container)

    def main_loop(self):
        super().main_loop()

    def start_server(self, loop):
        super().start_server(loop)

    def stop(self):
        super().stop()