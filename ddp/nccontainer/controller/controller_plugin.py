from threading import Thread
from queue import Queue

from nccontainer.common.logger import logger
from nccontainer.controller.controller_proxy_new import ControllerProxy
from nccontainer.controller.topology import Topology


class _ProxyThread(Thread):
    def __init__(self, server):
        Thread.__init__(self)
        self.__server = server

    def run(self):
        self.__server.main_loop()


class ControllerPlugin:
    def __init__(self):
        self.__server = ControllerProxy("127.0.0.1", 9090, "127.0.0.1", 6633)
        self.__serverthread = _ProxyThread(self.__server)

        from nccontainer.controller.schde_seq import UpdateScheduler
        self.__msg_queue = Queue()
        self.__schded = UpdateScheduler(self.__msg_queue, self.__server)

    def start(self):
        self.__serverthread.start()
        self.__schded.start()

    def stop(self):
        import os
        os._exit(0) # TODO safe exit

    def updateTopology(self, topo):
        assert isinstance(topo, Topology)
        # TODO compare topo
        self.__msg_queue.put(topo)

    def setupPath(self, priority, match, path):
        self.__msg_queue.put((priority, match, path))

    def setupPathList(self, path_table):
        self.__msg_queue.put(path_table)


if __name__ == "__main__":
    from pyof.foundation.basic_types import IPAddress

    logger.setLevel("DEBUG")
    plugin = ControllerPlugin()
    plugin.start()
    sw = ["",
          "00:00:00:00:00:00:00:01",
          "00:00:00:00:00:00:00:02",
          "00:00:00:00:00:00:00:03",
          "00:00:00:00:00:00:00:04"]
    ip1 = IPAddress("10.0.0.1/32").pack()
    ip2 = IPAddress("10.0.0.2/32").pack()
    IPTYPE = b'\x08\x00'
    match1_2 = {"eth_type": IPTYPE,
                "ip_src": ip1,
                "ip_dst": ip2}
    match2_1 = {"eth_type": IPTYPE,
                "ip_src": ip2,
                "ip_dst": ip1}
    path1_2 = [[(sw[1], {1}), (sw[2], {1}), (sw[3], {3})],
               [(sw[1], {2}), (sw[4], {1}), (sw[3], {3})]]
    path2_1 = [[(sw[3], {1}), (sw[2], {2}), (sw[1], {3})],
               [(sw[3], {2}), (sw[4], {2}), (sw[1], {3})]]
    count = 1
    while True:
        import time

        a = input("wait input: ")
        plugin.setupPath(10, match1_2, path1_2[count % 2])
        plugin.setupPath(10, match2_1, path2_1[count % 2])
        count += 1
