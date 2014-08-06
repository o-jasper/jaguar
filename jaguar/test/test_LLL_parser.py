import os.path, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from LLL_parser import LLLParser, LLLWriter
import utils

def in_there(ast, funs, vars):
    if isinstance(ast, utils.astnode):
        if ast.fun in funs:
            return ast.fun
        for el in ast.args[1:]:
            got = in_there(el, funs,vars)
            if got:
                return got, ast
    else:
        return ast if (ast in vars) else None

def case(input, eq=None, equal_after=True):
    tree = LLLParser(input).parse_lll()
    print('t', tree)
    string = LLLWriter().write_lll(tree)
    if eq is not None and eq != string:
        print('BUG: Mismatch specified', string, eq)
    tree_after = LLLParser(string).parse_lll()
    if utils.deastify(tree) != utils.deastify(tree_after) and equal_after:
        print('BUG: mismatch before/after', tree, tree_after)

    found = in_there(tree_after, ['aref'], [])
    if found:
        print('BUG: Something in there that shouldnt be;', found)

case('q(a b [a] 3 [ [b]] 432)')

case('a (thing) b')
case('a "string" b')

case('@@a @@ b @@(calldataload 0) @@ (calldataload 1)')

case(""" {
  [0] "Bank"
  (call 0x929b11b8eeea00966e873a241d4b67f7540d1f38 0 0 0 4 0 0)
  }""")

## Not equal after because case get bludgeoned.
case('(SEQ a b c)', '{\na\n  b\n  c}\n\n', False)

case("""(when @@(caller) [[@@(caller)]] 0)""")
case("[[@@ska]] skoe")

print("RAN: " + str(os.path.basename(__file__)))
