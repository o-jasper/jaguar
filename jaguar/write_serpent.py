
from io import StringIO
from utils import astnode, is_string

precedence = {
    '^': 1,
    '*': 2,
    '/': 3,
    '%': 4,
    '#/': 2,
    '#%': 2,
    '+': 3,
    '-': 3,
    '<': 4,
    '<=': 4,
    '>': 4,
    '>=': 4,
    '&': 5,
    '=': 5,
    '==': 5,
    '!=': 5,    
    'and': 6,
    '&&': 6,
    'or': 7,
    '||': 7,
    '!': 0
}


bodied = {'init':[], 'code':[],
          'while':[''],
          'cond':'dont',
          'case':[''],
          'for':['', 'in']}
cases  = {'cond':({'_if':[''], 'else':[]}, {}),
          'case':({'of':[''], 'default':[]}, {})}

the_tab = unicode('    ')


def after_tabs(stream, tabs, text):
    for i in range(tabs):
        stream.write(the_tab)
    stream.write(unicode(text))


dont_space_it = ['!', '^', '^']


def serialize_expr(ast, open='(', close=')', between=', ', precscore=-1):
    if is_string(ast):
        return ast
    elif type(ast) is list:
        if len(ast) > 0:
            ret = open + serialize_expr(ast[0])
            for el in ast[1:]:
                ret += between + serialize_expr(el, open, close, between)
            return ret + close
        else:
            return open + close
    assert isinstance(ast, astnode)

    if ast.fun in precedence:
        between = ast.fun if (ast.fun in dont_space_it) else ' ' + ast.fun + ' '
        open, close = ('', '') if precscore < precedence[ast.fun] else ('(',')')
        return serialize_expr(ast.args[1:], open, close, between, precedence[ast.fun])
    elif ast.fun == 'access':  # TODO do this fancier.
        return serialize_expr(ast[1]) + '[' + serialize_expr(ast[2]) + ']'
    elif ast.fun == 'array_lit':
        return serialize_expr(ast.args[1:], '[', ']')
    elif ast.fun == 'str':
        assert len(ast) == 2
        return '"' + ast[1] + '"'
    else:
        return ast.fun + serialize_expr(ast.args[1:])


# Does elements that create their own body.
def serialize_bodied(ast, output, tabs, by_name, bodied=bodied, cases=cases):
    names = bodied[ast.fun]
    n = len(names)
    if names == 'dont':
        n = 0
    else:
        if by_name.fun == '_':
            by_name = by_name[1:]
        after_tabs(output, tabs, by_name)
        for i in range(n):
            output.write(unicode(names[i] + ' ' + serialize_expr(ast.args[i + 1])))
        output.write(unicode(':\n'))

    if ast.fun in cases:  # Recurses.
        i = 1
        allowed, deeper = cases[ast.fun]
        for el in ast.args[n + 1:]:
            assert el.fun in allowed
            serialize_bodied(el, output, tabs, el.fun,
                             bodied=allowed, cases=deeper)
    else:
        for el in ast.args[n + 1:]:
            write_serpent(el, output, tabs + 1)


def cond_args(args):  # Makes `if` fit the paradigm.
    o = [astnode('_if', args[:2])]
    if len(args) == 3:
        if isinstance(args[2], astnode) and args[2].fun == 'if':
            o += cond_args(args[2].args)
        else:
            o.append(astnode('else', [args[2]]))
    return o


def write_serpent(ast, output='', tabs=0):
    if isinstance(output, (str,unicode)):
        stream = StringIO(unicode(output))
        write_serpent(ast, stream, tabs)
        stream.seek(0)
        return stream.read()

    if is_string(ast):
        return after_tabs(output, tabs, ast + '\n')

    if not isinstance(ast, astnode):
        raise Exception('what is', ast, type(ast))
    if ast.fun in ['outer', 'seq']:
        for el in ast.args[1:]:
            write_serpent(el, output, tabs)
    elif ast.fun == 'if':  # Make it fit the paradigm.
        return write_serpent(astnode('cond', cond_args(ast.args[1:])), output, tabs)
    elif ast.fun in bodied:
        serialize_bodied(ast, output, tabs, ast.fun)
    else:
        after_tabs(output, tabs, serialize_expr(ast) + '\n')
