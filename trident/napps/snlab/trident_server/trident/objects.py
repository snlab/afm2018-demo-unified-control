import uuid
import numpy as np

class Packet(object):
    def __init__(self, sip, dip, sport, dport, ipproto):
        self.sip = sip
        self.dip = dip
        self.sport = sport
        self.dport = dport
        self.ipproto = ipproto

    def __repr__(self):
        return '<%s,%s,%d,%d,%s>' % (self.sip, self.dip, self.sport, self.dport, self.ipproto)

class Table(object):
    """
    Table: Flow table data structure. 
    attr: Flow table attributes. NOTE: ALL KEY ATTR MUST APPEAR BEFORE NOT KEY ATTR
    key: Flow table primary key
    rules: Flow table's set of rules
    """
    def __init__(self, key, act, typ = 'assignment'):
        self.key = key
        self.act = act
        self.typ = typ # typ includes 'assignment', 'header', 'stream_attribute', 'phi', 'super_sink' and ast('route-algebra')
        self.rules = np.array([], dtype=object)
        # records: inputs, itself
        # tags: updating -> true means the table has changed

    def get_key(self):
        return self.key

    def get_act(self):
        return self.act

    def get_rules(self):
        return self.rules

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
            if len(rule) != 1 + len(self.key) + len(self.act):
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

#     def rule_union(ax, ay, rx, ry, ajoin):
#     """
#     rule_union: computes the union of two rules, coalescing any shared attributes.
#     ax: rule 1's attributes
#     ay: rule 2's attributes
#     rx: rule 1's values
#     ry: rule 2's values
#     ajoin: the union of Rule 1 and Rule 2's attributes
# 
#     returns rjoin: The union of Rule 1 and Rule 2's values, coalescing shared attributes
#     """
#     pri_ind = 0    #Priority is always the first value in a rule
#     first_attr_ind = 1 #Attributes start from index 1
#     
#     rjoin = np.zeros(len(ajoin), dtype=object)  #rjoin: The rule union
#     rjoin[pri_ind] = str(int(rx[PRI_IND]) + int(ry[PRI_IND]))
#     
#     for i in range(1, len(ajoin)): #Don't join priority
#         rx_ind = np.where(ax == ajoin[i])[0]
#         ry_ind = np.where(ay == ajoin[i])[0]
#         #print "attr:{}, rx_ind:{}, ry_ind:{}".format(ajoin[i], rx_ind, ry_ind)
#         
#         if len(rx_ind) > 0 and len(ry_ind) > 0:
#             rjoin[i] = coalesce(rx[rx_ind[0]], ry[ry_ind[0]])
#             #print "coalesce:{} and {} -> {}".format(rx[rx_ind[0]], ry[ry_ind[0]], rjoin[i])
#             if rjoin[i] == None:
#                 return None
#         elif len(rx_ind) > 0:
#             rjoin[i] = rx[rx_ind[0]]
#         else: 
#             rjoin[i] = ry[ry_ind[0]]
# 
#     return rjoin
# 
#     def flow_join(trgt): # dummy join
#         key = []
#         for attr in self.key:
#             key.append(attr)
# 
#         for attr in trgt.key:
#             if attr not in trgt.get_act():
#                 key.append(attr)
# 
#         rules = []
#         for rx in self.rules:
#             for ry in trgt.get_rules():
#                 rxy = rule_union(tx.get_attr(), ty.get_attr(), rx, ry, attr)
#                 if rx is not None:
#                     rules.append(rxy)
#         
#         txy = table(key, 
#         txy.add_rules(rules)
#         return txy

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
