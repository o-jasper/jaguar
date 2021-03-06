import re, sys


class astnode():
    def __init__(self, args, fil='', line=0, char=0, comments=[]):
        assert isinstance(args, list)
        self.args = args
        self.metadata = [self.fil, self.line, self.char] = fil, line, char
        self.comments = comments

    @property
    def line_i(self):
        return self.line

    @property
    def fun(self):
        return self.args[0] if len(self.args) > 0 else ''

    def __repr__(self):
        if len(self.args) == 0:
            return '()'

        def semi_repr(x):
            return x if is_string(x) else repr(x)

        o = '(' + semi_repr(self.args[0])
        for el in self.args[1:]:
            o += ' ' + semi_repr(el)
        o += ')'
        return o

    def __len__(self):
        return len(self.args)

    def __getitem__(self, i):
        return self.args[i]

def astify(s, fil='', line=0, char=0):
    if isinstance(s, astnode):
        return astnode(map(lambda x: astify(x, *s.metadata), s.args), *s.metadata)
    elif isinstance(s, list):
        metadata = fil, line, char
        return astnode(map(lambda x: astify(x, *metadata), s), *metadata)    
    elif isinstance(s, (int, long)):
        return str(s)
    elif isinstance(s, (str, unicode)):
        return s
    else:
        assert False

def deastify(ast):
    if isinstance(ast, astnode):
        return map(deastify, ast.args)
    else:
        return str(ast)


is_numeric = lambda x: isinstance(x, (int, long))
def str_is_numeric(x):
    return x[:2] == '0x' or\
           (x[:1].isdigit() or x[0] in ['+','-']) and (x[1:].isdigit() or len(x[1:]) == 0)

is_string = lambda x: isinstance(x, (str, unicode))

to_string = unicode

# A set of methods for detecting raw values (numbers and strings) and
# converting them to integers
def frombytes(b):
    return 0 if len(b) == 0 else ord(b[-1]) + 256 * frombytes(b[:-1])


def fromhex(b):
    hexord = lambda x: '0123456789abcdef'.find(x)
    return 0 if len(b) == 0 else hexord(b[-1]) + 16 * fromhex(b[:-1])


def is_valuelike(b):
    if isinstance(b, (str, unicode)):
        if re.match('^[0-9\-]*$', b):
            return True
        if b[0] in ["'", '"'] and b[-1] in ["'", '"'] and b[0] == b[-1]:
            return True
        if b[:2] == '0x':
            return True
    return False


def log256(x):
    return 0 if x == 0 else (1 + log256(x / 256))


def tobytearr(n, L):
    return [] if L == 0 else tobytearr(n / 256, L - 1) + [n % 256]


def numberize(b):
    if is_numeric(b):
        return b
    elif b[0] in ["'", '"']:
        return frombytes(b[1:-1])
    elif b[:2] == '0x':
        return fromhex(b[2:])
    else:
        return int(b)

# For testing.
def in_there(ast, funs, vars):
    if isinstance(ast, astnode):
        if ast.fun in funs:
            return ast.fun
        for el in ast.args[1:]:
            got = in_there(el, funs,vars)
            if got:
                return got, ast
    else:
        return ast if (ast in vars) else None
