# S-expression input of exactly the same as serpent.

import io
from python_2_3_compat import to_str, is_str


class BeginEnd:
    def __init__(self, begin, end, name=None,
                  allow_different_end = False, seek_different_end = False,
                  internal_handling = 'continue',
                  wrong_end = 'default'):
        self.begin = begin
        self.end   = end
        self.name  = name
        self.allow_different_end = allow_different_end
        self.seek_different_end  = seek_different_end
        self.internal_handling   = internal_handling
        self.wrong_end = wrong_end


class SExprParser:

    # Class essentially just stops me from having to pass these all the time.
    # Just do SExprParser().parse(), dont neccesarily need a variable.
    def __init__(self, start_end = [BeginEnd('(', ')'),
                                    BeginEnd(';', '\n', internal_handling='scrub'),
                                    BeginEnd('"', '"',  'str', internal_handling='str',
                                             wrong_end='ignore')],
                 wrong_end_warning=True,
                 white=[' ', '\t', '\n'],
                 earliest_macro={}):
        self.start_end = start_end
        self.wrong_end_warning = wrong_end_warning
        self.white = white
        self.earliest_macro = {}  # Dictionary of functions that act as macros.


    # Convenience function. Gets begin/end at position, if available.
    def begin_here(self, string):
        for el in self.start_end:
            if string[:len(el.begin)] == el.begin:
                return el
        return None

    def end_here(self, string):
        for el in self.start_end:
            if string[:len(el.end)] == el.end:
                return el
        return None

    # Parses just looking at the end. TODO may want to have it parse, looking
    # beginners _and_ enders, but just returning as a single string.
    def raw_parse_plain(self, stream, initial='', end=')'):
        cur = initial
        i = 0
        if len(cur) < len(end):
            cur = cur + stream.readline()

        while cur[i:i + len(end)] != end:
            i += 1
            n = 0
            while i + len(end) > len(cur):
                cur = cur + stream.readline()
                n += 1
                if n > 16:  # TODO need stream.eof
                    return cur[i + len(end):], cur[:i]

        return cur[i + len(end):], cur[:i]

    # Returns a pair of arguments, the result and the remaining string.
    def raw_parse_stream(self, stream, initial='',
                         begin=BeginEnd('top', ')', 'top')):
        cur = initial
        out = []

        def add(what):
            if what != '':  # Dont do empty strings.
                out.append(what)

        def add_sub(added):
            if len(added) > 0 and is_str(added[0]) and added[0] in self.earliest_macro:
                out.append(self.earliest_macro[added[0]](added))
            else:
                out.append(added)

        i = 0
        while True:

            while i < len(cur):

                if cur[i] in self.white:  # Whitespace separates symbols.
                    add(cur[:i])
                    cur = cur[i + 1:]  # Update cur and integer.
                    i = 0
                    continue

                # (cheaper way, only checks the current one.)
                if cur[i:i+len(begin.end)] == begin.end:
                    add(cur[:i])
                    return cur[i + len(begin.end):], out
                # Potentially stop substree.
                elif self.wrong_end_warning in ['accept', 'warn', 'assert']:

                    end = self.end_here(cur[i:])

                    if end is not None and end.wrong_end != 'ignore':
                        if end.end != begin.end and \
                           end.allow_different_end and begin.seek_different_end:
                            if self.wrong_end_warning == 'warn':
                                print("Warning, beginner and ender didnt match %s vs %s" %
                                      (end, se))
                                add(cur[:i])
                                return cur[i + len(begin.end):], out
                            raise((end, begin, i))  # Error, starter and ender did not match.
                        else:  # Correct ending, or ignoring.
                            add(cur[:i])
                            return cur[i + len(begin.end):], out

                # Potentially start subtree.
                start = self.begin_here(cur[i:])
                if start is not None:
                    add(cur[:i])

                    if start.internal_handling in ['scrub', 'str']:  # Dont parse inside.
                        left, got = self.raw_parse_plain(stream,
                                                         cur[i + len(start.begin):],
                                                         start.end)

                        if start.internal_handling == 'str':  # Use it.
                            add_sub([start.name, got])

                        cur = left
                    else:
                        left, ret = self.raw_parse_stream(stream,
                                                          cur[i + len(start.begin):],
                                                          begin=start)
                        # The ender-starter associated is optionally attached.
                        if start.name is None:
                            add_sub(ret)
                        else:
                            add_sub([start.name] + ret)
                        cur = left
                    i = 0  # As `cur` is set to be used with reset integer.
                    continue
                i += 1

            n = 0

            extend = stream.readline()
            while extend == '':  # TODO need stream.eof
                extend = stream.readline()
                n += 1
                if n > 16:
                    if cur != '':
                        out.append(cur)
                        return '', out
                    else:
                        return '', out
            cur = cur + extend

        assert False

    def parse_stream(self, stream, initial=''):
        return self.raw_parse_stream(stream, initial=initial)[1]

    def parse_file(self, file, initial=''):
        with open(file, 'r') as stream:
            tree = self.parse_stream(stream, initial)
        return tree

    def parse(self, string):
        return self.parse_stream(io.StringIO(to_str(string)))


# Note: it doesnt do indentation.. or newlines.
# also only does the s-expression way.
def s_expr_write(stream, input, o='(', c=')', w=' '):
    def handle_1(el):
        if type(el) is list:
            stream.write(to_str(o))
            s_expr_write(stream, el, o=o, c=c, w=w)
            stream.write(to_str(c))
        else:
            stream.write(to_str(el))

    if len(input) > 0:
        handle_1(input[0])
        for el in input[1:]:
            stream.write(to_str(w))
            handle_1(el)


def s_expr_str(tree, o='(', c=')', w=' '):
    stream = io.StringIO()
    s_expr_write(stream, tree, o=o, c=c, w=w)
    stream.seek(0)  # Dont forget to read back!
    return stream.read()
