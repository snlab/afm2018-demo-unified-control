from threading import Thread

from nccontainer.controller.dependency import DependencyGraph, DependencyNode
from nccontainer.controller.topology import Topology
from .utils import make_flow_key
from nccontainer.common.logger import logger


class _FlowStatus:
    def __init__(self, key):
        self.path = None
        self.priority = 1
        self.match = None
        self.key = key  # flow priority match tuple


class UpdateScheduler(Thread):
    def __init__(self, msg_queue, controller_proxy):
        Thread.__init__(self)
        self.__msg_queue = msg_queue
        self.__topo = None
        self.__flow_status = {}
        self.__controller_proxy = controller_proxy

    def run(self):
        logger.info("update scheduler start")
        while True:
            e = self.__msg_queue.get()
            logger.info("msg = %s", str(e))
            if isinstance(e, Topology):
                self.__update_topology(e)
            elif isinstance(e, tuple):
                priority, match, path = e
                flow = make_flow_key(priority, match)
                self.__flow_status.setdefault(flow, _FlowStatus(key=flow))
                stat = self.__flow_status[flow]
                dep = DependencyGraph().construct(priority, match, stat.path, path)
                self.__execute(dep)
                stat.path = path
                stat.priority = priority
                stat.match = match

    def __update_topology(self, topo):
        # TODO compare topo
        # TODO set flag
        self.__topo = topo

    def __execute(self, dep):
        dpid2info = self.__controller_proxy.get_dpid2info_threadsafe()
        conts = dep.convert_to_container(dpid2info)
        for cont in conts:
            self.__controller_proxy.send_container(cont)
