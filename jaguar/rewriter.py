from parser import parse
from utils import astnode, astify, is_string, str_is_numeric, numberize

# All AST rewrite rules go here
#
# Format specification (yo dawg, I herd you like DSLs so I made a DSL
# to help you write a compiler for your DSL into your other DSL so you
# can debug your code while you debug your code...)
#
# Use <xxx> to indicate parts of the code that can pattern-match anything
# Use '@xxx' to generate variables on the fly

preparing_simple_macros = [
    [
        ['if', '$cond', '$do', ['else', '$else']],
        ['if', '$cond', '$do', '$else']
    ],
    [
        ['elif', '$cond', '$do'],
        ['if', '$cond', '$do']
    ],
    [
        ['elif', '$cond', '$do', '$else'],
        ['if', '$cond', '$do', '$else']
    ],
    [
        ['code', '$code'],
        '$code'
    ]
]

simple_macros = [
    [
        ['access', 'msg.data', '$ind'],
        ['CALLDATALOAD', ['MUL', '32', '$ind']]
    ],
    [
        ['array', '$len'],
        ['alloc', ['MUL', '32', '$len']]
    ],
    [
        ['while', '$cond', '$do'],
        ['until', ['NOT', '$cond'], '$do']
    ],
    [
        ['while', ['NOT', '$cond'], '$do'],
        ['until', '$cond', '$do']
    ],
    [
        ['if', ['NOT', '$cond'], '$do'],
        ['unless', '$cond', '$do']
    ],
    [
        ['if', '$cond', '$do'],
        ['unless', ['NOT', '$cond'], '$do']
    ],
    [
        ['access', 'contract.storage', '$ind'],
        ['SLOAD', '$ind']
    ],
    [
        ['access', '$var', '$ind'],
        ['MLOAD', ['ADD', '$var', ['MUL', '32', '$ind']]]
    ],
    [
        ['set', ['access', 'contract.storage', '$ind'], '$val'],
        ['SSTORE', '$ind', '$val']
    ],
    [
        ['set', ['access', '$var', '$ind'], '$val'],
        ['arrset', '$var', '$ind', '$val']
    ],
    [
        ['arrset', '$var', '$ind', '$val'],
        ['MSTORE', ['ADD', '$var', ['MUL', '32', '$ind']], '$val']
    ],
    [
        ['getch', '$var', '$ind'],
        ['MOD', ['MLOAD', ['ADD', '$var', '$ind']], '256']
    ],
    [
        ['setch', '$var', '$ind', '$val'],
        ['MSTORE8', ['ADD', '$var', '$ind'], '$val']
    ],
    [
        ['send', '$to', '$value'],
        ['CALL', ['SUB', ['GAS'], '25'], '$to', '$value', '0', '0', '0', '0']
    ],
    [
        ['send', '$gas', '$to', '$value'],
        ['CALL', '$gas', '$to', '$value', '0', '0', '0', '0']
    ],
    [
        ['sha3', '$x'],
        ['seq', ['MSTORE', '@1', '$x'], ['SHA3', '@1', '32']]
    ],
    [
        ['sha3', '$start', '$len'],
        ['SHA3', '$start', ['MUL', '32', '$len']]
    ],
    [
        ['calldataload', '$start', '$len'],
        ['CALLDATALOAD', '$start', ['MUL', '32', '$len']]
    ],
    [
        ['id', '$0'],
        '$0'
    ],
    [
        ['return', '$x'],
        ['seq', ['MSTORE', '@1', '$x'], ['RETURN', '@1', '32']]
    ],
    [
        ['return', '$start', '$len'],
        ['RETURN', '$start', ['MUL', '32', '$len']]
    ],
    [
        ['&&', '$x', '$y'],
        ['if', '$x', '$y', '0']
    ],
    [
        ['||', '$x', '$y'],
        ['if', '$x', '$x', '$y']  # Double x; abstraction leak.
    ],
    [
        ['>=', '$x', '$y'],
        ['NOT', ['LT', '$x', '$y']]
    ],
    [
        ['<=', '$x', '$y'],
        ['NOT', ['GT', '$x', '$y']]
    ],
    [
        ['create', '$endowment', '$code'],
        ['seq',
            ['CREATE', '$endowment', '@1', ['lll', ['outer', '$code'], '@1']]]
    ],
    [
        ['msg', '$gas', '$to', '$val', '$dataval'],
        ['seq',
            ['MSTORE', '@1', '$dataval'],
            ['CALL', '$gas', '$to', '$val', '@1', '32', '@2', '32'],
            ['MLOAD', '@2']]
    ],
    [
        ['call', '$f', '$dataval'],
        ['msg', ['SUB', ['GAS'], '45'], '$f', '0', '$dataval']
    ],
    [
        ['msg', '$gas', '$to', '$val', '$inp', '$inpsz'],
        ['seq',
            ['CALL', '$gas', '$to', '$val', '$inp',
                ['MUL', '32', '$inpsz'], '@1', '32'],
            ['MLOAD', '@1']]
    ],
    [
        ['call', '$f', '$inp', '$inpsz'],
        ['seq',
            ['set', '@1', '$inpsz'],
            ['msg',
                ['SUB', ['GAS'], ['ADD', '25', ['MLOAD', '@1']]],
                '$f', '0', '$inp', ['MLOAD', '@1']]]
    ],
    [
        ['msg', '$gas', '$to', '$val', '$inp', '$inpsz', '$outsz'],
        ['seq',
            ['MSTORE', '@1', ['MUL', '32', '$outsz']],
            ['MSTORE', '@2', ['alloc', ['MLOAD', '@1']]],
            ['POP',
                ['CALL', '$gas', '$to', '$val',
                 '$inp', ['MUL', '32', '$inpsz'], '@2', ['MLOAD', '@1']]],
            ['MLOAD', '@2']]
    ],
    [
        ['outer', ['init', '$init', '$code']],
        ['seq',
            '$init',
            ['RETURN', '0', ['lll', '$code', '0']]]
    ],
    [
        ['outer', ['init', '$shared', '$init', '$code']],
        ['seq',
            '$shared',
            '$init',
            ['RETURN', '0', ['lll', ['seq', '$shared', '$code'], '0']]]
    ],
    [
        ['outer', '$code'],
        ['outer', ['init', ['seq'], '$code']]
    ],
    [
        ['seq', ['seq'], '$x'],
        '$x'
    ]
]

