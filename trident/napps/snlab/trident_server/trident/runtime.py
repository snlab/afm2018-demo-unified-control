import uuid
import networkx as nx
from thespian.actors import *
from itertools import groupby
from napps.snlab.trident_server.trident.interpreter import EMPTY

"""
The runtime takes the graph of variables and creates the decision tree.
"""

KEY_FUNCTION = {
    'global': lambda pkt: 1,
    'tcp-5-tuple': lambda pkt: 'x'.join([pkt.sip, pkt.dip, pkt.sport, pkt.dport, pkt.proto]),
    'dst-ip': lambda pkt: pkt.dip,
    'src-ip': lambda pkt: pkt.sip
}

class Packet(object):
    def __init__(self, sip, dip, sport, dport, ipproto):
        self.sip = sip
        self.dip = dip
        self.sport = sport
        self.dport = dport
        self.ipproto = ipproto

    def __repr__(self):
        return '<%s,%s,%d,%d,%s>' % (self.sip, self.dip, self.sport, self.dport, self.ipproto)

class Match(object):
    def __init__(self, pkt, keyfunc):
        self.pkt = pkt
        self.keyfunc = keyfunc

class HandleAction(object):
    def __init__(self, var, msg):
        self.var = var
        self.msg = msg

    def run(self):
        yield from self.var.handle(self.msg)

class UpdateAction(object):
    def __init__(self, var):
        self.var = var

    def run(self):
        yield from self.var.update()

class PullAction(object):
    def __init__(self, var, pkt):
        self.var = var
        self.pkt = pkt

    def run(self):
        yield from self.var.pull(self.pkt)


class LvMessage(object):
    def __init__(self, event):
        self.event = event

class Pull(LvMessage):
    def __init__(self, dst, pkt):
        LvMessage.__init__(self, 'pull')
        self.dst = dst
        self.pkt = pkt

class Notification(LvMessage):
    def __init__(self, event, src, match, value, version, rootcause):
        self.event = event
        self.src = src
        self.match = match
        self.value = value
        self.version = version
        self.rootcause = rootcause

class Propagate(Notification):
    def __init__(self, src, match, version, rootcause):
        Notification.__init__(self, 'propagate', src, match, None, version, rootcause)

class Sync(Notification):
    def __init__(self, src, match, value, version, rootcause):
        Notification.__init__(self, 'sync', src, match, value, version, rootcause)

class NoSync(Notification):
    def __init__(self, src, match, version, rootcause):
        Notification.__init__(self, 'nosync', src, match, None, version, rootcause)

DEACTIVATED = 0
ACTIVATED = 1

class LivePktVariable(object):
    def __init__(self, var, keyfunc, deps):
        self.var = var
        self.keyfunc = keyfunc

        self.version = 0
        self.state = DEACTIVATED
        self.deps = {dep: 0 for dep in deps}
        self.awaits = {dep: 1 for dep in deps}

        self.followers = {}

    def update(self):
        self.version = self.version + 1

        # TODO update

        if len(self.awaits) == 0:
            print("%s[%s] is up to date" % (self.var, self.key))
            self.state = ACTIVATED

            msg = LvMessage.sync(pkt, self.keyfunc, self.var, self.version)

