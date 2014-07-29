
import io
from python_2_3_compat import to_str, is_str
from s_expr_parser import SExprParser, BeginEnd, Incorrect
from utils import astnode, is_string

def assert_len(ast, length, say="wrong_length, should be"):
    if len(ast) != length:
        raise Exception(say, length, len(ast), ast)
        

def lll_to_s_expr(ast):

    if isinstance(ast, astnode):
        ms = {'@':'mload', '@@':'sload'}
        i, intermediate = 0, []
        while i < len(ast):
            el = ast[i]
            if el in ms:
                top = astnode([ms[el], None], *ast.metadata)
                add = top
                j = i
                while ast[j] in ms:
                    if j >= len(ast) - 1:  # Out of space.
                        raise Incorrect('Accessing; @@ or @ may not be last element',
                                        None, ast)
                    if i != j:
                        add = astnode([ms[ast[j]], add], *ast.metadata)
                    j += 1
                top.args[1] = ast[j]
                intermediate.append(add)
                i = j + 1
            else:
                intermediate.append(el)
                i += 1
        i, ret = 0, []
        while i < len(intermediate):
            el = intermediate[i]
            enter = el
            if isinstance(el, astnode) and len(el.args)>0 and el[0] == 'aref':
                if i >= len(intermediate) - 1:
                    raise Incorrect('Setting; [[..]] [...] may not be last element',
                                    el, None)
                if len(el) != 2:
                    raise Incorrect("Wrong number of arguments to aref ([])",
                                    el, None)
                if isinstance(el[1], astnode) and el[1][0] == 'aref':
                    enter = ['sstore', el[1][1], intermediate[i+1]]
                else:                
                    enter = ['mstore', el[1], intermediate[i + 1]]

                enter = astnode(enter, *ast.metadata)
                i += 2
            else:
                i += 1
            ret.append(lll_to_s_expr(enter))

        assert '@' not in ret and '@@' not in ret
        return astnode(ret, *ast.metadata)
    elif is_string(ast):
        assert ast not in ['@', '@@']
        return ast
    else:
        raise Exception('Dont expect type in AST:', type(ast), ast)


class LLLParser(SExprParser):
    # Class essentially just stops me from having to pass these all the time.
    # Just do SExprParser().parse(), dont neccesarily need a variable.
    def __init__(self, stream, line_i = 0, fil=''):
        if isinstance(stream, (str, unicode)):
            stream = io.StringIO(to_str(stream))

        self.stream = stream
        self.line_i = line_i

        self.start_end = [BeginEnd('[', ']', 'aref'),
                          BeginEnd('(', ')', 'call'),
                          BeginEnd('{', '}', 'seq'),
                          BeginEnd(';', '\n', 'comment', internal='scrub',
                                   ignore_alt_end=True, ignore_as_alt_end=True),
                          BeginEnd('"', '"', 'str', internal='str')]
        self.n_max = 16
        self.fil = fil  # Current file.

    def handle(self, in_string ,b):
        ret = []
        for string in in_string.split():
            i = string.find('@')
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
        return ret

    def parse_lll(self, initial=''):
        return lll_to_s_expr(self.parse(initial))

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
