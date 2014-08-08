from parser import parse
from utils import astnode, astify, is_string, str_is_numeric, numberize

# Placeholders for type calculation.
def calc_type(x):
    return x

def type_of(x):
    return 'slot'

def size_of(x):
    return {'slot':32}[x]

# Use $xxx to indicate parts of the code that can pattern-match anything.
# Use '@xxx' to generate variables on the fly.

# Note:
#  * mload, sload, sstore, mstore refer to memory operations.
#  * mget, sget, sset and mset refer to those memory operations,
#    but with index finding inbetween.
# Tuples for knowing locations of variables and their types.

# TODO looks ugly, just read it in.

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
    [ # Types?!
        ['access', '$var', '$ind'],
        ['MLOAD', ['ADD', '$var', ['MUL', '32', '$ind']]]
    ],
    [ # TODO/note: maybe this should storah be relegated to sstore, as you're
      # doing it manually.
        ['set', ['access', 'contract.storage', '$ind'], '$val'],
        ['SSTORE', '$ind', '$val']
    ],
    [
        ['set', ['access', '$var', '$ind'], '$val'],
        ['arrset', '$var', '$ind', '$val']
    ],
    [ # Types?!
        ['arrset', '$var', '$ind', '$val'],
        ['MSTORE', ['ADD', '$var', ['MUL', '32', '$ind']], '$val']
    ],
    [ # * 
        ['getch', '$var', '$ind'],
        ['MOD', ['MLOAD', ['ADD', '$var', '$ind']], '256']
    ],
    [ # *
        ['setch', '$var', '$ind', '$val'],
        ['MSTORE8', ['ADD', '$var', '$ind'], '$val']
    ],
    [
        ['send', '$to', '$value'],
        ['CALL', ['SUB', ['GAS'], 'gascosts.send_ether'],
                 '$to', '$value', '0', '0', '0', '0']
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
    [   ['!=', '$x', '$y'],
        ['NOT', ['=', '$x', '$y']]
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
            ['mget', '@2']]
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
            ['mget', '@1']]
    ],
    [
        ['call', '$f', '$inp', '$inpsz'],
        ['seq',
            ['mset', '@1', '$inpsz'],
            ['msg',
                ['SUB', ['GAS'], ['ADD', '25', ['mget', '@1']]],
                '$f', '0', '$inp', ['mget', '@1']]]
    ],
    [
        ['msg', '$gas', '$to', '$val', '$inp', '$inpsz', '$outsz'],
        ['seq',
            ['mset', '@1', ['MUL', '32', '$outsz']],
            ['mset', '@2', ['alloc', ['mget', '@1']]],
            ['POP',
                ['CALL', '$gas', '$to', '$val',
                 '$inp', ['MUL', '32', '$inpsz'], '@2', ['mget', '@1']]],
            ['mget', '@2']]
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
    ],

    # Setting variables.
    [['set', '$var', '$to'], ['mset', '$var', '$to']]
    
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
    ['stop',             ['STOP']]
]

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

    ['gascosts.send_ether', '25']
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

# Probably: the macro decides to take over how the internals are rewritten.
macroexpand_stopper = []

# Apply all rewrite rules
def rewrite(ast):
    while True:
        ast2 = None
        for macro in macros:
            ast2 = macro(ast2 or ast) or ast2
        if not ast2:  # None of them changed anything.
            break
        ast = ast2
    if is_string(ast) or ast.fun in macroexpand_stopper:
        return ast
    else:  # Macroexpand all the arguments. #(TODO except something?)
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


# Figures out if a ast matches a pattern, and what the parameters are, if so.
def get_macro_vars(pattern, ast):
    d = {}
    if isinstance(pattern, list):
        if not isinstance(ast, astnode) or len(ast) != len(pattern):
            return None
        for mitem, astitem in zip(pattern, ast.args):
            subdict = get_macro_vars(mitem, astitem)
            if subdict is None:
                return None
            for k in subdict:
                d[k] = subdict[k]
    else:  
        if pattern[0] == '$':  # TODO handle $var... (need to have ast at list level)
            d[pattern[1:]] = ast
        elif isinstance(ast, astnode) or pattern != ast:
            return None
    return d

