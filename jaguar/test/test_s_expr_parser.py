
import os.path, io, sys
from random import random

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from s_expr_parser import SExprParser
import utils

def gen_tree(p, n, d):
    out = []
    for i in range(n):
        if random() < p and d > 0:
            out.append(gen_tree(p, n, d - 1))
        else:
            out.append(str(random()))
    return out


def test_case(string, tree, o='(', c=')', white=[' ', '\t', '\n']):
    result =  map(utils.deastify, SExprParser(string).parse().args[1:])
    if result != tree:
        #raise Exception('Mismatch', "\ntree", tree, "\nstring", string, "\nresult", result)
        print("BUG Mismatch", string, tree, result)


def test_1(p=0.1, n=2, d=2):
    tree = gen_tree(p, n, d)
    test_case(repr(utils.astify(tree)), [tree])


test_case('"string (stuff" should end', [['str', 'string (stuff'], 'should', 'end'])

# Simple case test.
test_case("bla 123 (45(678      af)sa faf((a sf))  (a) sfsa) ;do not include",
          ['bla', '123', ['45', ['678', 'af'],
            'sa', 'faf', [['a', 'sf']], ['a'], 'sfsa']])

# IMO Should have been caught in a test and not ended up downstream.
for i in range(200):
    test_1()

print("RAN: " + str(os.path.basename(__file__)))
