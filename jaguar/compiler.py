#!/usr/bin/python
import re
from parser import parse
import utils

from opcodes import opcodes, reverse_opcodes

import rewriter


label_counter = [0]


def mksymbol():
    label_counter[0] += 1
    return '_' + str(label_counter[0] - 1)


# Compile LLL to EVM
def compile_lll(ast):
    symb = mksymbol()
    # Literals
    if not isinstance(ast, utils.astnode):
        return [utils.numberize(ast)]


    subcodes = map(compile_lll, ast.args[1:])

    # Seq
    if ast.fun == 'seq':
        o = []
        for subcode in subcodes:
            o.extend(subcode)
        return o
    elif ast.fun == 'unless':
        assert len(ast.args) == 3
        return subcodes[0] + ['$endif'+symb, 'JUMPI'] + \
               subcodes[1] + ['~endif'+symb]
    elif ast.fun == 'if':
        assert len(ast.args) == 4
        return subcodes[0] + ['NOT', '$else'+symb, 'JUMPI'] + \
               subcodes[1] + ['$endif'+symb, 'JUMP', '~else'+symb] + \
               subcodes[2] + ['~endif'+symb]
    elif ast.fun == 'until':
        return ['~beg'+symb] + subcodes[0] + ['$end'+symb, 'JUMPI'] + \
               subcodes[1] + ['$beg'+symb, 'JUMP', '~end'+symb]
    elif ast.fun == 'lll':
        LEN = '$begincode'+symb+'.endcode'+symb
        STARTSYMB, STARTIND = '~begincode'+symb, '$begincode'+symb
        ENDSYMB, ENDIND = '~endcode'+symb, '$endcode'+symb
        return [LEN, 'DUP'] + subcodes[1] + [STARTIND, 'CODECOPY'] + \
               [ENDIND, 'JUMP', STARTSYMB, '#CODE_BEGIN'] + subcodes[0] + \
               ['#CODE_END', ENDSYMB]
    elif ast.fun == 'alloc':
        return subcodes[0] + ['MSIZE', 'SWAP', 'MSIZE'] + \
               ['ADD', 1, 'SWAP', 'SUB', 0, 'SWAP', 'MSTORE8']
    elif ast.fun == 'array_lit':
        x = ['MSIZE', 'DUP']
        for s in subcodes:
            x += s + ['SWAP', 'MSTORE', 'DUP', 32, 'ADD']
        return x[:-3] if len(subcodes) > 0 else ['MSIZE']
    else:
        o = []
        for subcode in subcodes[::-1]:
            o.extend(subcode)
        return o + [ast.fun]

# Dereference labels
def dereference(c):
    label_length = utils.log256(len(c)*4)
    iq = [x for x in c]
    mq = []
    pos = 0
    labelmap = {}
    beginning_stack = [0]
    while len(iq):
        front = iq.pop(0)
        if not utils.is_numeric(front) and front[0] == '~':
            labelmap[front[1:]] = pos - beginning_stack[-1]
        elif front == '#CODE_BEGIN':
            beginning_stack.append(pos)
        elif front == '#CODE_END':
            beginning_stack.pop()
        else:
            mq.append(front)
            if utils.is_numeric(front):
                pos += 1 + max(1, utils.log256(front))
            elif front[:1] == '$':
                pos += label_length + 1
            else:
                pos += 1
    oq = []
    for m in mq:
        oqplus = []
        if utils.is_numeric(m):
            L = max(1, utils.log256(m))
            oqplus.append('PUSH' + str(L))
            oqplus.extend(utils.tobytearr(m, L))
        elif m[:1] == '$':
            vals = m[1:].split('.')
            if len(vals) == 1:
                oqplus.append('PUSH'+str(label_length))
                oqplus.extend(utils.tobytearr(labelmap[vals[0]], label_length))
            else:
                oqplus.append('PUSH'+str(label_length))
                value = labelmap[vals[1]] - labelmap[vals[0]]
                oqplus.extend(utils.tobytearr(value, label_length))
        else:
            oqplus.append(m)
        oq.extend(oqplus)
    return oq


def serialize(source):
    def numberize(arg):
        if utils.is_numeric(arg):
            return arg
        elif arg.upper() in reverse_opcodes:
            return reverse_opcodes[arg.upper()]
        elif arg[:4] == 'PUSH':
            return 95 + int(arg[4:])
        elif re.match('^[0-9]*$', arg):
            return int(arg)
        else:
            raise Exception("Cannot serialize: " + str(arg), source)
    return ''.join(map(chr, map(numberize, source)))


def deserialize(source):
    o = []
    i, j = 0, -1
    while i < len(source):
        p = ord(source[i])
        if j >= 0:
            o.append(p)
        elif p >= 96 and p <= 127:
            o.append('PUSH' + str(p - 95))
        else:
            o.append(opcodes[p][0])
        if j < 0 and p >= 96 and p <= 127:
            j = p - 95
        j -= 1
        i += 1
    return map(utils.tokenify, o)


def assemble(source):
    return serialize(dereference(source))


def compile(source):
    return assemble(compile_lll(rewriter.rewrite_to_lll(parse(source))))


def biject(source, byte):
    c = dereference(compile_lll(compile_to_lll(parse(source))))
    return c[int(byte)].metadata


def encode_datalist(vals):
    def enc(n):
        if utils.is_numeric(n):
            return ''.join(map(chr, utils.tobytearr(n, 32)))
        elif utils.is_string(n) and len(n) == 40:
            return '\x00' * 12 + n.decode('hex')
        elif utils.is_string(n):
            return '\x00' * (32 - len(n)) + n
        elif n is True:
            return 1
        elif n is False or n is None:
            return 0
    if isinstance(vals, (tuple, list)):
        return ''.join(map(enc, vals))
    elif vals == '':
        return ''
    else:
        # Assume you're getting in numbers or 0x...
        return ''.join(map(enc, map(utils.numberize, vals.split(' '))))


def decode_datalist(arr):
    if isinstance(arr, list):
        arr = ''.join(map(chr, arr))
    o = []
    for i in range(0, len(arr), 32):
        o.append(utils.frombytes(arr[i:i + 32]))
    return o
