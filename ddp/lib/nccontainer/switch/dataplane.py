import asyncio

from nccontainer.common.utils import *


class DDPServerProtocol(asyncio.DatagramProtocol):
    def __init__(self, proxy):
        self._proxy = proxy
        self._transport = None

    def connection_made(self, transport):
        self._transport = transport

    def datagram_received(self, data, addr):
        logger = self._proxy.logger
        msg = DPMsg.unpack(data)
        # self.transport.sendto(data, addr)
        mgr = self._proxy.container_manager
        if msg.type==DPMsg.TYPE_PUSH:
            logger.info("received PUSH %s",str(msg))
            mgr.on_recv_push(msg.op_id)
        elif msg.type == DPMsg.TYPE_PULL:
            logger.info("received PULL %s", str(msg))
            mgr.on_recv_pull(msg.op_id)


class DDPClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, container, proxy):
        self._container = container
        self._proxy = proxy
        self._transport = None

    def connection_made(self, transport):
        logger = self._proxy.logger
        self._transport = transport
        msg = DPMsg(DPMsg.TYPE_PUSH, self._container.dp_id, self._container.op_id)
        data = msg.pack()
        addr_list = self._container.get_ack_to_address()
        logger.debug("DDPClientProtocol addr_list=%s", str(addr_list))
        for addr in addr_list:
            self._transport.sendto(data, addr)
            logger.info("DDPClientProtocol sendto addr=%s data=%s", str(addr), str(data))
        self._transport.close()

    def datagram_received(self, data, addr):
        # print("Received:", data.decode())
        # print("Close the socket")
        # self.transport.close()
        pass

    def error_received(self, exc):
        self._proxy.logger.error('Error received:', exc)

    def connection_lost(self, exc):
        self._proxy.logger.warn("DDPClientProtocol, closed")


class ContainerManager:
    def __init__(self, proxy):
        self._proxy = proxy
        self._received_containers = [] # op_id
        self._pending_containers = {} # op_id : ( Container, connection )
        self._finshed_containers = [] # op_id

    def on_recv_container(self, container, connection):
        if not container.state:
            for op_id in self._received_containers:
                container.receive_ack(op_id)
                if container.state:
                    break
            if not container.state:
                for op_id in self._finshed_containers:
                    container.receive_ack(op_id)
                    if container.state:
                        break
        if container.state:
            self._container_exec((container, connection))
            self._finshed_containers.append(container.dp_id)
        else:
            self._pending_containers[container.dp_id]=(container, connection)

    def on_recv_push(self, op_id):
        logger=self._proxy.logger
        logger.info("receive container %s", op_id)
        for pending in list(self._pending_containers.values()):
            container = pending[0]
            container.receive_ack(op_id)
            if container.state:
                self._container_exec(pending)
                self._finshed_containers.append(container.dp_id)
                self._pending_containers.pop(container.dp_id)
        self._received_containers.append(op_id)

    def on_recv_pull(self, op_id):
        raise NotImplementedError()

    def _container_exec(self, pair):
        container, connection = pair
        connection.exec_container(container)
        self.on_container_execd(container)

    def on_container_execd(self,container):
        connect =self._proxy.loop.create_datagram_endpoint(
            lambda: DDPClientProtocol(container, self._proxy), family=socket.AF_INET)
        self._proxy.loop.create_task(connect)