class LiveVariable(object):
    def __init__(self, lvs, var, op, args, kwargs):
        self.lvs = lvs
        self.var = var
        self.op = op
        self.args = args
        self.kwargs = kwargs

        dep1 = [ (args[i], i) for i in range(len(args)) ]
        dep2 = [ (kwargs[k], k) for k in kwargs ]

        deps = sorted(dep1 + dep2, key=lambda k: k[0])
        deps = {m: list(map(lambda x: x[1], g)) for m, g in groupby(deps, lambda k: k[0])}

        self.deps = deps

        self.table = {}

    def update(self):
        self.version = self.version + 1
        if len(self.awaits) == 0:
            print('%s is up to date' % (self.var))
            self.state = 'fresh'
            msg = LvMessage.sync(None, self.var, self.version, self.var)
            for f in self.followers:
                yield HandleAction(lvs.get(f), msg)

    def handle(self, msg):
        print('%s is handling event %s from %s' % (self.var, msg.event, msg.var))
        if msg.event == 'change':
            yield from self.handle_change(msg.pkt, msg.var, msg.version, msg.rootcause)
        elif msg.event == 'sync':
            yield from self.handle_sync(msg.pkt, msg.var, msg.version, msg.rootcause)
        elif msg.event == 'pull':
            yield from self.handle_pull(msg.pkt, msg.var, msg.version)
        elif msg.event == 'depend':
            yield from self.handle_depend(msg.pkt, msg.var, msg.version)

    def pull(self, pkt):
        if self.state == 'fresh':
            return

        for aw in self.awaits:
            var, ver = aw, self.awaits[aw]
            msg = LvMessage.pull(pkt, self.var, ver)
            yield HandleAction(lvs.get(var), msg)

    def handle_change(self, pkt, source, version, rootcause):
        if source not in self.deps:
            return
        # add the changed node to awaits
        oldv = self.awaits.get(source, 0)
        self.awaits[source] = max(oldv, version)

        self.state = 'waiting'

        msg = LvMessage.change(pkt, self.var, self.version + 1, rootcause)
        for f in self.followers:
            yield HandleAction(lvs.get(f), msg)

    def handle_sync(self, pkt, source, version, rootcause):
        if source not in self.deps:
            return
        # if new version >= awaits, accept
        if source not in self.awaits:
            return
        oldv = self.awaits[source]
        if version >= oldv:
            del self.awaits[source]
            self.deps[source].version = version
        if len(self.awaits) == 0:
            yield UpdateAction(self)

    def handle_pull(self, pkt, dest, version):
        self.followers |= { dest }

        msg = LvMessage.sync(pkt, self.var, self.version, self.var)
        if self.state == 'fresh' and self.version >= version:
            yield HandleAction(lvs.get(dest), msg)
        elif self.state == 'waiting':
            for aw in self.awaits:
                var, ver = aw, awaits[aw].version
                msg = LvMessage.pull(pkt, self.var, ver)
                yield HandleAction(lvs.get(var), msg)

    def handle_depend(self, pkt, dest, version):
        self.followers |= { dest }

class DirectLiveVariable(LiveVariable):
    def __init__(self, lvs, symbol, init_value):
        LiveVariable.__init__(self, lvs, symbol, 'direct', [], {})

        self.state = 'fresh'
        self.version = 1

    def new_value(self, match, value):
        self.state = 'waiting'
        msg = LvMessage.change(match, self.var, self.version + 1, self.var)
        for f in self.followers:
            yield HandleAction(lvs.get(f), msg)

        self.version = self.version + 1
        self.state = 'fresh'

        #TODO
        msg = LvMessage.sync(match, self.var, self.version + 1, self.var)
        for f in self.followers:
            yield HandleAction(lvs.get(f), msg)

    def handle_pull(self, pkt, dest, version):
        self.followers |= { dest }

        msg = LvMessage.sync(pkt, self.var, self.version, self.var)
        if self.state == 'fresh' and self.version >= version:
            yield HandleAction(lvs.get(dest), msg)

class LvSystem(object):
    def __init__(self):
        self.lvs = {}

        self.q = []
        self.executor = None
        # create a thread to execute the actions
        # each execution yields one or many actions (which should be appended to the execution queue)
        # Yes, it's a single thread model now.

    def launch(self, vgraph, vnodes):
        from interpreter import StreamAttribute

        self.sa_dict = {}
        for v in vnodes:
            var = v['var']
            if type(var) is StreamAttribute and var.name not in self.sa_dict:
                self.sa_dict[var.name] = var
                # they should also be converted to DirectLiveVariable (i.e.,
                # whose value can be modified through the set function)
        self.virsink = vnodes[-1]

        self.lvs = {} # create a live variable/table for each vnode

    def stop(self):
        pass

    def get_match(self, sa_name, pkt):
        pass

    def get_value(self, sa_name, value):
        pass

    def new_pkt(self, pkt):
        self.q.put(PullAction(self.lvs[self.vnode], pkt))
        # TODO return table

    def update_sa(self, sa_name, pkt, value):
        # TODO
        match = self.get_match(sa_name, pkt)
        value = self.get_value(sa_name, value)
        var = self.sa_dict[sa_name]
        self.q.put(self.lvs[var].new_value(match, value))
        # first send propagate message, then sync/nosync message

    def update_topology():
        pass

if __name__ == '__main__':
    lvs = LvSystem()

    lvs.create_dlv('a', 1)
    lvs.create_dlv('b', 2)
    lvs.create_lv('c', '+', ['a', 'b'], {})

    print(lvs.get('c').deps)

    act0 = PullAction(lvs.get('c'), None)
    q = [act0]
    while len(q) > 0:
        act, q = q[0], q[1:]
        print(act)
        q += list(act.run())