constants = [
    ['msg.datasize',     ['DIV', ['CALLDATASIZE'], '32']],
    ['msg.sender',       ['CALLER']],
    ['msg.value',        ['CALLVALUE']],
    ['tx.gasprice',      ['GASPRICE']],
    ['tx.origin',        ['ORIGIN']],
    ['tx.gas',           ['GAS']],
    ['contract.balance', ['BALANCE']],
    ['contract.address', ['ADDRESS']],
    ['block.prevhash',   ['PREVHASH']],
    ['block.coinbase',   ['COINBASE']],
    ['block.timestamp',  ['TIMESTAMP']],
    ['block.number',     ['NUMBER']],
    ['block.difficulty', ['DIFFICULTY']],
    ['block.gaslimit',   ['GASLIMIT']],
    ['stop',             ['STOP']],
]


def _getvar(ast):
    if is_string(ast) and not ast[0] == '"' and not str_is_numeric(ast) and \
       ast not in map(lambda x: x[0], constants) and \
       ast[0] != '_':
        inner = '__' + ast
        return astnode(['MLOAD', inner])


def _setvar(ast):
    if isinstance(ast, astnode) and ast.fun == 'set':
        prefix = '__' if ast[1][0] != '_' else ''
        inner = prefix + ast[1]
        return astnode(['MSTORE', inner, ast[2]], *ast.metadata)

