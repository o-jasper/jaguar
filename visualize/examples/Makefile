
default: sg cf

clean:
	rm cf/cf_*.png cf/cf_*.svg sg/sg_*.png sg/sg_*.svg

sg: sg_png
cf: cf_png

VISUALIZE=../bin/code-visualize.py

sg/sg_%.png: %.lsp ../visualize.py ../bin/code-visualize.py
	$(VISUALIZE) $< $@ --which sg --uniqify no

sg/sg_uniq_%.png: %.lsp ../visualize.py ../bin/code-visualize.py
	$(VISUALIZE) $< $@ --which sg

cf/cf_%.png: %.lsp ../visualize.py ../bin/code-visualize.py
	$(VISUALIZE) $< $@ --theme cut_corners

sg/sg_%.svg: %.lsp ../visualize.py ../bin/code-visualize.py
	$(VISUALIZE) $< $@ --which sg --uniqify no

sg/sg_uniq_%.svg: %.lsp ../visualize.py ../bin/code-visualize.py
	$(VISUALIZE) $< $@ --which sg

cf/cf_%.svg: %.lsp ../visualize.py ../bin/code-visualize.py
	$(VISUALIZE) $< $@

png: sg_png cf_png
svg: sg_svg cf_svg

sg_svg: sg/sg_Bank.svg sg/sg_kv.svg sg/sg_NameReg.svg sg/sg_Splitter.svg sg/sg_SubCurrency.svg
sg_png: sg/sg_Bank.png sg/sg_kv.png sg/sg_NameReg.png sg/sg_Splitter.png sg/sg_SubCurrency.png

cf_svg: cf/cf_Bank.svg cf/cf_kv.svg cf/cf_NameReg.svg cf/cf_Splitter.svg cf/cf_SubCurrency.svg
cf_png: cf/cf_Bank.png cf/cf_kv.png cf/cf_NameReg.png cf/cf_Splitter.png cf/cf_SubCurrency.png

sg_uniq_svg: sg/sg_uniq_Bank.svg sg/sg_uniq_kv.svg sg/sg_uniq_NameReg.svg sg/sg_uniq_Splitter.svg sg/sg_uniq_SubCurrency.svg
sg_uniq_png: sg/sg_uniq_Bank.png sg/sg_uniq_kv.png sg/sg_uniq_NameReg.png sg/sg_uniq_Splitter.png sg/sg_uniq_SubCurrency.png

show_off.html: show_off.sh png sg_uniq_png
	sh show_off.sh > show_off.html
