import random


class Node:
    def __init__(self, id):
        self.id = id
        self.ports = {}  # {port_no: Link}
        self.flag = -1


class Link:
    def __init__(self, start, end):
        self.start = start  # (nodeid,portno)
        self.end = end  # (nodeid,portno)


class Topology:
    def __init__(self):
        self.nodes = {}  # {node_id: Node}
        self.links = {}  # {(nodeid,portno): Link}
        random.seed(0)
        self.__randomstate = random.getstate()

    def get_outer_ports(self):
        list = []
        for node in self.nodes.values():
            id = node.id
            for port in node.ports:
                if not (id, port) in self.links:
                    list.append((id, port))
        return list

    def is_outer_port(self, node_id, port_no):
        return not (node_id, port_no) in self.links

    def get_shortest_path(self, inport, outport):
        from queue import Queue

        assert inport != outport
        start_node = self.nodes[inport[0]]
        end_node = self.nodes[outport[0]]
        if start_node == end_node:
            return [outport]
        self.__set_all_flag()
        q = Queue()
        start_node.flag = 0
        q.put(start_node)
        path_map = {}
        while not q.empty():
            n = q.get()
            assert isinstance(n, Node)
            for port, link in n.ports.items():
                if link is not None:
                    assert isinstance(link, Link)
                    endid = link.end[0]
                    if endid == outport[0]:
                        path_list = [outport, link.start]
                        id = n.id
                        while id in path_map:
                            bp = path_map[id]
                            path_list.append(bp)
                            id = bp[0]
                        path_list.reverse()
                        return path_list
                    else:
                        link_end_node = self.nodes[endid]
                        if link_end_node.flag == -1:
                            link_end_node.flag = n.flag + 1
                            q.put(link_end_node)
                            path_map[endid] = link.start
        return None

    def random_change_path(self, oldpath):
        """
        random change old path to different new path
        :param oldpath: list
        :return: new path or None if the old path is only path
        """
        oldlen = len(oldpath)
        if oldlen <= 1:
            return None
        start_node_id = oldpath[0][0]
        end_port = oldpath[-1]
        assert self.is_outer_port(*end_port)

        end_node_id = end_port[0]
        self.__set_all_flag()
        for port in oldpath[:-1]:
            self.links[port].flag = 1  # link of old path
        path_link_list = []
        start_node = self.nodes[start_node_id]

        random.setstate(self.__randomstate)
        ret = self.__random_change_path_recurse(start_node, end_node_id, path_link_list)
        self.__randomstate = random.getstate()

        if ret:
            path_list = [item.start for item in path_link_list]
            path_list.append(end_port)
            return path_list
        else:
            return None

    def __random_change_path_recurse(self, current_node, end_node_id, path_link_list):
        if current_node.id == end_node_id:  # check the validation
            for link in path_link_list:
                if link.flag != 1:
                    return True
            return False
        else:  # recurse
            current_node.flag = 1  # visited
            links = filter(lambda l: l is not None, current_node.ports.values())
            random.shuffle(links)

            for link in links:
                next_node_id = link.end[0]
                next_node = self.nodes[next_node_id]
                if next_node.flag == 1:  # visited
                    continue

                path_link_list.append(link)

                if self.__random_change_path_recurse(next_node, end_node_id, path_link_list):
                    return True

                path_link_list.pop()

            current_node.flag = -1
            return False

    def __set_all_flag(self, flag=-1):
        for n in self.nodes.values():
            n.flag = flag
        for l in self.links.values():
            l.flag = flag
