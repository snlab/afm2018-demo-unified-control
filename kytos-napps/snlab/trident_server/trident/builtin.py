
from util import error

def terror(msg):
    error('typechecking', msg)

def quick_check(args, nlen, types):
    if len(args) != nlen:
        return False
    for i in range(nlen):
        if args[i] != types[i]:
            return False
    return True

class BuiltinFunction(object):
    def __init__(self, name):
        self.name = name

    def typecheck(self, args):
        terror("method %s not implemented" % ('typecheck'))

    def execute(self, args):
        terror("method %s not implemented" % ('execute'))

    def __str__(self):
        return self.name

class Equal(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'equal')

    def typecheck(self, args):
        if len(args) == 2 and args[0] == args[1]:
            return 'bool'
        return None

class NotEqual(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'not_equal')

    def typecheck(self, args):
        if len(args) == 2 and args[0] == args[1]:
            return 'bool'
        return None

class ShortcutAnd(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'sand')

    def typecheck(self, args):
        if quick_check(args, 2, ['bool', 'bool']):
            return 'bool'
        return None

class ShortcutOr(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'sor')

    def typecheck(self, args):
        if quick_check(args, 2, ['bool', 'bool']):
            return 'bool'
        return None

class And(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'and')

    def typecheck(self, args):
        if quick_check(args, 2, ['bool', 'bool']):
            return 'bool'
        return None

class Or(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'or')

    def typecheck(self, args):
        if quick_check(args, 2, ['bool', 'bool']):
            return 'bool'
        return None

class Add(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'add')

    def typecheck(self, args):
        if quick_check(args, 2, ['int', 'int']):
            return 'int'
        if quick_check(args, 2, ['string', 'string']):
            return 'string'
        return None

class Subtract(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'subtr')

    def typecheck(self, args):
        if quick_check(args, 2, ['int', 'int']):
            return 'int'
        return None

class GreaterThan(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'gt')

    def typecheck(self, args):
        if quick_check(args, 2, ['int', 'int']):
            return 'bool'
        return None

class LessThan(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'lt')

    def typecheck(self, args):
        if quick_check(args, 2, ['int', 'int']):
            return 'bool'
        return None

class GreaterThanOrEqual(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'gte')

    def typecheck(self, args):
        if quick_check(args, 2, ['int', 'int']):
            return 'bool'
        return None

class LessThanOrEqual(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'lte')

    def typecheck(self, args):
        if quick_check(args, 2, ['int', 'int']):
            return 'bool'
        return None

class Preference(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'prefer')

    def typecheck(self, args):
        if quick_check(args, 2, ['route-set', 'route-set']):
            return 'route-set'
        return None

class Concatenation(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'concat')

    def typecheck(self, args):
        if quick_check(args, 2, ['route-set', 'route-set']):
            return 'route-set'
        return None

class Union(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'union')

    def typecheck(self, args):
        if quick_check(args, 2, ['route-set', 'route-set']):
            return 'route-set'
        return None

class Intersection(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'intersect')

    def typecheck(self, args):
        if quick_check(args, 2, ['route-set', 'route-set']):
            return 'route-set'
        return None

class Difference(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'diff')

    def typecheck(self, args):
        if quick_check(args, 2, ['route-set', 'route-set']):
            return 'route-set'
        return None

SYM_INDICATOR_TYPES = [
    ('waypoint', 'waypoint'),
    ('waypoint', 'route-set'),
    ('route-set', 'waypoint'),
    ('route-set', 'route-set')
]

class UniSym(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'uni_sym')

    def typecheck(self, args):
        if len(args) == 2 and (args[0], args[1]) in SYM_INDICATOR_TYPES:
            return 'route-set'
        return None

class UniAsym(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'uni_asym')

    def typecheck(self, args):
        if len(args) == 2 and (args[0], args[1]) in SYM_INDICATOR_TYPES:
            return 'route-set'
        return None

