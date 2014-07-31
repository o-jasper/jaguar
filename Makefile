
test: test_jaguar_internal test_jaguar

test_jaguar:
	python2 runtests.py | ./remember_test.sh runtests

test_jaguar_internal:	
	cd jaguar/test/; make test