# Symbol generator for temporary variables. (otherwise you get abstraction leaks.)
gensym_counter = 0

def gensym(name='_gen_', post=''):
    global gensym_counter
    gensym_counter += 1
    return name + str(gensym_counter) + ('' if (post == '') else '_' + post)


# Sets the parameters in a pattern.
def set_macro_vars(subst, pattern, anchor):
    if isinstance(pattern, (str, unicode)):
        if pattern[0] == '$':
            return subst[pattern[1:]]
        elif pattern[0] == '@':  # Basically `gensym(..)` without counting.
            return '_smv_' + str(gensym_counter) + pattern[1:]
        else:
            return pattern
    else:
        f = lambda ast: set_macro_vars(subst, ast, anchor)
        args = [pattern[0]] + map(f, pattern[1:])
        if isinstance(pattern, list):
            if is_string(anchor):
                return astnode(args)
            else:
                return astnode(args, *anchor.metadata)
        else:
            return pattern

# If pattern, set by second pattern.
def simple_macro(args):
    pattern, subst = args

    def app(ast):
        dic = get_macro_vars(pattern, ast)
        if dic is not None:
            global gensym_counter
            gensym_counter += 1  # Counts instead of the function itself continuously.
            return set_macro_vars(dic, subst, ast)
    return app

# If  pattern, call function.
def on_pattern_macro(args):
    pattern, fun = args

    def app(ast):
        dic = get_macro_vars(pattern, ast)
        if dic is not None:
            return fun(ast, *dic)
    return app

# Assert a pattern shouldnt be in there, returning a message.
def assert_nonexistance(args):
    pattern, msg = args
    
    def app(ast):
        dic = get_macro_vars(pattern, ast)
        if dic is not None:  # TODO better message.
            raise Exception('may not exist:', ast, msg)
    return app

# Straight out replacement doing nothing.
def synonym_macro(args):
    old, new = args

    def app(ast):
        if isinstance(ast, astnode) and ast.fun == old:
            return astnode([new] + ast.args[1:], *ast.metadata)
    return app

# Simplification with plain numbers.
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

base_dir = ''  # Directory to import from.

def file_ast(filename):
    global base_dir
    return parse(open(base_dir + filename).read(), filename)


# If it is a plain string, not a constant, and it is from serpent, it is an mload.
def _se_getvar(ast):
    assert ast != ''
    if is_string(ast) and not ast[0] in ['\'', '"'] and not str_is_numeric(ast) and \
       ast not in map(lambda x: x[0], constants):
        return astnode(['mget', ast])

#def _se_setvar(ast, var, to):
#    if is_string(ast[1]):  # Otherwise it could be other things like contract.storage[11]
#        return astnode(['mset', ast[1], ast[2]], *ast.metadata)


class VarInfo:
    def __init__(self, index, tp, *metadata):
        self.index, self.tp = index, tp
        self.metadata = metadata

    @property
    def info(self):

