#!/usr/bin/python2

import os.path
import sys
import io

fromdir = os.path.dirname(__file__)
sys.path.append(os.path.join(fromdir, '..'))
sys.path.append(os.path.join(fromdir, '../../serpent/'))

import argparse

parser = argparse.ArgumentParser(description="""Visualize code with graphviz.
Control flow available.""")
parser.add_argument('input',  help='Input LLL file.')
parser.add_argument('output', help='Output file.')
parser.add_argument('--prog', default='dot',
                    help='Graphviz program to use dot|twopi|neato|circo|fdp.')
parser.add_argument('--format', default=None,
                    help='Output format, defaults based on output file.')
parser.add_argument('--which', default='cf',
                    help='What kind, sg|cf for straight graph/control flow.')
parser.add_argument('--comments', default='no',
                    help='Link comments aswel')
parser.add_argument('--text', default='serpent',
                    help='How to write down code in nodes, serpent|lll')
parser.add_argument('--symbols', default='yes',
                    help='whether to turn >= etcetera into symbols.')
parser.add_argument('--theme', default='basic',
                    help='name of theme to use.')
parser.add_argument('--uniqify', default='yes',
                    help='Whether to force all nodes to be unique, default yes. No _does not make sense for control flow!')
args = parser.parse_args()

import pydot

from visualize import GraphCode
from LLL_parser import LLLParser, LLLWriter

import utils
import write_serpent  #serialize.


def _write_fun(stream, ast):
    internal = io.StringIO()
    if args.text =='serpent':
        write_serpent.serialize(utils.nodeify(ast), internal)
    else:
        LLLWriter().write_lll_stream(internal, ast)
    internal.seek(0)
    string = internal.read()
    if args.symbols == 'yes':
        string = string.replace('<=', '&le;').replace('>=', '&ge;')
        string = string.replace('!=', '&ne;')

    if string != '':
        stream.write(string[:-1] if string[-1]=='\n' else string)


def graph_file(which, fr, to, prog='dot', format=None,
               comment_name=None, text='serpent'):
    graph = pydot.Dot('from-tree', graph_type='digraph')
    graph.set_fontname('Times-Bold')
    gc = GraphCode(graph=graph, write_fun=_write_fun, theme=args.theme,
                   uniqify=args.uniqify.lower() in ['yes', 'true'])

    tree = LLLParser(comment_name=comment_name).parse_lll_file(fr)
    if which in ['sg']:
        g = gc.straight(['root'] + tree)
    elif which in ['cf']:
        g = gc.control_flow(tree)

    if format is None:
        format = to[-3:]
    g.write(to, format=format, prog=prog)


graph_file(args.which, args.input, args.output, args.prog,
           args.format, 'comment' if args.comments == 'yes' else None,
           text=args.text)
