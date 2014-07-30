
# Visualizing based on pydot and the AST tree/LLL

### Control flow graph
The `GraphCode().control_flow` is what i wanted to make, the other one was created
because it is relatively easy.

Note that.

1. If it leads to a `return` or `stop` computation ends there.
2. Otherwise trace back and follow consecutive body lines.

#### Install
If it isnt there already, add `~/.bin/` and then add in `~/bashrc`
`PATH=~/.bin/:$PATH`, now all executable programs in that directory are accesible.

Then `cd ~/.bin/; ln -s path/to/serpent/visualize/bin/code-visualize.py` now
once the current `~/.bashrc` is in use, you can directly call the program.

`visualize/bin/code_visualize.py` is intended to run as program. It requires the
presence of `python2`.

Once it works, to see what it can do use
`cd visualize/examples/; make show_off.html; $BROWSER show_off.html`.

### Straight graph
Note that the `GraphCode().straight` visualization, loses a lot of information.
Because it doesnt show the order of the arguments.
[Unlike EtherScripter](http://etherscripter.com/), which visualizes it better
and is editable.

Also have trouble making nodes with the same names not be the same one.
(You'd say that is the default)

Looking to make something that visualizes the control flow, rather than the
AST tree. That would actually be useful.

## TODO
* Graphically indicate `return`, `stop`.

* Handle comments.

* More/nicer themes.. Particularly an Ethereum theme would be nice.(difficult..)

* Further out:
  + More direct control of positioning?
  + Make it workable with other presentation?

* Really closer to the parser/write/ast stuff.
  + infix-like printing (Serpent-like) i.e `a + b` instead of `(+ a b)`
  + Identify identical paths.

* Tricky:
  + Decorate `if`, `when`, `unless`, `for`? (Apparently no html)
  + Edges back to body. Tricky, and probably not very enlightening.
  