class BiSym(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'bi_sym')

    def typecheck(self, args):
        if len(args) == 2 and (args[0], args[1]) in SYM_INDICATOR_TYPES:
            return 'route-set'
        return None

class BiLeftAsym(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'bi_lasym')

    def typecheck(self, args):
        if len(args) == 2 and (args[0], args[1]) in SYM_INDICATOR_TYPES:
            return 'route-set'
        return None

class BiRightAsym(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'bi_rasym')

    def typecheck(self, args):
        if len(args) == 2 and (args[0], args[1]) in SYM_INDICATOR_TYPES:
            return 'route-set'
        return None

class BiAsym(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'bi_asym')

    def typecheck(self, args):
        if len(args) == 2 and (args[0], args[1]) in SYM_INDICATOR_TYPES:
            return 'route-set'
        return None

class Inversion(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'inv')

    def typecheck(self, args):
        if quick_check(args, 1, ['route-set']):
            return 'route-set'
        return None

class Any(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'any')

    def typecheck(self, args):
        if quick_check(args, 1, ['route-set']):
            return 'route-set'
        return None

class Negation(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'not')

    def typecheck(self, args):
        if quick_check(args, 1, ['bool']):
            return 'bool'
        return None

class Waypoint(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'waypoint')

    def typecheck(self, args):
        return 'waypoint'

class Shortest(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'shortest')

    def typecheck(self, args):
        if quick_check(args, 1, ['route-set']):
            return 'route-set'
        return None

class Select(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'select')

    def typecheck(self, args):
        if quick_check(args, 2, ['route-set', 'bool']):
            return 'route-set'
        return None

class Bind(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'bind')

    def typecheck(self, args):
        if quick_check(args, 2, ['pkt', 'route-set']):
            return 'binding'
        return None

class Drop(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'drop')

    def typecheck(self, args):
        if quick_check(args, 1, ['pkt']):
            return 'binding'
        return None

class Test(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'test')

    def typecheck(self, args):
        return 'string'

class Phi(BuiltinFunction):
    def __init__(self, branch_type):
        BuiltinFunction.__init__(self, 'branch')
        self.branch_type = branch_type

    def typecheck(self, args):
        return args[0]

class VirtualSink(BuiltinFunction):
    def __init__(self):
        BuiltinFunction.__init__(self, 'virtual-sink')

    def typecheck(self, args):
        if quick_check(args, len(args), ['binding'] * len(args)):
            return 'binding'
        return None

BUILTIN_FUNCTABLE = {
    'equal': [Equal()],
    'not_equal': [NotEqual()],
    'sand': [ShortcutAnd()],
    'sor': [ShortcutOr()],
    'and': [And(), Intersection()],
    'or': [Or(), Union()],
    'add': [Add(), Concatenation()],
    'subtract': [Subtract(), Difference()],
    'gt': [GreaterThan()],
    'lt': [LessThan()],
    'gte': [GreaterThanOrEqual()],
    'lte': [LessThanOrEqual()],
    'preference': [Preference()],
    'uni_sym': [UniSym()],
    'uni_asym': [UniAsym()],
    'bi_sym': [BiSym()],
    'r_asym': [BiRightAsym()],
    'l_asym': [BiLeftAsym()],
    'bi_asym': [BiAsym()],
    'not': [Negation()],
    'inversion': [Inversion()],
    'any': [Any()],
    'Waypoint': [Waypoint()],
    'test': [Test()],
    'Shortest': [Shortest()],
    'bind': [Bind()],
    'drop': [Drop()],
    'virtualsink': [VirtualSink()],
    'select': [Select()]
}

def lookup_builtin_func(fname, argtypes):
    for f in BUILTIN_FUNCTABLE[fname]:
        if f.typecheck(argtypes) is not None:
            return f
    terror("No valid function %s(%s)" % (fname, ','.join(argtypes)))
