# S-expression input of exactly the same as serpent.

import io
import utils

from python_2_3_compat import to_str, is_str


class BeginEnd:
    def __init__(self, begin, end, name,
                 allow_different_end = False, seek_different_end = False,
                 internal='continue'):
        self.begin = begin  # What begins and ends a expression.
        self.end   = end
        self.name  = name   # Name of the expression.
        self.allow_different_end = allow_different_end  # Whether other enders can stop it.
        self.seek_different_end  = seek_different_end   # Ignore other endings for speed.
        self.internal   = internal    # What to do with contents.

    def __repr__(self):
        return self.name + " " + self.begin

class Incorrect:
    def __init__(self, msg, parser, be=None):
        self.msg = msg
        self.line_i = parser.line_i
        self.be = be

    def __repr__(self):
        return str(self.line_i) + ": " + self.be.name + ", " + self.be.begin + ": " + self.msg


class SExprParser:

    # Class essentially just stops me from having to pass these all the time.
    # Just do SExprParser().parse(), dont neccesarily need a variable.
    def __init__(self, stream, line_i = 0,
                 start_end = [BeginEnd('(', ')', 'call'),
                              BeginEnd(';', '\n', 'comment', internal='scrub'),
                              BeginEnd('"', '"',  'str', internal='str')],
                 white=[' ', '\t', '\n'],
                 earliest_macro={}, fil='',
                 handle = lambda a,b: str(a).split()):
        if isinstance(stream, (str, unicode)):
            stream = io.StringIO(to_str(stream))

        self.stream = stream
        self.line_i = line_i
        self.start_end = start_end
        self.n_max = 16
        self.fil = fil  # Current file.
        self.handle = handle


    def readline(self):  # Helps reading lines and the number we have read.
        n, line = 0, self.stream.readline()

        while line == '' and n < self.n_max:  # TODO need stream.eof
            line, n = self.stream.readline(), n + 1
        self.line_i += n
        return line + '\n', n

    # Convenience function. Gets begin/end at position, if available.
    def begin_i(self, string):
        k, which = len(string), None
        for el in self.start_end:
            j = string.find(el.begin)
            if j != -1 and j < k:
                k, which = j, el
        return k,which

    def end_i(self, string):
        k, which = len(string), None
        for el in self.start_end:
            j = string.find(el.end)
            if j != -1 and j < k:
                k, which = j, el
        return k,which

    
    def ast(self, name, args):
        prep = []
        if name != 'call':
            prep = [name]
        return utils.astnode(prep + args, self.fil, self.line_i)

    # Parses just looking at the end. For instance for "strings"
    # TODO may want to have it parse, looking
    # beginners _and_ enders, but just returning as a single string.
    def parse_plain(self, begin, initial=''):
        cur = initial
        have = ''
        while True:
            i = cur.find(begin.end)
            if i != -1:
                return self.ast(begin.name, [have + cur[:i]]), cur[i + 1:]
            have += cur

            line, n = self.readline()
            if n == self.n_max:
                raise Incorrect("file/stream ended unexpectedly", self, begin)

    # Returns a pair of arguments, the result and the remaining string.
    def raw_parse(self, initial, begin):
        have, cur, out = '', initial, []

        while True:
            i, sub_begin = self.begin_i(cur)
            j, end = self.end_i(cur)
            #print(i,j, sub_begin, end)
            if (sub_begin is not None) and i <= j:
                out += self.handle(have + cur[:i], self)
                if sub_begin.internal == 'continue':
                    ast, cur = self.raw_parse(cur[i + 1:], sub_begin)
                elif sub_begin.internal in ['str','scrub']:
                    ast, cur = self.parse_plain(sub_begin, cur[i + 1:])
                if sub_begin.internal != 'scrub':
                    out.append(ast)    
                continue
            
            if begin.seek_different_end and end is not None:
                # End doesnt match beginning. (and it should)
                if begin is not end and not begin.allow_different_end:
                    raise Incorrect("ending", self, begin)

                out += self.handle(have + cur[:i], self)
                return self.ast(begin.name, out), cur[i + 1:]
            else:
                i = cur.find(begin.end)
                if i != -1:
                    out += self.handle(have + cur[:i], self)
                    return self.ast(begin.name, out), cur[i + 1:]

            have += cur
            cur, n = self.readline()
            if n == self.n_max:  # Ran out of stuff to read.
                if begin.end != 'top':
                    raise Incorrect("file/stream ended unexpectedly", self, begin)
                out += self.handle(have,self)
                return self.ast('top', out), ''

    def parse(self, initial='', begin=BeginEnd('top', 'top', 'top')):
        return self.raw_parse(initial, begin)[0]
