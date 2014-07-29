
import pydot
from random import random

import io
from python_2_3_compat import to_str, is_str

from LLL_parser import LLLWriter
from utils import astnode, is_string

themes = {'basic' :
           {'default'      : [('fontname', 'Arial')],
            'body'         : [('shape', 'box')],
            'body_edge'    : [('penwidth', '2.0')],
            'true'         : [('label','true')],
            'false'        : [('label','false')],
            'for_edge'     : [('label','loop'), ('back_too', 'plain_edge')],
            'lll'          : [('label',' LLL')],
            'comment'      : [],
            'debug'        : [('label','bugifshown')]},
          'cut_corners' :
           {'pass_on'  : 'basic',
            'cut_tops' : ['if', 'when', 'else', 'for'],
            'if'       : [('bgcolor', 'lightgrey'), ('style', 'filled')],
            'when'     : [('derive', 'if')],
            'unless'   : [('derive', 'if')],
            'for'      : [('derive', 'if')]
            }}
            

class GraphCode:
    
    def __init__(self, graph=None, fr=None, uniqify=True, theme='basic', attrs=None,
                 write_fun=None, lllwriter=LLLWriter()):
        self.graph = graph or pydot.Dot('from-tree', graph_type='digraph')
        self.fr = fr
        self.uniqify = uniqify
        self.budders = {'lll':"_LLL_", 'comment':""}

        self.attrs = attrs or themes[theme]
        self.calculated_attrs = {}
        self.write_fun = write_fun or lllwriter.write_lll_stream
        
        self.i = 0

    def cf_expr_str(self, seq):
        if is_string(seq):
            return seq
        if not isinstance(seq, (list, astnode)) or len(seq) == 0:
            raise Exception(seq, type(seq))
        if 'cut_tops' in self.attrs and seq[0] in self.attrs['cut_tops']:
            seq = seq[1:]
            assert len(seq) > 0
        stream = io.StringIO()
        self.write_fun(stream, seq[0])
        for el in seq[1:]:  # Here for the newlines.
            stream.write(to_str('\n'))
            self.write_fun(stream, el)
        stream.seek(0)  # Dont forget to read back!
        return stream.read()

    # Checks if parts of expressions need more nodes.
    def control_flow_budding(self, ast):
        line_i = -1
        if isinstance(ast, astnode):
            line_i = ast.line_i
            ast = ast.args
        if isinstance(ast, list):
            if len(ast) == 0:
                return '()', []

            if is_str(ast[0]) and str(ast[0].lower()) in self.budders:
                name = ast[0].lower()
                use_str = self.budders[name]
                return use_str, [[name] + ast[1:]]
            else:
                ret_alt, ret_buds = [], []
                for el in ast:
                    alt, buds = self.control_flow_budding(el)
                    if alt not in ['seq', '']:
                        ret_alt.append(alt)
                    ret_buds = ret_buds + buds
                if len(ret_alt) == 0:
                    ret_alt = ['_seq_']
                return ret_alt, ret_buds
        else:
            return ast, []

    def get_attrs(self, of, attrs=None):
        attrs = attrs or self.attrs
        if of not in attrs:
            if 'pass_on' in attrs:
                return self.get_attrs(of, themes[attrs['pass_on']])
            else:
                return dict(attrs['default'])
        elif of in self.calculated_attrs:
            return dict(self.calculated_attrs[of])
        else:
            val = dict(attrs[of])
            for sub in (val['derive'].split(',') if 'derive' in val else []) + ['default']:
                cur = attrs
                while sub not in cur:
                    cur = themes[cur['pass_on']]
                for el in cur[sub]:
                    if el[0] not in val:
                        val[el[0]] = el[1]
            self.calculated_attrs[of] = val
            return dict(val)

    def add_node(self, added, which='default', uniqify=None):
        if uniqify is None:
            uniqify = self.uniqify

        if is_str(added):
            self.i += 1
            node = pydot.Node(str(self.i) if uniqify else added)
            node.obj_dict['attributes'] = self.get_attrs(which)
            # (Python3 needs issubclass) **
            assert isinstance(node.obj_dict['attributes'], dict)
            node.set_label(added)
            added = node

        self.graph.add_node(added)
        return added

    def add_edge(self, fr, to, edge_which='default_edge'):
        edge = pydot.Edge(fr, to)
        attrs = self.get_attrs(edge_which)
        assert isinstance(attrs, dict)  # **
        edge.obj_dict['attributes'] = attrs
        self.graph.add_edge(edge)
        if 'back_too' in attrs:  # Option to make a backward edge.
            back = pydot.Edge(to, fr)
            back.obj_dict['attributes'] = self.get_attrs(attrs['back_too'])
            self.graph.add_edge(back)

    def cf_add_node(self, added, fr, which, edge_which):
        buds = []
        if isinstance(added, astnode):
            added = added.args
        if isinstance(added, list):
            added, buds = self.control_flow_budding(added)
            added = self.cf_expr_str(added)

        added = self.add_node(added, which)

        if fr is not None:
            self.add_edge(fr, added, edge_which)

        for bud in buds:
#            if len(bud) < 2:
 #               raise Exception(bud)
            self.control_flow(bud[1:], added, bud[0])
        return added

    def control_flow(self, ast, fr=None, fr_which='body_edge'):
        fr = fr or self.fr
    
        i, j = 0, 0
        while i < len(ast):
    
            el = ast[i]
            if isinstance(el, astnode):
                if len(el) == 0:
                    raise Exception('Zero length entry?', i, ast)
    
                pre_n = {'when' : (2, 'true'),  'unless' : (2, 'false'),
                          'for' : (4, 'for_edge'), 'seq' : (1,None),
                          'lll' : (1, 'lll'),       'if' : (None,None)}
                name = el[0].lower()
                if name in pre_n:
                    if j < i-1:  # Collect stuff in between.
                        fr = self.cf_add_node(ast[j:i-1], fr, 'body', fr_which)
                        fr_which = 'body_edge'
                    j = i + 1

                    if name == 'if':
                        if len(el) not in [4,5]:
                            raise Exception(len(el), el)
                        assert len(el) in [4,5]  # The condition.
                        fr = self.cf_add_node(el[:2], fr, name, fr_which)
                        self.control_flow([el[2]], fr, 'true')
                        if len(el) == 4:
                            self.control_flow([el[3]], fr, 'false')
                    else:
                        n, which = pre_n[name]
                        if len(el) < n:
                            raise Exception('Not enough arguments', len(el), el)

                        if name not in ['seq']:
                            fr = self.cf_add_node(el[:n], fr, name, fr_which)
                        else:
                            which = fr_which
                        self.control_flow(el[n:], fr, which)
                    fr_which = 'body_edge'
            i += 1
        if j < i:
            self.cf_add_node(ast[j:], fr, 'body', fr_which)
        return self.graph

# Note: all the 'straight graph' stuff is a slap-on.
    def sg_add_node(self, added, fr=None, uniqify=None):
        node = self.add_node(added, uniqify=uniqify)
        if fr is not None:
            self.add_edge(fr, node)
        return node

    # Graph straight from tree.
    def straight(self, tree, fr=None):
        fr = fr or self.fr

        if isinstance(tree, astnode):
            if len(tree) > 0:
                if not is_string(tree[0]):
                    raise Exception('First argument not name', tree, type(tree[0]))
                root = self.sg_add_node(tree[0], fr)
        
                for el in tree[1:]:
                    self.straight(el, root)
            else:
                self.sg_add_node('()', fr)
        elif is_string(tree):
            self.sg_add_node(tree, fr)
        else:
            raise Exception(tree, type(tree))
        return self.graph
