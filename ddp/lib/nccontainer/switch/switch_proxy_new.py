import asyncio
import select
import socket
import struct
import threading
import time
from datetime import datetime

from nccontainer.common.logger import logger
from nccontainer.common.utils import *
from .dataplane import DDPServerProtocol,ContainerManager


class _Tunnel2OFHandler(Tunnel2OFHandler):

    async def _on_pass_msg(self, msg):
        self._writer.write(msg.body)
        await self._writer.drain()

    async def _on_ctrl_msg(self, msg):
        self._connection.logger.debug("recv ctrl_msg %s"%str(msg.body))
        container = msg.body
        mgr = self._connection.get_container_manager()
        mgr.on_recv_container(container, self._connection)


class _OF2TunnelHandler(OF2TunnelHandler):

    async def loop(self):
        init_info = self._connection.get_ddp_info()
        msg = TunnelMsg.construct(TunnelMsg.TYPE_INFO, init_info)
        self._writer.write(msg.pack())
        await self._writer.drain()
        return await super().loop()

    async def _on_of_msg(self, of_msg, msg_data):
        logger = self._connection.logger
        logger.debug("OpenFlow Message Type: %s" % of_msg.header.message_type)
        if of_msg.header.message_type == Type.OFPT_FEATURES_REPLY:
            logger.info("accept Type.OFPT_FEATURES_REPLY")
        elif of_msg.header.message_type == Type.OFPT_PORT_STATUS:
            logger.info("accept Type.OFPT_PORT_STATUS")
        elif of_msg.header.message_type == Type.OFPT_ERROR:
            logger.info(of_msg.error_type)
        msg = TunnelMsg.construct(TunnelMsg.TYPE_PASS, msg_data)
        tunnel = self._writer
        tunnel.write(msg.pack())
        await tunnel.drain()


class SwitchConnectHandler(ConnectHandler):

    def get_container_manager(self):
        return self._proxy.container_manager

    def exec_container(self, container):
        """
        provide to container_manager
        """
        self._writer.write(container.entry)

    def get_ddp_info(self):
        return self._proxy.get_ddp_info()


class SwitchProxy(Proxy):
    def __init__(self, host, port, tunnel_addr, tunnel_port, ddp_addr, ddp_port):
        super().__init__(host,port,tunnel_addr,tunnel_port, logger=logger)
        self._ddp_transport = None
        self._ddp_addr = ddp_addr
        self._ddp_port = ddp_port
        self.container_manager = ContainerManager(self)

    def get_connect_handler(self, reader, writer):
        return SwitchConnectHandler(
            reader, writer,
            self._forward_addr, self._forward_port,
            self,
            c2s_handler_cls = _OF2TunnelHandler,
            s2c_handler_cls = _Tunnel2OFHandler
        )

    def get_ddp_info(self):
        return ("%s:%d" % (self._ddp_addr, self._ddp_port)).encode()

    def main_loop(self):
        super().main_loop()
        self._ddp_transport.close()

    def start_server(self, loop):
        listen = loop.create_datagram_endpoint(
            lambda: DDPServerProtocol(self), local_addr=(self._ddp_addr, self._ddp_port), family=socket.AF_INET)
        transport, protocol = loop.run_until_complete(listen)
        self._ddp_transport = transport
        super().start_server(loop)

    def stop(self):
        super().stop()


if __name__=="__main__":
    proxy = SwitchProxy('127.0.0.3',6653,'127.0.0.1',9090,'127.0.0.3',10091)
    proxy.main_loop()