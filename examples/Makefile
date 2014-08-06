
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

%.ebc.test: % jag
	../bin/jaguar $< ebc | ../remember_test.sh $@ ; touch $@

%.easm.test: % jag
	../bin/jaguar $< easm | ../remember_test.sh $@ ; touch $@

%.lll.test: % jag
	../bin/jaguar $< lll | ../remember_test.sh $@ ; touch $@

%.exp.lll.test: % jag
	../bin/jaguar $< exp.lll | ../remember_test.sh $@ ; touch $@

ebc.test: Bank/Bank.lll.ebc.test Key_Value/kv.lll.ebc.test NameReg/NameReg.lll.ebc.test Splitter/Splitter.lll.ebc.test \
	SubCurrency/SubCurrency.lll.ebc.test

easm.test: Bank/Bank.lll.easm.test Key_Value/kv.lll.easm.test NameReg/NameReg.lll.easm.test Splitter/Splitter.lll.easm.test \
	SubCurrency/SubCurrency.lll.easm.test

lll.test: Bank/Bank.lll.lll.test Key_Value/kv.lll.lll.test NameReg/NameReg.lll.lll.test Splitter/Splitter.lll.lll.test \
	SubCurrency/SubCurrency.lll.lll.test

exp.lll.test: Bank/Bank.lll.exp.lll.test Key_Value/kv.lll.exp.lll.test NameReg/NameReg.lll.exp.lll.test Splitter/Splitter.lll.exp.lll.test \
	SubCurrency/SubCurrency.lll.exp.lll.test

alltest: ebc.test easm.test lll.test
