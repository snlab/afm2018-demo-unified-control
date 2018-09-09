import uuid
import numpy as np

class Table(object):
    """
    Table: Flow table data structure. 
    attr: Flow table attributes. NOTE: ALL KEY ATTR MUST APPEAR BEFORE NOT KEY ATTR
    key: Flow table primary key
    rules: Flow table's set of rules
    """
    def __init__(self, attr, key):
        self.attr = np.array(attr)
        self.key = np.array(key)
        self.rules = np.array([], dtype=object)

    def add_rules(self, rules):
        """
        add_rules: Add rules to table's set of rules.
        """
        for rule in rules:
            if len(rule) != len(self.attr):
                print "Table: Rule has the wrong number of attr: {}".format(rule)
                print "Attr list is:{}".format(self.attr)
    
        if len(self.rules) > 0:
            self.rules = np.concatenate((self.rules, np.array(rules, dtype=object)), axis=0)
        else:
            self.rules = np.array(rules, dtype=object)

    def __str__(self):
        not_key_attr = []
        for attr_i in self.attr[1:]:
            if attr_i not in self.key:
                not_key_attr.append(attr_i)

        out = "-------\n"
        out += "{} -> {}\n".format(self.key, not_key_attr)
        out += "{}\n".format(self.attr)
        for rule in self.rules:
            out += "{}\n".format(rule)
        out += "-------\n"
        return out

class Node(object): # TODO
    def __init__(self):
        # self.parents =

    def update(self, args): # args are inputs
        # self.parents = array of Node
        # self.records = previous inputs, i.e., join of parents

        # if parents update or <inputs> not in records:
            # self.executor = factor: <inputs> -> <output>
            # self.records = update acoording to executor
            # self.table = update according to executor

        # label as update for children

class Instruction(object):
    def __init__(self, ctx, inst_type, ret_type, var_in, var_out):
        self.ctx = ctx
        self.inst_type = inst_type
        self.ret_type = ret_type
        self.var_in = var_in
        self.var_out = var_out

    def execute(self, pkt, rs):
        """
        pkt: packet
        rs: reactive system
        """
        pass

    def __str__(self):
        varout = ','.join(self.var_out)
        varin = ','.join(self.var_in)
        return varout + '=' + inst_type + '(' + varin + ')'

class Variable(object):
    def __init__(self, symbol, stream_type):
        self.symbol = symbol
        self.key = symbol + uuid.uuid4().hex
        self.stream_type = stream_type

    def get(self, rs):
        pass

    def __str__(self):
        return self.symbol

class Block(object):
    def __init__(self, parent):
        self.parent = parent
        self.symbols = {}
        self.instructions = []

    def get(self, symbol):
        if symbol in self.symbols:
            return self.symbols[symbol]
        if parent is not None:
            return self.parent.get(symbol)
        return None

    def put(self, symbol, variable):
        self.symbols[symbol] = variable

HEADER_TABLE = {
    'sip': 'string',
    'dip': 'string',
    'sport': 'int',
    'dport': 'int',
    'proto': 'string'
}

KEY_FUNCTION = {
    'global': lambda pkt: 1,
    'tcp-5-tuple': lambda pkt: 'x'.join([pkt.sip, pkt.dip, pkt.sport, pkt.dport, pkt.proto]),
    'dst-ip': lambda pkt: pkt.dip,
    'src-ip': lambda pkt: pkt.sip
}
