import re

import utils
from utils import token, astnode, astify

import rewriter

var_types = {}

fun_types = {}
fun_plain_types = {}  # Just plainly says an output that is always so.

fun_defines = {}


def fit_type_str(tp, fr_tp):
    if tp[:3] == 'int':
        assert (fr_tp[:3] == 'int'  and int(tp[3:]) >= int(fr_tp[3:]) or \
                fr_tp[:4] == 'uint' and int(tp[3:]) > int(fr_tp[3:]))
    elif tp[:4] == 'uint':
        assert fr_tp[:4] == 'uint' and int(tp[3:]) >= int(fr_tp[3:])
    elif tp[:4] == 'float':
        assert (fr_tp[:4] == 'float' and int(tp[3:]) >= int(fr_tp[3:]) or \
                fr_tp[:3] == 'int' or fr_tp[:3] == 'uint')
    return fr_tp + '_to_' + tp


def fit_type(tp, fr_tp, ast):
    if tp == fr_tp:
        return ast
    elif isinstance(tp, list):
        if tp[0] == 'tuple' and fr_tp == 'tuple':
            # Tuples converted into each other must have same length.
            assert len(tp) == len(fr)
            ret, var = ['tuple'], rewriter2.gensym()
            for i in range(len(tp) - 1):
                ret.append(fit_type_str(tp[i + 1], fr_tp[i+1]))
            return astify(['to_tuple', ret, ast])
        elif tp[0] == 'list' and fr_tp == 'list':
            return astify(['to_list', fit_type_str(tp[1]), ast])
    else:
        return astnode(fit_type_str(tp, fr, to), [ast])
            

def convert_type(name):
    if not(isinstance(name, (str, unicode)) and name.find('_to_') >= 0):
        raise Exception(name)
    return name[name.find('_to_') + 4:]

# Gives a type a-priory given an expression, will not try hard.
# Using type_of(calc_type(ast)) will try actually figure something out.
def type_of(ast):
    if isinstance(ast, astnode):
        if ast.fun == 'the':
            return ast.args[0]
        elif ast.fun.find('_to_') > 0:  # These are build-in.
            return convert_type(ast.fun)
        elif ast.fun == 'to_tuple':  # Conversion.
            ret = ['tuple']
            for el in ast.args[0].args:
                ret.append(convert_type(el.val))
            return ret
        elif ast.fun == 'to_list':
            return ['list', convert_type(ast.args[0].val)]
        else:
            return 'any'
    else:
        b = ast.val
        if re.match('^[0-9\-]*$', b):
            return 'int64'
        elif b[:2] == '0x':
            return 'uint64' if len(b) < 18 else 'uint256'
        elif re.match('^[0-9\-\.]*$', b):
            return 'float64'
        elif b[0] in ["'", '"'] and b[-1] in ["'", '"'] and b[0] == b[-1]:
            return ['string', len(b) - 2]
        else:
            assert b in var_types  # The variable is not set yet!

            return var_types[b]


def calc_type(ast):
    if isinstance(ast, astnode):
        if ast.fun == 'set':
            var = ast.args[0]
            if isinstance(var, token):
                to = calc_type(ast.args[1])
                tp = type_of(to)
                if var.val in var_types:  # Already exist, must fit in.
                    return astnode('set', [var, fit_type(var_types[var.val], tp, to)])
                else:
                    var_types[var.val] = tp
                    return astnode('set', [var, to])
        else:
            input = map(calc_type, ast.args)
            if ast.fun in fun_types:  # Use the function to calculate the type.
                return astify(['the', fun_types[ast.fun](map(type_of, input)),
                               astnode(ast.fun, input)])
            elif ast.fun in fun_defines:
                print 'TODO the variant thing.'
            else:
                return astnode(ast.fun, input)
    else:
        return ast


fun_types['address'] = lambda types: 'address'


def two_to_n(bin_function):
    def fun(types):
        tp = types[-1]
        for i in range(len(types)-1):
            tp = bin_function(types[i], tp)
        return tp
    return fun


def max_type(a, b):
    if a[:4] == 'uint' and b[:4] == 'uint':
        return 'uint' + str(max(int(a[4:]), int(b[4:])))
    elif (a[:3] == 'int' and (b[:3] == 'int' or b[:4] == 'uint') or \
          b[:3] == 'int' and (a[:3] == 'int' or a[:4] == 'uint')):
        return 'int' + str(max(int(a[3:]), int(b[3:])))
    elif a[:4] == 'float' and b[:4] == 'float':
        return 'float' + str(max(int(a[5:]), int(b[5:])))
    elif a[:4] == 'float':
        return a
    elif b[:4] == 'float':
        return b


def num_fun_type(a,b):
    if isinstance(a, str):
        assert isinstance(b, str)
        return max_type(a, b)
    elif a[0] == 'tuple' and isinstance(b, list) and b[0] == 'tuple':
        assert len(a) == len(b)
        return ['tuple'] + map(fun, a[1:], b[1:])
    elif isinstance(b, list) and b[0] == 'tuple':
        return ['tuple'] + map(lambda x: fun(a, x), b)


for el in ['+', '-', '*', '/']:
    fun_types[el] = two_to_n(num_fun_type)


#bitlens = [256, 64, 32, 16, 8]
#for i in range(len(bitlens)):
#    for j in range(i):
#        for kind in ['int', 'uint', 'float']:
#            if kind == 'float' and not (i in [32, 64] and j in [32, 64]):
#                continue
#            name = kind + str(bitlens[i]) + '_to_' + kind + str(bitlens[j])
#            fun_plain_types[name] = lambda types: kind + str(bitlens[j])
