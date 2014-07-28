
from io import StringIO
import utils
token, astnode = utils.token, utils.astnode

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
    if isinstance(ast, token):
        return ast.val
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
        return serialize_expr(ast.args, open, close, between, precedence[ast.fun])
    elif ast.fun == 'access':  # TODO do this fancier.
        return serialize_expr(ast.args[0]) + '[' + serialize_expr(ast.args[1]) + ']'
    elif ast.fun == 'array_lit':
        return serialize_expr(ast.args, '[', ']')
    elif ast.fun == 'str':
        assert len(ast.args) == 1
        return '"' + ast.args[0].val + '"'
    else:
        return ast.fun + serialize_expr(ast.args)


# Does elements that create their own body.
def serialize_bodied(ast, output, tabs, by_name, bodied=bodied, cases=cases):
    names = bodied[ast.fun]
    n = len(names)
    if names == 'dont':
        n = 0
    else:
        if by_name[0] == '_':
            by_name = by_name[1:]
        after_tabs(output, tabs, by_name)
        for i in range(n):
            output.write(unicode(names[i] + ' ' + serialize_expr(ast.args[i])))
        output.write(unicode(':\n'))

    if ast.fun in cases:  # Recurses.
        i = 1
        allowed, deeper = cases[ast.fun]
        for el in ast.args[n:]:
            assert el.fun in allowed
            serialize_bodied(el, output, tabs, el.fun,
                             bodied=allowed, cases=deeper)
    else:
        for el in ast.args[n:]:
            serialize(el, output, tabs + 1)


def cond_args(args):  # Makes `if` fit the paradigm.
    o = [astnode('_if', args[:2])]
    if len(args) == 3:
        if isinstance(args[2], astnode) and args[2].fun == 'if':
            o += cond_args(args[2].args)
        else:
            o.append(astnode('else', [args[2]]))
    return o


def serialize(ast, output='', tabs=0):
    if isinstance(output, (str,unicode)):
        stream = StringIO(unicode(output))
        serialize(ast, stream, tabs)
        stream.seek(0)
        return stream.read()

    if isinstance(ast, token):
        return after_tabs(output, tabs, ast.val + '\n')
    if isinstance(ast, (str, unicode)):  # NOTE: reckon it shouldnt be mixed.
        return after_tabs(output, tabs, ast + '\n')

    assert isinstance(ast, astnode)
    if ast.fun in ['outer', 'seq']:
        for el in ast.args:
            serialize(el, output, tabs)
    elif ast.fun == 'if':  # Make it fit the paradigm.
        return serialize(astnode('cond', cond_args(ast.args)), output, tabs)
    elif ast.fun in bodied:
        serialize_bodied(ast, output, tabs, ast.fun)
    else:
        after_tabs(output, tabs, serialize_expr(ast) + '\n')
