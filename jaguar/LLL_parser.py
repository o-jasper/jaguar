
import io
from s_expr_parser import SExprParser, BeginEnd, Incorrect
from utils import astnode, is_string, to_string

def assert_len(ast, length, say="wrong_length, should be"):
    if len(ast) != length:
        raise Exception(say, length, len(ast), ast)

# Returns what it got and what is left.
def lll_to_s_expr(inp, metadata=None):
    if isinstance(inp, list):
        loads = {'@':'mload', '@@':'sload'}
        if inp[0] in loads:
            got, left = lll_to_s_expr(inp[1:], metadata)
            return astnode([loads[inp[0]], got], *metadata), left
        elif isinstance(inp[0], astnode) and inp[0].fun == 'aref':
            got, left = lll_to_s_expr(inp[1:], metadata)
            assert len(inp[0]) == 2
            if inp[0][1].fun == 'aref':
                mod_node = astnode(['top'] + inp[0][1].args[1:], *metadata)
                index = lll_to_s_expr(mod_node, metadata)[1]
                return astnode(['sstore', index, got], *metadata), left
            else:
                mod_node = astnode(['top'] + inp[0].args[1:], *metadata)
                index = lll_to_s_expr(mod_node, metadata)[1]
                return astnode(['mstore', index, got], *metadata), left
        else:
            return inp[0], inp[1:]
    elif isinstance(inp, astnode):
        left = inp.args[1:]
        out = [inp.fun]
        while len(left) > 0:
            got, left = lll_to_s_expr(left, metadata or inp.metadata)
            out.append(got)
        return astnode(out, *inp.metadata)
    else:
        return inp


def lll_split(string):
    o = []
    for el in string.split():
        for sel in el.split(':'):
            if sel != '':
                o.append(sel)
    return o


class LLLParser(SExprParser):
    # Class essentially just stops me from having to pass these all the time.
    # Just do SExprParser().parse(), dont neccesarily need a variable.
    def __init__(self, stream, line_i = 0, fil='', do_comments=True):
        if isinstance(stream, (str, unicode)):
            stream = io.StringIO(to_string(stream))

        self.stream = stream
        self.line_i = line_i

        comments_internal = ('comment' if do_comments else 'ignore')
        self.start_end = [BeginEnd('[', ']', 'aref'),
                          BeginEnd('(', ')', 'call'),
                          BeginEnd('{', '}', 'seq'),
                          BeginEnd(';', '\n', 'comment', internal=comments_internal,
                                   ignore_alt_end=True, ignore_as_alt_end=True),
                          BeginEnd('"', '"', 'str', internal='str')]
        self.n_max = 16
        self.fil = fil  # Current file.

    def handle(self, in_string ,b):
        ret = []
        for string in lll_split(in_string):
            
            i = string.find('@') # Separate @
            if i == -1:
                ret.append(str(string))
            elif i != 0:
                raise Incorrect('@ or @@ may not be in middle of symbol.', self, None)
            elif str(string) in ['@', '@@']:
                ret.append(str(string))
            elif string[i + 1] == '@':
                ret += [str('@@'), str(string[i+2:])]
            else:
                ret += [str('@'), str(string[i+1:])]
        ret2 = []
        for el in ret:
            ret2 += el.split(':')
        return ret2

    def parse_lll(self, initial=''):
        return lll_to_s_expr(self.parse(initial))

def write_str(stream, what):
    stream.write(to_string(what))

class LLLWriter:

    def __init__(self, mload='@', mstore='[', sload='@@',sstore='[[', config=None):
        self.config = {} if config is None else config
        def sc(name, to):
            if name not in self.config:
                self.config[name] = to
        sc('mload',  mload)
        sc('mstore', mstore)
        sc('sload',  sload)
        sc('sstore', sstore)
        sc('str',    '"')
        sc('seq',    '{')
        sc('top',    True)

    # Handles lists, putting around spaces and whitespace betweem.
    def write_lll_list_stream(self, stream, inlist, o='(', c=')', b=' ', n=0, t='  '):
        if not isinstance(inlist, list):
            raise Exception('Not list: ', type(inlist), list)
        write_str(stream, o)
        if len(inlist) > 0:
            self.write_lll_stream(stream, inlist[0], n)
            for el in inlist[1:]:
                write_str(stream, b + t*n if b == '\n' else b)
                self.write_lll_stream(stream, el, n)
                        
        write_str(stream, c)

    # NOTE: a lot of cases, maybe something like
    # rewriter.simple_macro can do it better.
    def write_lll_special_stream(self, stream, val, name, c, n):
        if name == 'top':
            for el in val.args[1:]:
                self.write_lll_stream(stream, el, n)
                write_str(stream, "\n")
        elif name in ['mload','sload']:
            if len(val) != 2:
                raise Exception(name, 'wrong number of args 2!=', len(val), val, val.line)
            if c in ['@','@@']:
                write_str(stream, c)
                self.write_lll_stream(stream, val[1], n)
            elif c == 'var':  # (Note this is not LLL output)
                if type(val[1]) is str:
                    write_str(stream, val[1])
                else:
                    write_str(stream, '(mload ')
                    self.write_lll_stream(stream, val[1], n)
                    write_str(stream, ')')
        elif name in ['mstore', 'sstore']:
            if len(val) != 3:
                raise Exception(name, 'wrong number of args 3!=', len(val), val, val.line)
            if c in ['[', '[[']:
                write_str(stream, c)
                self.write_lll_stream(stream, val[1], n)
                write_str(stream, '] ' if c == '[' else ']] ')
                self.write_lll_stream(stream, val[2], n)
        elif name == 'seq':
            if c == '{':
                self.write_lll_list_stream(stream, val.args[1:],
                                           '{\n', '}\n', '\n', n + 1)
        elif name in ['when', 'unless', 'if', 'for']:
            self.write_lll_list_stream(stream, val.args, '(', ')', '\n', n + 1)
        elif name == 'str':
            assert len(val) == 2
            if c == '"':
                write_str(stream, '"' + val[1] + '"')
        else:
#            return self.write_lll_list_stream(stream, val, '(', ')', ' ', n)
            raise Exception('Invalid config', c, val)

    # Main 'portal' function.
    def write_lll_stream(self, stream, ast, n):
        if is_string(ast):
            write_str(stream, ast)
        elif isinstance(ast, astnode):
            if is_string(ast.fun):
                name = ast.fun.lower()
                if name in self.config:  # It is a special statement.
                    c = self.config[name]
                    if c != 'sexpr':  # (Unless config tells us to use s-expressions.)
                        return self.write_lll_special_stream(stream, ast, name, c, n)

            self.write_lll_list_stream(stream, ast.args, '(', ')', ' ', n)
        else:
            raise Exception('What is', ast, type(ast))

    def write_lll(self, tree):
        stream = io.StringIO()
        self.write_lll_stream(stream, tree, 0)
        stream.seek(0)  # Dont forget to read back!
        return stream.read()


def all_comments(ast):
    ret = []
    if isinstance(ast, astnode):
        for el in ast.comments:
            ret.append(el[1])
        ret += all_comments(ast.args)
    elif isinstance(ast, list):
        for el in ast:
            ret += all_comments(el)
    return ret
