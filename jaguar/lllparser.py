import io
import parser


def parse_lll(stream):
    if isinstance(stream, (str, unicode)):
        stream = io.StringIO(unicode(stream))

    tokens, i = [], 0  # Line number and the tokens accumulated.
    i = 0
    while True:
        line, n = "", 0  # Get current line. (n for end of file.
        while len(line) == 0:
            line = line + stream.readline()
            i += 1
            n += 1
            if n > 16:  # TODO need stream.eof
                ast, v = _parse_lll(tokens, 0)
                return ast

        upto, upto2 = line.find('#'), line.find('//')  # Clumsy.
        if upto == -1:
            upto = len(line)
        if upto2 == -1:
            upto2 = len(line)
        upto = min(upto, upto2)

        for token in parser.tokenize(line[:upto]):  # Muck with tokens.
            token.line = i - 1
            token.metadata = [token.fil, token.line, token.char]

            tokens.append(token)

    ast, v = _parse_lll(tokens, 0)
    return ast


def _parse_lll(tokens, pos):
    m, sv, o = tokens[pos].metadata, tokens[pos].val, []
    if sv not in ['(', '{', '[', '@', '@@']:
        return tokens[pos], pos + 1
    elif sv == '@':
        node, pos = _parse_lll(tokens, pos+1)
        return parser.astnode('mload', [node], *m), pos
    elif sv == '@@':
        node, pos = _parse_lll(tokens, pos+1)
        return parser.astnode('sload', [node], *m), pos
    elif sv == '(':
        pos, o, watch = pos + 1, [], ')'
    elif sv == '{':
        pos, o, watch = pos + 1, [parser.token('seq')], '}'
    elif sv == '[':
        sv, pos, o, watch = '[[', pos + 1, [parser.token('mstore')], ']'
    else:
        raise Exception(sv)
    while tokens[pos].val != watch:
        sub, pos = _parse_lll(tokens, pos)
        o.append(sub)
    pos += 1
    if sv in ['[', '[['] and tokens[pos].val != ']':
        sub, pos = _parse_lll(tokens, pos)
        o.append(sub)
    if len(o) == 0:
        o.append(parser.token('seq'))
    if len(o) == 3 and isinstance(o[0], parser.token) and o[0].val == 'mstore' and \
            isinstance(o[1], parser.astnode) and len(o[1].args) == 1 and \
            o[1].fun == 'mstore':
        o = [parser.token('sstore'), o[1].args[0], o[2]]
    return parser.astnode(o[0].val, o[1:], *m), pos


def write_lll_stream(ast, stream):
    prep = {'mload':'@', 'sload':'@@' }
    setting = {'mstore':('[',']'), 'sstore':('[[', ']]')}
    surround = {'seq':('{','}','\n'), 'str':('"','"','')}
    if ast.fun in prep:
        if len(ast.args) != 1:
            raise Exception("%s input wrong length" % ast.fun, val)
        stream.write(prep[ast.fun])
        write_lll_stream(stream, ast.args[1])
    elif ast.fun in setting:
        if len(ast.args) != 2:
            raise Exception("%s input wrong length" % ast.fun, val)
        b,a = setting[ast.fun]
        stream.write(b)
        write_lll_stream(ast.args[0])
        stream.write(a + ' ')
        write_lll_stream(ast.args[1])
    elif ast.fun in surround:
        b,a, between = surround[ast.fun]
        stream.write(b)
        for el in ast.args:
            stream.write(between)
            write_lll_stream(ast, stream)
        stream.write(a)
    elif len(ast.args) == 0:
        stream.write('()')
    else:
        stream.write('(')
        write_lll_stream(ast.args[0], stream)
        for el in ast.args[1:]:
            stream.write(' ')
            write_lll_stream(el, stream)
        stream.write(')')


def write_lll(ast):
    s = io.StringIO()
    write_lll_stream(ast, s)
    s.seek(0)
    return s.read()
