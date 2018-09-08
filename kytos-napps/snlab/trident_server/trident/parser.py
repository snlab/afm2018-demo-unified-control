from lark import Lark, Transformer

class TridentParser(object):
    def parse(self, program):
        return None

class LarkParser(TridentParser):
    def __init__(self, filename):
        with open(filename) as f:
            self.parser = Lark(f.read())

    def parse(self, program):
        return self.parser.parse(program)
