import asyncio
import socket


class Forwarder:
    def __init__(self, reader, writer, connection):
        self._reader = reader
        self._writer = writer
        self._connection = connection

    async def loop(self):
        logger = self._connection.logger
        logger.info("start forward loop")
        try:
            while True:
                data = await self._reader.read(1024)
                if len(data)==0:
                    break
                logger.info("received %s"%str(data))
                self._writer.write(data)
                await self._writer.drain()
        except Exception:
            pass
        logger.info('end forward loop')
        self._writer.close()


class BoundProtocolForwarder(Forwarder):
    def __init__(self, reader, writer, connection):
        super().__init__(reader, writer, connection)

    async def readexactly(self, length):
        data = b''
        while length>0:
            r = await self._reader.read(length)
            if len(r)==0:
                raise Exception('read length == 0')
            data+=r
            length-=len(r)
        return data

    async def loop(self):
        logger = self._connection.logger
        while True:
            try:
                header_length = self.get_header_length()
                header_data = await self.readexactly(header_length)
            except Exception as e:
                logger.error("read header Error, %s", str(e))
                break
            try:
                body_length = self.get_body_length(header_data)
                body_data = await self.readexactly(body_length)
            except Exception as e:
                logger.error("read body Error, %s", str(e))
                break
            data = header_data + body_data
            await self.on_msg(data)
        logger.info("BoundProtocolForwarder loop end")
        self._writer.close()

    def get_header_length(self):
        """
        :return: integer, header_length
        """
        raise NotImplementedError("get_header_length")

    def get_body_length(self, header_data):
        """
        :return: body_length
        """
        raise NotImplementedError("get_body_length")

    async def on_msg(self, msg_data):
        raise NotImplementedError("on_msg")


class ConnectHandler:
    def __init__(self, reader, writer, forward_addr, forward_port, proxy, c2s_handler_cls=Forwarder, s2c_handler_cls=Forwarder):
        self._reader = reader
        self._writer = writer
        self._forward_addr = forward_addr
        self._forward_port = forward_port
        self._proxy = proxy
        self._forward_reader = None
        self._forward_writer = None
        self._c2s_handler_cls = c2s_handler_cls
        self._s2c_handler_cls = s2c_handler_cls
        self._c2s_handler = None
        self._s2c_handler = None
        self.logger = proxy.logger

    async def handle(self):
        writer = self._writer
        logger = self.logger
        addr = writer.get_extra_info('peername')
        try:
            self._forward_reader, self._forward_writer = await asyncio.open_connection(
                self._forward_addr, self._forward_port, loop=self._proxy.loop)
        except Exception:
            logger.warn("proxy can not connect to %s:%s" % (self._forward_addr, self._forward_port))
            writer.close()
            logger.info("close the client socket %s" % str(addr))
            # import os
            # os._exit(0)
        else:
            logger.info("connected to forward address")
            self._c2s_handler = self._c2s_handler_cls(self._reader, self._forward_writer, self)
            self._proxy.loop.create_task(self._c2s_handler.loop())
            self._s2c_handler = self._s2c_handler_cls(self._forward_reader, self._writer, self)
            await self._s2c_handler.loop()
            logger.info("close the client socket %s" % str(addr))


class Proxy:
    def __init__(self, host, port, forward_addr, forward_port, logger):
        self._host = host
        self._port = port
        self._forward_addr = forward_addr
        self._forward_port = forward_port
        self.loop = None
        self.logger = logger
        self._server = None
    
    def get_connect_handler(self, reader, writer):
        return ConnectHandler(reader, writer, self._forward_addr, self._forward_port, self)
    
    def main_loop(self):
        self.logger.warn("Proxy main_loop")
        # loop = asyncio.get_event_loop()
        loop =  asyncio.new_event_loop()
        self.loop = loop
        self.start_server(loop)
        while True:
            try:
                loop.run_forever()
            except KeyboardInterrupt as e:
                self.logger.error(str(e))
            except Exception as e:
                self.logger.error(str(e))
                break
        # Close the server
        self.logger.warn("run_forever exited")
        self._server.close()
        self.logger.warn("self._server.close")
        loop.run_until_complete(self._server.wait_closed())
        self.logger.warn("self._server.wait_closed()")
        loop.close()

    def start_server(self, loop):
        async def handle_connect(reader, writer):
            addr = writer.get_extra_info('peername')
            self.logger.info("accept connect from %s" % str(addr))
            connect_handler = self.get_connect_handler(reader, writer)
            if connect_handler:
                await connect_handler.handle()

        coro = asyncio.start_server(handle_connect,
                                    self._host,
                                    self._port,
                                    family = socket.AF_INET,
                                    loop=loop)
        self._server = loop.run_until_complete(coro)
        self.logger.info('Serving on {}'.format(self._server.sockets[0].getsockname()))

    def stop(self):
        def _stop():
            self.loop.stop()
        self.loop.call_soon_threadsafe(_stop)


if __name__=="__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    Proxy('127.0.0.1',9994,'42.96.146.169',80,logger=logging).main_loop()