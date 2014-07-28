
import io
from python_2_3_compat import to_str, is_str
from s_expr_parser import SExprParser, BeginEnd

def assert_len(ast, length, say="wrong_length, should be"):
    if len(ast) != length:
        raise Exception(say, length, len(ast), ast)


def lll_to_s_expr_munch(ast):
    if len(ast) == 0:
        return ast, []

    sm_load = {'@':'mload', '@@':'sload'}
    el = ast[0]
    if is_str(el) and el in sm_load:
        got,left = lll_to_s_expr_munch(ast[1:])
        return [sm_load[el], got], left
    elif type(el) is list and len(el) > 0 and is_str(el[0]) and el[0].lower() == 'aref':
        assert_len(el, 2)
        got,left = lll_to_s_expr_munch(ast[1:])
        if type(el[1]) is list and el[1][0].lower() == 'aref':
            assert_len(el, 2)  # (aref (aref <a>)) <b> -> (sstore <a> <b>)
            return ['sstore', lll_to_s_expr_munch(el[1][1:])[0], got], left
        else:  # (aref <a>) <b> -> (mstore <a> <b>)
            return ['sstore', lll_to_s_expr_munch(el[1:])[0], got], left
    else:
        return lll_to_s_expr(el), ast[1:]
        

# Assumes `sstore`, `mstore`, `sload`, `mload`, will do vars.
def lll_to_s_expr(ast):

    if type(ast) is list:
        left, ret = ast, []
        while len(left) > 0:
            got, left = lll_to_s_expr_munch(left)
            ret.append(got)
        return ret
    elif is_str(ast):
        if len(ast) == 0:
            raise Exception('Zero length strings not allowed in ast')

        assert ast not in ['@@','@']

        if ast[0] == '@':  # @ straight onto a name.
            assert len(ast) > 1
            if ast[1] == '@':
                assert len(ast) > 2
                return ['sload', ast[2:]]
            return ['mload', ast[1:]]

        return ast
    else:
        raise Exception('Dont expect type in AST:', type(ast), ast)


class LLLParser(SExprParser):
    # Class essentially just stops me from having to pass these all the time.
    # Just do SExprParser().parse(), dont neccesarily need a variable.
    def __init__(self, comment_name=None):

        int_handling = ('scrub' if comment_name is None else 'str')
        self.start_end = [BeginEnd('[', ']', 'aref'),
                          BeginEnd('(', ')'),
                          BeginEnd('{', '}', 'seq'),
                          BeginEnd(';', '\n', comment_name,
                                   internal_handling=int_handling),
                          BeginEnd('"', '"', 'str', internal_handling='str',
                                   wrong_end='ignore')]
        self.wrong_end_warning = 'warn'
        self.white = [' ', '\t', '\n', ':']
        self.earliest_macro = {}  # Dictionary of functions that act as macros.

    def parse_lll_stream(self, stream, initial=''):
        return lll_to_s_expr(self.parse_stream(stream, initial))

    def parse_lll(self, string):
        return self.parse_lll_stream(io.StringIO(to_str(string)))

    def parse_lll_file(self, file, initial=''):
        with open(file, 'r') as stream:
            tree = self.parse_lll_stream(stream, initial)
        return tree

def write_str(stream, what):
    stream.write(to_str(what))

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

    # Handles lists, putting around spaces and whitespace betweem.
    def write_lll_list_stream(self, stream, inlist, o='(', c=')'):
        if type(inlist) is not list:
            raise Exception('Not list: ', type(inlist), list)
        write_str(stream, o)
        if len(inlist) > 0:
            self.write_lll_stream(stream, inlist[0])
            for el in inlist[1:]:
                write_str(stream, ' ')
                self.write_lll_stream(stream, el)
        write_str(stream, c)

    # NOTE: a lot of cases, maybe something like
    # rewriter.simple_macro can do it better.
    def write_lll_special_stream(self, stream, val, name, c):
        if name in ['mload','sload']:
            if len(val) != 2:
                raise Exception("%s input wrong length" % name, val)
            if c in ['@','@@']:
                write_str(stream, c)
                return self.write_lll_stream(stream, val[1])
            elif c == 'var':  # (Note this is not LLL output)
                if type(val[1]) is str:
                    write_str(stream, val[1])
                else:
                    write_str(stream, '(mload ')
                    self.write_lll_stream(val[1])
                    write_str(stream, ')')
                return
        elif name in ['mstore', 'sstore']:
            assert len(val) == 3
            if c in ['[', '[[']:
                write_str(stream, c)
                self.write_lll_stream(stream, val[1])
                write_str(stream, '] ' if c == '[' else ']] ')
                return self.write_lll_stream(stream, val[2])
        elif name == 'seq':
            if c == '{':
                return self.write_lll_list_stream(stream, val[1:], '{', '}')
        elif name == 'str':
            assert len(val) == 2
            if c == '"':
                return write_str(stream, '"' + val[1] + '"')
        else:
            return self.write_lll_list_stream(stream,val, '(', ')')
        raise Exception('Invalid config', c, val)

    # Main 'portal' function.
    def write_lll_stream(self, stream, ast):
        if type(ast) is list:
            if is_str(ast[0]):
                name = ast[0].lower()
                if name in self.config:  # It is a special statement.
                    c = self.config[name]
                    if c != 'sexpr':  # (Unless config tells us to use s-expressions.)
                        return self.write_lll_special_stream(stream, ast, name, c)
            self.write_lll_list_stream(stream, ast, '(', ')')
        else:
            write_str(stream, ast)

    def write_lll(self, tree):
        stream = io.StringIO()
        self.write_lll_stream(stream, tree)
        stream.seek(0)  # Dont forget to read back!
        return stream.read()
