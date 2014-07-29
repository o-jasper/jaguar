import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from LLL_parser import LLLParser, LLLWriter
import utils

def case(input, eq=None, equal_after=True):
    tree = utils.deastify(LLLParser(input).parse_lll())
    string = LLLWriter().write_lll(tree)
    if eq is not None and eq != string:
        raise Exception('Mismatch specified', string, eq)
    tree_after = utils.deastify((LLLParser(string).parse_lll()))[1]
    if tree != tree_after and equal_after:
        raise Exception('mismatch before/after', tree, tree_after)

#case('q(a b [a] 3 [ [b]] 432)')

case('a (thing) b')
case('a "string" b')

case('@@a @@ b @@(calldataload 0) @@ (calldataload 1)')

case(""" {
  [0] "Bank"
  (call 0x929b11b8eeea00966e873a241d4b67f7540d1f38 0 0 0 4 0 0)
  }""")

# Not equal after because case get bludgeoned.
case('(SEQ a b c)', '(top {a b c})', False)
