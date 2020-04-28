all:
	# Use setup.py to install
	exit 1

install: all

DEPENDENCIES := \
	black \
	binutils \
	execstack \
	fakeroot \
	file \
	flake8 \
	jq \
	pylint \
	python3-coverage \
	python3-magic \
	python3-requests \
	python3-setuptools \
	python3-simplejson \
	python3-yaml \
	squashfs-tools

check-deps:
	@for dep in $(DEPENDENCIES); do if ! dpkg -l $$dep 1>/dev/null 2>&1; then echo "Please apt install $$dep"; exit 1; fi; done

test:
	./run-tests

functest:
	./tests/test.sh

functest-system:
	./tests/test.sh system

functest-updates:
	./tests/test-updates-available.sh

functest-dump-tool:
	./tests/test-dump-tool.sh

coverage:
	python3 -m coverage run ./run-tests

coverage-report:
	python3 -m coverage report --show-missing --omit="*skeleton*,*/dist-packages/*"

syntax-check: clean
	./run-flake8
	./run-pylint

style-check: clean
	./run-black

check-names:
	# make sure check-names.list is up to date
	cp -f check-names.list check-names.list.orig
	./collect-check-names
	diff -Naur check-names.list.orig check-names.list || exit 1
	rm -f check-names.list.orig

check: check-deps test functest-updates functest-dump-tool functest syntax-check style-check check-names

clean:
	rm -rf ./reviewtools/__pycache__ ./reviewtools/tests/__pycache__
	rm -rf ./tests/review-tools-extras/__pycache__
	rm -rf ./.coverage
	rm -rf ./review-tools-*
	rm -rf ./build ./review_tools.egg-info

.PHONY: check-names.list
check-names.list:
	./collect-check-names