synonyms = [
    ['|', 'OR'],
    ['or', 'OR'],
    ['xor', 'XOR'],
    ['&', 'AND'],
    ['and', 'AND'],
    ['!', 'NOT'],
    ['not', 'NOT'],
    ['byte', 'BYTE'],
    ['string', 'alloc'],
    ['create', 'CREATE'],
    ['+', 'ADD'],
    ['-', 'SUB'],
    ['*', 'MUL'],
    ['/', 'SDIV'],
    ['^', 'EXP'],
    ['%', 'SMOD'],
    ['<', 'SLT'],
    ['>', 'SGT'],
    ['%', 'SMOD'],
    ['#/', 'DIV'],
    ['#%', 'MOD'],
    ['#<', 'LT'],
    ['#>', 'GT'],
    ['=', 'set'],
    ['==', 'EQ'],
]

mathfuncs = [
    ['ADD', lambda x, y: x+y % 2**256],
    ['MUL', lambda x, y: x*y % 2**256],
    ['SUB', lambda x, y: (x-y+2**256) % 2**256],
    ['DIV', lambda x, y: x/y],
    ['MOD', lambda x, y: x % y],
    ['EXP', lambda x, y: pow(x, y, 2**256)],
    ['AND', lambda x, y: x & y],
    ['OR', lambda x, y: x | y],
    ['XOR', lambda x, y: x ^ y]
]


def _import(ast):
    if isinstance(ast, astnode) and ast.fun == 'import':
        filename = ast[1]
        if filename[0] == '"':
            filename = filename[1:-1]
        x = preprocess(parse(open(filename).read(), ast[1]))
        return astnode(['code', x], *ast.metadata)

def _str(ast):
    if isinstance(ast, astnode) and ast.fun == 'str':
        assert len(ast) == 2
        return '"' + ast[1] + '"'


def _inset(ast):
    if isinstance(ast, astnode) and ast.fun == 'inset':
        filename = ast[1]
        if filename[0] == '"':
            filename = filename[1:-1]
        return parse(open(filename).read(), ast[1])


label_counter = [0]


# Apply all rewrite rules
def rewrite(ast):
    while True:
        ast2 = None
        for macro in macros:
            ast2 = macro(ast2 or ast) or ast2
        if not ast2:  # None of them changed anything.
            break
        ast = ast2
    if is_string(ast):
        return ast
    else:
        return astnode([ast.fun] + map(rewrite, ast.args[1:]), *ast.metadata)


def analyze_and_varify_ast(ast, data):
    if isinstance(ast, astnode):
        if ast.fun in ['alloc', 'array_lit']:
            data['alloc_used'] = True
        if ast.fun == 'lll':
            inner = {"varhash": {}, "inner": []}
            argz = [finalize(ast[1], inner),
                    analyze_and_varify_ast(ast[2], data)]
            data["inner"].append(inner)
        else:
            argz = map(lambda x: analyze_and_varify_ast(x, data), ast.args[1:])
        return astnode([ast.fun] + argz, *ast.metadata)
    elif str_is_numeric(ast):
        return str(numberize(ast))
    else:
        if ast not in data['varhash']:
            data['varhash'][ast] = str(len(data['varhash']) * 32)
        if ast == '__msg.data':
            data['msgdata_used'] = True
        return data['varhash'][ast]


def finalize(expr, data=None):
    data = data or {"varhash": {}, "inner": []}
    e = analyze_and_varify_ast(expr, data)
    if len(data['varhash']) > 0 and data.get('alloc_used'):
        memsz = len(data['varhash']) * 32 - 1
        inner = astnode(['MSTORE8'] + map(str, [memsz, 0]))
        e = astnode(['seq', inner, e])
    if data.get('msgdata_used'):
        msg_data_addr = data['varhash']['__msg.data']
        alloc = astnode(['alloc', astnode(['CALLDATASIZE'])])
        node1 = astnode(['MSTORE', msg_data_addr, alloc])
        tok3 = astnode(['CALLDATASIZE'])
        node2 = astnode(['CALLDATACOPY', '0', msg_data_addr, tok3])
        e = astnode(['seq', node1, node2, e])
    return e


