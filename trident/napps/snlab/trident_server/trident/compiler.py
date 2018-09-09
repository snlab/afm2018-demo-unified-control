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
        self.wp = {}

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

    def regist_wp(self, ast, name):
        assert ast.data == 'way_point'
        role = ts.string(ast.children[0])
        self.wp[name] = role
        
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

    def compile_cond(ast, in_g):
        assert ast.data == 'condition'
        # TODO modularize for compile()
        
    def compile_bind(ast, in_g):
        assert ast.data == 'bind'
        # TODO modularize for compile()

   #  def validate(self, ast):
   #      if len(ast.children) == 3:


   #  def dfs(self, node, ast):
   #      path.append(node)
   #      if path.validate(path, ast):
   #          ret_list.append(path.clone())

   #      for trgt in node.next():
   #          if not trgt in path:
   #              dfs(trgt, ast)
   #      path.pop()


    def calc_ra(self, ast): # TODO
        """
        return Table((start, end) -> (R)),
        where variable R represents path, 
        and capacity is not included in demo
        """
        assert ast.data == 'ra_dec'

        table = Table([], [], ast)
        # for node in Nodes
        #   DFS(node, ast) # update path during DFS, 
        #                         # use validation function to check if this path follows the 

        return table

    def do_compile(self, ast):
        for k in HEADERFIELD_TABLE:
            name = "pkt." + k
            self.symbols[name] = len(self.tables)
            self.tables.append(Table([k], [name], 'header'))

        self.compile(ast, "None")

        key = []
        for t in self.binds:
            key.append(t.get_output())
        self.tables.append(Table(key, ["Path"], 'super_sink'))

        return self.tables

    def compile(self, ast, in_g): # WARNING: only implement a subset of "subset grammar"
        if ast.data in ['start', 'pass', 'program', 'expr', 'expr2', 'expr3', 'expr4']: # structure tokens w/o meaning
            for child in ast.children:
                self.compile(child, in_g)
        elif 'sa_dec' == ast.data:
            name = ts.variable(ast.children[0])
            self.symbols[name] = len(self.tables)
            self.tables.append(Table([lv.regist_sa(ast.children[1])], [name], 'stream_attribute'))
        elif 'wp_dec' == ast.data: # Regist Waypoint w/o generating table
            name = ts.variable(ast.children[0])
            lv.regist_wp(ast.children[1], name)
        elif 'ra_dec' == ast.data: # Constructing table for route-algebra (which reads Waypoints)
            name = ts.variable(ast.children[0]) 
            self.symbols[name] = len(self.tables)
            self.tables.append(self.calc_ra(ast))
        elif 'bi_branches' == ast.data: # WARNING: only the following instructions can have guard variable
            condition, t_branch, f_branch = ast.children
            self.compile_cond(condition, in_g)
            out_g = self.tables[len(self.tables) - 1].get_output()
            self.compile(t_branch, "1" + out_g)
            self.compile(f_branch, "0" + out_g)
        elif 'bind' == ast.data:
            self.compile_bind(ast, in_g)
        else:
            print("Unknown instruction: %s" % ast.data)

tc = TridentCompiler()
