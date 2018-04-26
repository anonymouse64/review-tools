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
	python3 -mjson.tool ./data/*.json >/dev/null
	CHECK_CLICK_FILES=1 ./run-pyflakes
	CHECK_CLICK_FILES=1 ./run-pep8
	CHECK_CLICK_FILES=1 ./run-pylint

check-names:
	# make sure check-names.list is up to date
	cp -f check-names.list check-names.list.orig
	./collect-check-names
	diff -Naur check-names.list.orig check-names.list || exit 1
	rm -f check-names.list.orig

check: test functest-updates functest syntax-check check-names

clean:
	rm -rf ./clickreviews/__pycache__ ./clickreviews/tests/__pycache__
	rm -rf ./.coverage

.PHONY: check-names.list
check-names.list:
	./collect-check-names
