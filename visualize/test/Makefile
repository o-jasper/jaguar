
default: control_flow.svg straight.svg

clean:
	rm control_flow.svg straight.svg

%.svg: test_%.py ../visualize.py
	python2 $<

%.png: %svg
	convert $< $@
