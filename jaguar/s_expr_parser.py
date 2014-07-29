# S-expression input of exactly the same as serpent.

import io
import utils

from python_2_3_compat import to_str, is_str


class BeginEnd:
    def __init__(self, begin, end, name,
                 allow_alt_end=None, seek_alt_end=False,
                 ignore_alt_end=False, ignore_as_alt_end=False,
                 internal='continue'):
        self.begin = begin  # What begins and ends a expression.
        self.end   = end
        self.name  = name   # Name of the expression.
        self.ignore_alt_end = ignore_alt_end
        self.allow_alt_end  = allow_alt_end  # Whether other enders can stop it.        
        if allow_alt_end is None:
            self.allow_alt_end = ignore_alt_end
        self.ignore_as_alt_end = ignore_as_alt_end
        self.seek_alt_end   = seek_alt_end   # May in future ignore other endings.
        self.internal   = internal    # What to do with contents.

    def __repr__(self):
        return self.name + " " + self.begin

class Incorrect:
    def __init__(self, msg, obj, be=None):
        self.msg = msg
        if obj is not None:
            self.line_i = obj.line_i
        else:
            self.line_i = 'u'
        self.be = be
        self.obj = obj

    def __repr__(self):
        o = str(self.line_i) + ": " + self.msg
        if self.obj is not None:
            o += '; ' + repr(self.obj)
        return o


class SExprParser:

    # Class essentially just stops me from having to pass these all the time.
    # Just do SExprParser().parse(), dont neccesarily need a variable.
    def __init__(self, stream, line_i = 0,
                 start_end = None, do_comments=True,
                 white=[' ', '\t', '\n'],
                 earliest_macro={}, fil='',
                 handle = lambda a,b: str(a).split()):
        if isinstance(stream, (str, unicode)):
            stream = io.StringIO(to_str(stream))

        self.stream = stream
        self.line_i = line_i
        self.start_end = start_end
        if start_end is None:
            comment_internal = ('comment' if do_comments else 'ignore')
            self.start_end = [BeginEnd('(', ')', 'call'),
                              BeginEnd(';', '\n', 'comment', internal=comment_internal,
                                       ignore_alt_end=True, ignore_as_alt_end=True),
                              BeginEnd('"', '"',  'str', internal='str')]
        self.n_max = 16
        self.fil = fil  # Current file.
        self.handle = handle


    def readline(self):  # Helps reading lines and the number we have read.
        n, line = 1, self.stream.readline()

        while line == '' and n < self.n_max:  # TODO need stream.eof
            line, n = self.stream.readline(), n + 1
        self.line_i += n
        return line + '\n', n

    # Gets begin/end at position, if available.
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

    
    def ast(self, name, args, comments=[]):
        prep = []
        if name != 'call':
            prep = [name]
        return utils.astnode(prep + args, self.fil, self.line_i, comments=comments)

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
        have, cur, out, next_comments = '', initial, [], []

        while True:
            i, sub_begin = self.begin_i(cur)
            j, end = self.end_i(cur)
            if j == -1:
                j = len(cur)

            if (sub_begin is not None) and i <= j:
                out += self.handle(have + cur[:i], self)
                if sub_begin.internal == 'continue':
                    ast, cur = self.raw_parse(cur[i + 1:], sub_begin)
                elif sub_begin.internal in ['str', 'ignore', 'comment']:
                    ast, cur = self.parse_plain(sub_begin, cur[i + 1:])
                if sub_begin.internal not in ['ignore', 'comment']:
                    ast.comments = next_comments
                    next_comments = []
                    out.append(ast)
                if sub_begin.internal == 'comment':
                    next_comments.append(ast[1])
                have = ''
                continue
            
            if end is not None:
                # End doesnt match beginning. (and it should)
                if begin.end != end.end and not (begin.allow_alt_end or end.ignore_as_alt_end):
                    raise Incorrect("ending %s != %s" % (begin.end, end.end), self, begin)

                if begin.end == end.end or not (begin.ignore_alt_end or end.ignore_as_alt_end):
                    out += self.handle(have + cur[:j], self)
                    return self.ast(begin.name, out, comments= next_comments), cur[j + 1:]

            have += cur
            cur, n = self.readline()
            if n == self.n_max:  # Ran out of stuff to read.
                if begin.end != 'top':
                    raise Incorrect("file/stream ended unexpectedly", self, begin)
                out += self.handle(have,self)
                return self.ast('top', out), ''

    def parse(self, initial='', begin=BeginEnd('top', 'top', 'top')):
        return self.raw_parse(initial, begin)[0]
