#!/usr/bin/python

import random


from jaguar import parser, rewriter, compiler, LLL_parser, utils


def bijection_test_LLLParser(ast2):
    text2 = repr(ast2)
    i = 0
    n = random.randrange(4)  # No comments yet.
    while i >= 0 and n > 0:
        i = text2.find('\n', i)
        n -= 1
    if i > 0:
        text2 = text2[:i] + ';blablabla\n' + text2[i+1:]
    print(text2)

    ast3  = LLL_parser.LLLParser(text2, do_comments=False).parse_lll()
    if utils.deastify(ast3[1]) != utils.deastify(ast2):
        print("BUG: Parsing output again gave different result!")
        print(ast2)
        print(ast3)
        print("")


def test_on_text(text):
    print text
    ast = parser.parse(text)
    print "AST:", ast
    print ""
    ast2 = rewriter.rewrite_to_lll(ast)
    print "LLL:", ast2
    print ""
    bijection_test_LLLParser(ast2)

    print "Analysis: ", rewriter.analyze(ast)
    print ""
    aevm = compiler.compile_lll(ast2)
    print "AEVM:", ' '.join([str(x) for x in aevm])
    print ""
    code = compiler.assemble(aevm)
    print "Output:", code.encode('hex')


def test_on_file(file):
    t = open(file).readlines()
    i = 0
    while True:
        o = []
        while i < len(t) and (not len(t[i]) or t[i][0] != '='):
            o.append(t[i])
            i += 1
        i += 1
        print '================='
        text = '\n'.join(o).replace('\n\n', '\n')
        test_on_text(text)
        if i >= len(t):
            break

test_on_file('tests.txt')

rewriter.base_dir = 'examples/Just_code/'
# TODO point the commandline tool at it from the makefile instead.
for f in ['examples/Just_code/mul2.se',
          'examples/NameReg/namecoin.se',
          'examples/Just_code/returnten.se',
          'examples/SubCurrency/subcurrency.se'
          ]:
    test_on_file(f)
