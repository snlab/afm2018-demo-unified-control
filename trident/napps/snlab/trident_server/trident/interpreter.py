import json, uuid
import networkx as nx
from functools import reduce
from lark import Transformer
from napps.snlab.trident_server.trident.util import error
from napps.snlab.trident_server.trident.builtin import lookup_builtin_func, Phi

def ierror(msg):
    error('interpretation', msg)

DATA_TYPES = [ 'string', 'int', 'bool', 'route-set', 'waypoint' ]
STREAM_TYPES = [ 'global', 'tcp-5-tuple', 'src-ip', 'dst-ip' ]

class HeaderField(object):
    def __init__(self, name, datatype):
        self.name = name
        self.typeinfo = datatype

HEADERFIELD_TABLE = {
    'sip': HeaderField('sip', 'string'),
    'dip': HeaderField('dip', 'string'),
    'sport': HeaderField('sport', 'int'),
    'dport': HeaderField('dport', 'int'),
    'ipproto': HeaderField('ipproto', 'string')
}

class StreamAttribute(object):
    def __init__(self, context, datatype, name, streamtype):
        assert datatype in ['string', 'int', 'float', 'bool']
        assert streamtype in STREAM_TYPES

        self.context = context
        self.typeinfo = datatype
        self.name = name
        self.streamtype = streamtype

    @staticmethod
    def load(context, filename, attrname):
        with open(filename) as f:
            data = json.load(f)
        assert attrname in data
        attr = data[attrname]
        assert 'datatype' in attr
        assert 'name' in attr
        assert 'streamtype' in attr
        return StreamAttribute(context, attr['datatype'], attr['name'], attr['streamtype'])

    def __str__(self):
        return "stream attribute: %s [%s, %s]" % (self.name, self.typeinfo, self.streamtype)

class NetworkState(object):
    def __init__(self, context, datatype, name, object_type):
        assert datatype in ['string', 'int', 'bool']
        assert object_type in ['node', 'edge']

        self.context = context
        self.typeinfo = datatype
        self.name = name
        self.obj_type = object_type

    @staticmethod
    def load(context, filename, attrname):
        with open(filename) as f:
            data = json.load(f)
        assert attrname in data
        attr = data[attrname]
        assert 'datatype' in attr
        assert 'name' in attr
        assert 'object_type' in attr
        return NetworkState(context, attr['datatype'], attr['name'], attr['object_type'])

    def __str__(self):
        return "network state: %s [%s, %s]" % (self.name, self.typeinfo, self.obj_type)

class Variable(object):
    def __init__(self, symbol, typeinfo):
        self.symbol = symbol
        self.typeinfo = typeinfo
        self.version = uuid.uuid4().hex

    def __str__(self):
        return '%s@%s' % (self.symbol, self.version)

class Action(Variable):
    def __init__(self, pkt, action):
        Variable.__init__(self, uuid.uuid4().hex, 'binding')
        self.pkt = pkt
        self.action = action

class Const(object):
    def __init__(self, value, typeinfo):
        self.value = value
        self.typeinfo = typeinfo

    def __str__(self):
        return 'const(%s)' % self.value

EMPTY = Const('none', 'any')

class CodeBlock(object):
    """
    CodeBlock is a sequence of SSA instructions.
    """
    def __init__(self, parent, idx):
        self.idx= idx
        self.parent = parent
        self.symbols = {}

    def new_variable(self, symbol, typeinfo):
        if symbol is None:
            symbol = '_temp' + uuid.uuid4().hex
        return Variable(symbol, typeinfo)

    def new_constant(self, value, typeinfo):
        return Const(value, typeinfo)

    def get(self, symbol, safe=False):
        if symbol in self.symbols:
            return self.symbols[symbol]
        if self.parent is not None:
            return self.parent.get(symbol, safe)
        if not safe:
            ierror('variable %s used before declaration' % (symbol))
        else:
            return EMPTY

    def put(self, symbol, variable):
        #print('putting symbol %s into cb %s' % (symbol, self.idx))
        self.symbols[symbol] = variable

class TridentInterpreter(object):
    """
    TridentInterpreter should return code blocks containing instructions in the
    static singular assignment form.
    """
    def interpret(self, ast):
        return None

class TridentTransformer(Transformer): # Removing \"
    def stream_attribute(self, matches):
        return [m.value.strip('\"') for m in matches]

    def network_state(self, matches):
        return [m.value.strip('\"') for m in matches]

    def symbol(self, s):
        return s[0].value