class MemTracker:
    """Tracks where to put variables in memory"""
    def __init__(self, getword, setword):
        self.getword = getword
        self.setword = setword
        self.vdict = {}

        self.top_i = 0
        self.free = []

    def mget(self, ast, var):
        if isinstance(var, astnode):
            raise Exception('Cannot set a variable that is not a symbol.', var)
        if var not in self.vdict:
            raise Exception('Variable not declared before use:', var)
        index, tp, sz = self.vdict[var].info
        i, j = index%256, index%256 + sz        
        result = [self.getword, index/8]  # Best case is entire slot.
        if j > 256:
            raise Exception('BUG: larger than slot!', info, ast)

        if i != 0:
            result = ['DIV', result, 2**i]  # Shift out beginning.
        if index + sz != 256:
            result = ['MOD', result, 2**sz]  # Mask to select what we want.
        return result

    # Create an expression to set something.
    def set_expression(self, index, sz, to):
        i = index % 256
        j = i + sz
        if j > 256:
            raise Exception('BUG: larger than slot!', info, ast)
        # Modify `to` to a statement that mashes to correct type.
        # Can fail if types dont fit.
        to = mash_type(tp, to)
        if size_of(tp) == 256:  # Its the whole thing.(cheapest, hence preferable for mem)
            return [self.setword, index/8, to]

        get = [self.getword, index/8]  # Overhead is one getting, AND and OR.(bitwise)
        return [self.setword, index/8, ['OR', ['AND', 2**j - 1 - 2**i - 1, get], to]]
    
        # Alternatives: (neither seems faster, second maybe equal gas)
        #if i == 0:  # Starts at beginning. (sz == j) Strip by deleting and adding again.
        #    return [self.setword, index/256, ['ADD', ['MUL', ['DIV', get, 2**j], 2**j], to]]
        #
        #if j == 256:  # Ends at end
        #    return [self.setword, index/256, ['OR', ['MOD', get, 2**i], to]

    def next_top_i(self):
        return self.top_i - self.top_i % 256 + 256
    
    def finish_slot(self, reserve):
        self.open_spots.append([self.top_i, self.next_top_i() - self.top_i])
        reserve_i = self.next_top_i()
        self.top_i = reserve_i + reserve
        return reserve_i
    
    def mset(self, ast, var, to, vdict=memory_vars, prefer_whole=True)
        if var in vdict:  # Already exists.(ignores preference)
            index, tp, sz = self.vdict[var].info
            return self.set_expression(index, sz, to)
        else: # Have to create it.
            to = type_calc(to)
            take_sz = (256 if prefer_whole else size_of(type_of(to)))
                for i in range(len(self.open_spots)):
                    el = self.open_spots[i]
                    assert (el[0] + el[1])%256 == 0
                    if el[1] == 256:  # Is size of slot.
                        self.vdict[var] = VarInfo(el[0], ['whole_slot', type_of(to)], *ast.metadata)
                        self.open_spots = self.open_spots[:i-1] + self.open_spots[i:]
                        #(not expression because whole thing)
                        return [self.setword, el[0]/8, to]
                reserve_i = self.top_i
                if self.top_i % 256 != 0:  # Make chunk and keep reserve of 256 bits there.
                    reserve_i = self.finish_slot(256)
                return [self.setword, reserve_i/8, to]
            else:
                for i in range(len(self.open_spots)):
                    el = self.open_spots[i]
                    assert (el[0] + el[1])%256 == 0
                    if sz < el[1]:  # If fits.
                        ret = self.set_expression(el[0], sz, to)
                        self.vdict[var] = VarInfo(el[0], type_of(to), *ast.metadata)
                        if sz == el[1]:
                            self.open_spots = self.open_spots[:i-1] + self.open_spots[i:]
                        else:
                            el[0] += sz
                            el[1] -= sz
                        return ret
                reserve_i = self.top_i
                if self.top_i + sz > self.next_top_i():
                    reserve_i = self.finish_slot(sz)
                return self.set_expression(self.top_i, sz, to)

def _mem_reserve(ast, n):
    global memory_i
    memory_i += n
    return None
def _mem_reserve(ast, n):
    global memory_i
    memory_i += n
    return None

pattern_macros = [
    [['import', '$what'],     lambda ast, what: astnode(['code', preprocess(file_ast(what))],
                                                       *ast.metadata)],
    [['inset', '$what'],      lambda ast, what: file_ast(what)],
    [['str', '$string'],      lambda ast, what: '"' + what + '"'],

    [['mget', '$var'],        _mget],
    [['mset', '$var', '$to'], _mset],
#    ['mem_i',                    lambda ast: memory_i],
#    [['mem_reserve', '$amount'], _mem_reserve],

    [['sget', '$var'],        lambda ast, var: _mget(ast, var, storage_vars, 'sload')],
#    [['sset', '$var', '$to'], _sset],
#    ['storage_i',                     lambda ast: storage_i],
#    [['storage_reserve', '$amount'],  _storage_reserve]
    ]

disallowed_pattern = []  # TODO

def _case(ast):
    if isinstance(ast, astnode) and ast.fun == 'case':
        assert len(ast.args) == 4  # No cases, or plain wrong.
        assert ast[2].fun == 'seq' and len(ast[2]) == 1
        var, val = gensym('_case_'), ast[1]

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
    [_getvar, _se_getvar, _case] + \
    map(on_pattern_macro, pattern_macros) + \
    map(synonym_macro, synonyms) + \
    map(math_macro, mathfuncs) + \
    map(assert_nonexistance, disallowed_pattern)
