#! /usr/bin/env python3

from setuptools import setup, find_packages
import codecs
import glob
import os
import re

# look/set what version we have
changelog = 'debian/changelog'
if os.path.exists(changelog):
    head = codecs.open(changelog, encoding='utf-8').readline()
    match = re.compile('.*\((.*)\).*').match(head)
    if match:
        version = match.group(1)

scripts = glob.glob('bin/snap-*')
scripts.append('bin/create-snap-declaration')
scripts.append('bin/get-base-declaration')
scripts.append('bin/snap-updates-available')
scripts.append('bin/snap-check-notices')
scripts.append('bin/fetch-db')
scripts.append('bin/diffsquash')
scripts.append('bin/store-query')
scripts.remove('bin/snap-check-skeleton')
setup(
    name='review-tools',
    version=version,
    scripts=scripts,
    packages=find_packages(),
    test_suite='reviewtools.tests',
    package_data={'reviewtools': ['data/*.yaml', 'data/*.json']},
    include_package_data=True,
)
