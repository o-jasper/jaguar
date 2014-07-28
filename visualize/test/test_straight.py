import os.path
import sys
from random import random

fromdir = os.path.dirname(__file__)
sys.path.append(os.path.join(fromdir, '..'))
sys.path.append(os.path.join(fromdir, '../../serpent'))

from visualize import GraphCode

# Note.. s_expr_parser test uses the same code..
def gen_tree(p, n, d):
    out = [str(random())]
    for i in range(n):
        if random() < p and d > 0:
            out.append(gen_tree(p, n, d - 1))
        else:
            out.append(str(random()))
    return out

g = GraphCode().straight(gen_tree(0.2, 2, 2))

g.write(fromdir + 'straight.svg', format='svg')
