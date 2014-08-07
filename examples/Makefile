
default: sg cf

clean:
	rm */pic/*.png


# Visualization stuff.
jagviz: ../bin/jaguar_visualize ../jaguar_visualize/visualize.py jag_src

jag: ../bin/jaguar jag_src  # Jaguar itself.

# Sources to it.
jag_src: ../jaguar/compiler.py  ../jaguar/opcodes.py     ../jaguar/s_expr_parser.py \
	 ../jaguar/write_serpent.py   ../jaguar/__init__.py    ../jaguar/parser.py   \
	 ../jaguar/type_calculator.py ../jaguar/LLL_parser.py  ../jaguar/rewriter.py \
	 ../jaguar/utils.py

# Files visualizing it.
%.sg.png: %.lll jagviz
	../bin/jaguar_visualize $< $@ --which sg

%.sg.png: %.lll jagviz
	../bin/jaguar_visualize $< $@ --which sg

%.cf.svg: %.lll jagviz
	../bin/jaguar_visualize $< $@ --which cf

%.cf.png: %.lll jagviz
	../bin/jaguar_visualize $< $@ --which cf

sg: Bank/Bank.sg.png Key_Value/kv.sg.png NameReg/NameReg.sg.png Splitter/Splitter.sg.png \
	SubCurrency/SubCurrency.sg.png

cf: Bank/Bank.cf.png Key_Value/kv.cf.png NameReg/NameReg.cf.png Splitter/Splitter.cf.png \
	SubCurrency/SubCurrency.cf.png

allviz: sg cf

# Tests,

%.lll.test: % jag
	../bin/jaguar $< lll --check yes | ../remember_test.sh $@ ; touch $@

%.exp.lll.test: % jag
	../bin/jaguar $< exp.lll  --check yes | ../remember_test.sh $@ ; touch $@

%.easm.test: % jag
	../bin/jaguar $< easm --check yes | ../remember_test.sh $@ ; touch $@

%.ebc.test: % jag
	../bin/jaguar $< ebc --check yes | ../remember_test.sh $@ ; touch $@

lll.test:
	ls */*.se */*.lll | sh alldo.sh make .lll.test

exp.lll.test:  #.se ones dont succeed yet.
	ls */*.lll | sh alldo.sh make .exp.lll.test

easm.test:
	ls */*.lll | sh alldo.sh make .easm.test

ebc.test:
	ls */*.lll | sh alldo.sh make .ebc.test

alltest: ebc.test easm.test lll.test
