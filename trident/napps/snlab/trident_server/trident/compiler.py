import json, uuid
from functools import reduce
from lark import Transformer
from napps.snlab.trident_server.trident.util import error
from napps.snlab.trident_server.trident.objects import Table
from napps.snlab.trident_server.trident.builtin import lookup_builtin_func, execute_builtin_func

FILE_PATH = "napps/snlab/trident_server/trident/"

def ierror(msg):
    error('compilation', msg)

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
    def __init__(self, name, context,  datatype, streamtype):
        assert datatype in ['string', 'int', 'float', 'bool']
        assert streamtype in STREAM_TYPES

        self.name = name
        self.context = context
        self.datatype = datatype
        self.streamtype = streamtype

    def __str__(self):
        return "stream attribute: %s [%s, %s]\n" % (self.name, self.datatype, self.streamtype)

class Transformer(object):
    def __init__(self):
        pass

    def string(self, token):
        return str(token).strip("'")

    def variable(self, token):
        return str(token.children[0].value)

ts = Transformer()

class LiveVariables(object):
    def __init__(self):
        self.sa = {}

    def regist_sa(self, ast):
        assert ast.data == 'stream_attribute'
        filename, name = ast.children
        filename, name = ts.string(filename), ts.string(name)
        with open(FILE_PATH + filename) as f:
            data = json.load(f)
            attr = data[name]
        assert 'datatype' in attr
        assert 'name' in attr
        assert 'streamtype' in attr

        name = attr['name']
        if name in self.sa:
            return "SA-" + name
        self.sa[name] = StreamAttribute(name, "unknown", attr['datatype'], attr['streamtype'])
        return "SA-" + name

    def regist_wp(self, ast):
        assert ast.data == 'way_point'
        return "Role-" + ts.string(ast.children[0])
        
    def __str__(self):
        ret = ""
        for s in self.sa:
            ret = ret + str(s)
        return ret

lv = LiveVariables()

class TridentCompiler(object):
    def __init__(self):
        self.binds = []
        self.tables = []
        self.symbols = {} # output -> corresponding table

    def add_virtual_sink(self, cb): # TODO
        appeared = {}
        for v in reversed(self.vnodes):
            var = v['var']
            if var.typeinfo == 'binding' and var.symbol not in appeared:
                appeared[var.symbol] = var

        v = cb.new_variable('virtualsink', 'binding')
        op = self.do_compile_op('virtualsink', cb, ['binding'] * len(appeared))
        self.new_vnode(v, op, appeared.keys())

    def compile_cond(ast): # compile a whole condition as a single table
        # TODO
        return
        
    def compile_bind(ast): # compile a bind as a single table
        # TODO
        return

    def do_compile(self, ast):
        for k in HEADERFIELD_TABLE:
            name = "pkt." + k
            self.symbols[name] = len(self.tables)
            self.tables.append(Table([k], [name]))

        self.compile(ast, "None")

        # add virtual sink
        key = []
        for t in self.binds:
            key.append(t.get_output())
        self.tables.append(Table(key, ["Path"]))

        return self.tables

    def compile(self, ast, in_g): # WARNING: only implement a subset of "subset grammar"
        if ast.data in ['start', 'pass', 'program']:
            for child in ast.children:
                self.compile(child, in_g)
        elif 'sa_dec' == ast.data:
            name = ts.variable(ast.children[0])
            self.symbols[name] = len(self.tables)
            self.tables.append(Table([lv.regist_sa(ast.children[1])], [name]))
        elif 'wp_dec' == ast.data:
            name = ts.variable(ast.children[0])
            self.symbols[name] = len(self.tables)
            self.tables.append(Table([lv.regist_wp(ast.children[1])], [name]))
        elif 'ra_dec' == ast.data:
            pass
            # TODO
            # constructing Paths according to Topology, Waypoint and Ra-expression
        elif 'bi_branches' == ast.data: # WARNING: only the following instructions can have guard
            condition, t_branch, f_branch = ast.children
            self.compile(condition, in_g)
            out_g = self.tables[len(self.tables) - 1].get_output()
            self.compile(t_branch, "1" + out_g)
            self.compile(f_branch, "0" + out_g)
        elif 'condition' == ast.data:
            self.compile_bind(ast.children)
        elif 'bind' == ast.data:
            self.compile_bind(ast.children)
            self.binds.append(len(self.tables) - 1)
        else:
            print("Unknown instruction: %s" % ast.data)
