import uuid

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
