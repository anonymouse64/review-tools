all:
	# Use setup.py to install
	exit 1

install: all

test:
	./run-tests

functest:
	./tests/test.sh

functest-system:
	./tests/test.sh system

functest-updates:
	./tests/test-updates-available.sh

coverage:
	python3 -m coverage run ./run-tests

coverage-report:
	python3 -m coverage report --show-missing --omit="*skeleton*,*/dist-packages/*"

syntax-check: clean
	./run-pyflakes
	./run-pep8
	./run-pylint

check-names:
	# make sure check-names.list is up to date
	cp -f check-names.list check-names.list.orig
	./collect-check-names
	diff -Naur check-names.list.orig check-names.list || exit 1
	rm -f check-names.list.orig

check: test functest-updates functest syntax-check check-names

clean:
	rm -rf ./reviewtools/__pycache__ ./reviewtools/tests/__pycache__
	rm -rf ./.coverage
	rm -rf ./review-tools-*
	rm -rf ./build ./review_tools.egg-info

.PHONY: check-names.list
check-names.list:
	./collect-check-names
