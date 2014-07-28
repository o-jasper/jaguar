import os.path
import sys
from random import random

fromdir = os.path.dirname(__file__)
sys.path.append(os.path.join(fromdir, '..'))
sys.path.append(os.path.join(fromdir, '../../serpent'))

from visualize import GraphCode
from LLL_parser import LLLParser

inp =  """ seq 1 2 3
(when ska return 2)
ble
(if stuff consequence (if recurse {a b} c))
(for i (< i 30) (+ i 1) do stuff)
(return (lll just finally))"""

# WARN/TODO easy of forgetting comma is bad.
g = GraphCode().control_flow(LLLParser().parse_lll(inp))

g.write(fromdir + 'control_flow.svg', format='svg')