def preprocess(ast):
    return astnode(['outer', ast], *ast.metadata)


def rewrite_to_lll(ast):  # TODO some macroexpansions are theirs..
    if is_string(ast):
        ast = parse(ast)
    return finalize(rewrite(preprocess(ast)))


def analyze(ast):
    if is_string(ast):
        ast = parse(ast)
    ast = rewrite(preprocess(ast))
    data = {"varhash": {}, "inner": []}
    analyze_and_varify_ast(ast, data)
    return data


# macro, ast -> dict
def get_macro_vars(pattern, ast):
    d = {}
    if not isinstance(pattern, list):
        if pattern[0] == '$':
            d[pattern[1:]] = ast
        elif isinstance(ast, astnode) or pattern != ast:
            return None
    else:
        if not isinstance(ast, astnode) or len(ast) != len(pattern):
            return None
        for mitem, astitem in zip(pattern, ast.args):
            subdict = get_macro_vars(mitem, astitem)
            if subdict is None:
                return None
            for k in subdict:
                d[k] = subdict[k]
    return d


# dict, ast -> ast
def set_macro_vars(subst, pattern, anchor, lc):
    if isinstance(pattern, (str, unicode)):
        if pattern[0] == '$':
            return subst[pattern[1:]]
        elif pattern[0] == '@':
            return '_temp_'+str(lc)+'_'+pattern[1:]
        else:
            return pattern
    else:
        f = lambda ast: set_macro_vars(subst, ast, anchor, lc)
        args = [pattern[0]] + map(f, pattern[1:])
        if isinstance(pattern, list):
            if is_string(anchor):
                return astnode(args)
            else:
                return astnode(args, *anchor.metadata)
        else:
            return pattern


def simple_macro(args):
    pattern, subst = args

    def app(ast):
        dic = get_macro_vars(pattern, ast)
        if dic is not None:
            label_counter[0] += 1
            return set_macro_vars(dic, subst, ast, label_counter[0])
    return app


def synonym_macro(args):
    old, new = args

    def app(ast):
        if isinstance(ast, astnode) and ast.fun == old:
            return astnode([new] + ast.args[1:], *ast.metadata)
    return app


def math_macro(args):
    head, transform = args

    def app(ast):
        if isinstance(ast, astnode) and ast.fun == head:
            funargs = []
            for a in ast.args[1:]:
                if isinstance(a, astnode) or not str_is_numeric(a):
                    return
                else:
                    funargs.append(numberize(a))
            return str(transform(*funargs))
    return app


global gen_i
gen_i = 0

def gensym(name='#gen'):
    global gen_i
    gen_i += 1
    return name + str(gen_i)

def _case(ast):

    if isinstance(ast, astnode) and ast.fun == 'case':
        assert len(ast.args) == 4  # No cases, or plain wrong.
        assert ast[2].fun == 'seq' and len(ast[2]) == 1
        var, val = gensym('#casevar'), ast[1]

        def c(a):
            assert isinstance(a, astnode)
            if a.fun == 'default':
                assert len(a) == 2
                return a[1]
            elif a.fun == 'of':
                assert len(a) in [3,4]
                here = ['if', ['==', var, a[1]], a[2]]
                if len(a) == 4:
                    here.append(c(a[3]))
                return here
        return astify(c(ast[3]))

macros = \
    map(simple_macro, preparing_simple_macros) + \
    map(simple_macro, simple_macros + constants) + \
    [_getvar, _setvar, _case, _import, _inset, _str] + \
    map(synonym_macro, synonyms) + \
    map(math_macro, mathfuncs)
