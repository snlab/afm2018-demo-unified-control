from threading import Thread

from nccontainer.controller.dependency import DependencyGraph, DependencyNode
from nccontainer.controller.topology import Topology
from .utils import make_flow_key
from nccontainer.common.logger import logger


class _FlowStatus:
    def __init__(self, key, priority=-1, match=None, path=None):
        self.path = path
        self.priority = priority
        self.match = match
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
            elif isinstance(e, list):
                new_flow_status = {}
                for priority, match, path in e:
                    assert path is not None
                    flow = make_flow_key(priority, match)
                    status = _FlowStatus(key=flow, priority=priority, match=match, path=path)
                    new_flow_status[flow] = status
                new = set(new_flow_status.keys())
                old = set(self.__flow_status.keys())
                for install in new-old:
                    s = new_flow_status[install]
                    dep = DependencyGraph().construct(s.priority, s.match, None, s.path)
                    self.__execute(dep)
                for modify in new&old:
                    s1 = self.__flow_status[modify]
                    s2 = new_flow_status[modify]
                    dep = DependencyGraph().construct(s2.priority, s2.match, s1.path, s2.path)
                    self.__execute(dep)
                for remove in old-new:
                    s = self.__flow_status[remove]
                    dep = DependencyGraph().construct(s.priority, s.match, s.path, None)
                    self.__execute(dep)
                self.__flow_status = new_flow_status

    def __update_topology(self, topo):
        # TODO compare topo
        # TODO set flag
        self.__topo = topo

    def __execute(self, dep):
        dpid2info = self.__controller_proxy.get_dpid2info_threadsafe()
        conts = dep.convert_to_container(dpid2info)
        for cont in conts:
            self.__controller_proxy.send_container(cont)