class LarkInterpreter(TridentInterpreter):

    def __init__(self):
        pass

    def new_vnode(self, v, op=None, args=[], kwargs={}):
        self.vgraph.add_node(v, var=v, f=op, args=args, kwargs=kwargs)
        self.vnodes += [self.vgraph.node[v]]
        for arg in args:
            self.vgraph.add_edge(arg, v, active=True)
        for k in kwargs:
            self.vgraph.add_edge(kwargs[k], v, active=True)

    def new_codeblock(self, parent=None):
        cb = CodeBlock(parent, self.bidx)
        self.bidx += 1
        self.blocks[self.bidx] = cb
        return cb

    def interpret(self, ast):
        self.bidx = 0
        self.blocks = {}

        self.vgraph = nx.DiGraph()
        self.vnodes = []

        cb = self.new_codeblock()
        transformer = TridentTransformer()

        self.do_interpret(transformer.transform(ast), cb)
        self.add_virtual_sink(cb)
        return self.vgraph, self.vnodes # FIXME converting to sequence of Node s

    def add_virtual_sink(self, cb):
        appeared = {}
        for v in reversed(self.vnodes):
            var = v['var']
            if var.typeinfo == 'binding' and var.symbol not in appeared:
                appeared[var.symbol] = var

        v = cb.new_variable('virtualsink', 'binding')
        op = self.do_interpret_op('virtualsink', cb, ['binding'] * len(appeared))
        self.new_vnode(v, op, appeared.keys())

    def do_interpret(self, ast, cb):
        for k in HEADERFIELD_TABLE:
            cb.put('pkt.' + k, HEADERFIELD_TABLE[k])
        if 'start' == ast.data:
            self.do_interpret(ast.children[0], cb)
            self.do_interpret(ast.children[1], cb)
        elif 'preamble' == ast.data:
            for c in ast.children:
                self.do_interpret_dec(c, cb)
        elif 'program' == ast.data:
            self.do_interpret_program(ast.children[0], cb)

    def do_interpret_dec(self, ast, cb):
        if 'sa_dec' == ast.data:
            self.do_interpret_dataschema(ast, cb)
        elif 'ns_dec' == ast.data:
            self.do_interpret_networkstate(ast, cb)
        elif 'expr_dec' == ast.data:
            symbol = ast.children[0]
            self.do_interpret_expr(ast.children[1], cb, symbol)

    def do_interpret_dataschema(self, ast, cb):
        symbol, args = ast.children
        if len(args) == 3:
            value = StreamAttribute(cb, *args)
        else:
            value = StreamAttribute.load(cb, *args)
        self.new_vnode(value)

        cb.put('pkt.' + symbol, value)

    def do_interpret_networkstate(self, ast, cb):
        symbol, args = ast.children
        if len(args) == 3:
            value = NetworkState(cb, *args)
        else:
            value = NetworkState.load(cb, *args)
        self.new_vnode(value)

        cb.put(symbol, value)

    def do_interpret_program(self, ast, cb):
        pcb = self.new_codeblock(cb)
        for c in ast.children:
            if 'expr_ins' == c.data:
                symbol, expr = c.children
                self.do_interpret_expr(expr, pcb, symbol)
            elif 'two_way_branch' == c.data:
                cond, t1, t2 = c.children
                self.do_interpret_branch(cond, [t1, t2], c.data, pcb)
            elif 'three_way_branch' == c.data:
                cond, t1, t2, t3 = c.children
                self.do_interpret_branch(cond, [t1, t2, t3], c.data, pcb)
            elif 'fallback_branch' == c.data:
                cond, t1, t23 = c.children
                self.do_interpret_branch(cond, [t1, t23], c.data, pcb)
            elif 'binding' == c.data:
                pkt, rs = c.children

                pkt = pkt.data
                rv = self.do_interpret_expr(rs, pcb)

                op = self.do_interpret_op('bind', cb, ['pkt', rv.typeinfo])
                v = Action(pkt, 'bind')
                self.new_vnode(v, op, [rv])
                cb.put(v.symbol, v)
                # TODO
                print('bind(%s, %s)' % (pkt, rv))
            elif 'drop' == c.data:
                pkt = c.children[0].data

                op = self.do_interpret_op('drop', cb, ['pkt'])
                v = Action(pkt, 'drop')
                cb.put(v.symbol, v)
                print('drop(%s)' % (pkt))
            elif 'statements' == c.data:
                self.do_interpret_program(c.children[0], pcb)
        self.do_interpret_merge(cb, [pcb])

    def do_interpret_merge(self, cb, ccb, **kwargs):
        if 'guard_variable' not in kwargs:
            # not a branch, simply update the symbols
            for c in ccb:
                for sym, var in c.symbols.items():
                    cb.put(sym, var)
        else:
            # handle branches
            gv = kwargs['guard_variable']
            bt = kwargs['branch_type']
            symbols = [c.symbols for c in ccb]
            symbols = reduce(lambda x,y: x | y, map(set, symbols))
            for sym in symbols:
                vs = [c.get(sym, True) for c in ccb]
                vtypes = reduce(lambda x,y: x | y, [{x.typeinfo} for x in vs if x != EMPTY])
                if len(vtypes) > 1:
                    ierror('symbol %s has multiple types: [%s]' % (sym, ','.join(vtypes)))

                v = cb.new_variable(sym, list(vtypes)[0])
                self.new_vnode(v, Phi(bt), [gv] + vs)

                print("%s = %s(%s)" % (v, bt, ','.join([str(gv)] + list(map(str, vtypes)))))
                cb.put(sym, v)

    def do_interpret_expr(self, ast, cb, symbol=None):
        if 'bin_expr' == ast.data:
            t1, op, t2 = ast.children

            v1 = self.do_interpret_expr(t1, cb)
            v2 = self.do_interpret_expr(t2, cb)
            argtypes = [v1.typeinfo, v2.typeinfo]

            op = self.do_interpret_op(op.data, cb, argtypes)

            v = cb.new_variable(symbol, op.typecheck(argtypes))
            self.new_vnode(v, op, [v1, v2])
            cb.put(v.symbol, v)

            print('%s = %s(%s, %s)' % (v, op, v1, v2))
            return v
        elif 'uni_expr' == ast.data:
            op, t1 = ast.children

            v1 = self.do_interpret_expr(t1, cb)
            argtypes = [v1.typeinfo]

            op = self.do_interpret_op(op.data, cb, argtypes)

            v = cb.new_variable(symbol, op.typecheck(argtypes))
            self.new_vnode(v, op, [v1])
            cb.put(v.symbol, v)

            print('%s = %s(%s)' % (v, op, v1))
            return v
        elif 'v_expr' == ast.data:
            return self.do_interpret_value(ast.children[0], cb, symbol)
        elif 'sa_expr' == ast.data:
            symbol = 'pkt.' + ast.children[0]
            v = cb.get(symbol)
            return v
        elif 's_expr' == ast.data:
            symbol = ast.children[0]
            v = cb.get(symbol)
            return v
        elif 'wrap' == ast.data:
            return self.do_interpret_expr(ast.children[0], cb, symbol)
        elif ast.data in ['f_expr0', 'f_expr1', 'f_expr2']:
            func = ast.children[0]
            args, kwargs = [], []
            for c in ast.children[1:]:
                if 'args' == c.data:
                    args = c.children
                if 'kwargs' == c.data:
                    kwargs = c.children
            vargs = [self.do_interpret_expr(arg, cb) for arg in args]
            nkwargs = int(len(kwargs)/2)
            ks = [kwargs[i*2] for i in range(nkwargs)]
            ws = [self.do_interpret_expr(kwargs[i*2+1], cb) for i in range(nkwargs)]
            kwargs = {ks[i]: ws[i] for i in range(nkwargs)}

            argtypes = [var.typeinfo for var in vargs]
            op = self.do_interpret_op(func, cb, argtypes)
            v = cb.new_variable(symbol, op.typecheck(argtypes))
            self.new_vnode(v, op, vargs, kwargs)

            cb.put(v.symbol, v)
            print("%s = %s(...)" % (v.symbol, func))
            return v
        elif 'sl_expr' == ast.data:
            rs, cond = ast.children

            v1 = self.do_interpret_expr(rs, cb)
            v2 = self.do_interpret_expr(cond, cb)
            argtypes = [v1.typeinfo, v2.typeinfo]

            op = self.do_interpret_op('select', cb, argtypes)

            v = cb.new_variable(symbol, op.typecheck(argtypes))
            self.new_vnode(v, op, [v1, v2])
            cb.put(v.symbol, v)
            print("%s = select(%s, %s)" % (v.symbol, v1.symbol, v2.symbol))
            return v
        ierror("%s is not a valid expression" % (ast))

    def do_interpret_value(self, ast, cb, symbol):
        if 'numeric' == ast.data:
            t, v = 'int', int(ast.children[0])
        elif 'string' == ast.data:
            t, v = 'string', str(ast.children[0])
        elif 'boolean' == ast.data:
            t, v = 'bool', str(ast.children[0])
        const = cb.new_constant(v, t)
        self.new_vnode(const)
        if symbol is not None:
            cb.put(symbol, const)
            print('%s = const(%s)' % (symbol, const.value))
        return const

    def do_interpret_op(self, fname, cb, argtypes):
        f = lookup_builtin_func(fname, argtypes)
        return f

    def do_interpret_branch(self, cond, branches, branch_type, cb):
        ccb = self.new_codeblock(cb)
        cv = self.do_interpret_expr(cond.children[0], ccb)

        assert cv.typeinfo == 'bool', 'type of condition must be bool: %s' % (cond)

        bcb = [self.new_codeblock(ccb) for b in branches]
        for i in range(len(branches)):
            self.do_interpret_program(branches[i], bcb[i])

        self.do_interpret_merge(ccb, bcb, guard_variable=cv, branch_type=branch_type)
        self.do_interpret_merge(cb, [ccb])
