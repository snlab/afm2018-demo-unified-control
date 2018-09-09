import uuid
import numpy as np

class Table(object):
    """
    Table: Flow table data structure. 
    attr: Flow table attributes. NOTE: ALL KEY ATTR MUST APPEAR BEFORE NOT KEY ATTR
    key: Flow table primary key
    rules: Flow table's set of rules
    """
    def __init__(self, key, act):
        self.key = key
        self.act = act
        self.rules = np.array([], dtype=object)

    # def set_dependency(self, parents):
        # TODO
        # self.parents
        # self.inputs
        # self.table
        # self.updating

    def get_output(self):
        return act[len(act) - 1]

    def add_rules(self, rules):
        """
        add_rules: Add rules to table's set of rules.
        """
        for rule in rules:
            if len(rule) != len(self.key) + len(self.act):
                print("Table: Rule has the wrong number of attr: %s" % rule)
                print("Attr list is: %s -> %s" % self.key, self.act)
    
        if len(self.rules) > 0:
            self.rules = np.concatenate((self.rules, np.array(rules, dtype=object)), axis=0)
        else:
            self.rules = np.array(rules, dtype=object)
    
    def update_headers(self, pkt):
        # TODO
        pass

    def update_sa(self, sa):
        # TODO
        pass

    def equal(self, in0, in1):
        # TODO
        return True

    def update_accordingly(self, in_table): # in_table are inputs
        # self.parents is array of Node
        
        updating = False
        for t in self.parents:
            if t.updating:
                updating = True
        
        if updating:
            new_inputs = production(self.parents)

            if not self.equal(inputs, new_inputs):
                # self.executor = factor: <inputs> -> <output>
                # self.rules = update acoording to executor
                self.updating = True


    def __str__(self):
        out = "-------\n"
        out += "{} -> {}\n".format(self.key, self.act)
        for rule in self.rules:
            out += "{}\n".format(rule)
        out += "-------\n"
        return out

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
