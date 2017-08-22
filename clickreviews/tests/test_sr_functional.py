'''test_sr_functional.py: tests for the sr_functional module'''
#
# Copyright (C) 2017 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
from unittest import TestCase
import os
import shutil
import tempfile

from clickreviews.common import cleanup_unpack
from clickreviews.common import check_results as common_check_results
from clickreviews.common import cmd as cmd
from clickreviews.sr_functional import SnapReviewFunctional
import clickreviews.sr_tests as sr_tests
from clickreviews.tests import utils


class TestSnapReviewFunctional(sr_tests.TestSnapReview):
    """Tests for the functional lint review tool."""
    def setUp(self):
        super().setUp()
        self.set_test_pkgfmt("snap", "16.04")

    def test_all_checks_as_v2(self):
        '''Test snap v2 has checks'''
        self.set_test_pkgfmt("snap", "16.04")
        c = SnapReviewFunctional(self.test_name)
        c.do_checks()
        sum = 0
        for i in c.click_report:
            sum += len(c.click_report[i])
        self.assertTrue(sum != 0)

    def test_all_checks_as_v1(self):
        '''Test snap v1 has no checks'''
        self.set_test_pkgfmt("snap", "15.04")
        c = SnapReviewFunctional(self.test_name)
        c.do_checks()
        sum = 0
        for i in c.click_report:
            sum += len(c.click_report[i])
        self.assertTrue(sum == 0)

    def test_all_checks_as_click(self):
        '''Test click format has no checks'''
        self.set_test_pkgfmt("click", "0.4")
        c = SnapReviewFunctional(self.test_name)
        c.do_checks()
        sum = 0
        for i in c.click_report:
            sum += len(c.click_report[i])
        self.assertTrue(sum == 0)


class TestSnapReviewFunctionalNoMock(TestCase):
    """Tests without mocks where they are not needed."""
    def setUp(self):
        # XXX cleanup_unpack() is required because global variables
        # UNPACK_DIR, RAW_UNPACK_DIR are initialised to None at module
        # load time, but updated when a real (non-Mock) test runs, such as
        # here. While, at the same time, two of the existing tests using
        # mocks depend on both global vars being None. Ideally, those
        # global vars should be refactored away.
        self.addCleanup(cleanup_unpack)
        super().setUp()

    def mkdtemp(self):
        """Create a temp dir which is cleaned up after test."""
        tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp_dir)
        return tmp_dir

    def check_results(self, report,
                      expected_counts={'info': 1, 'warn': 0, 'error': 0},
                      expected=None):
        common_check_results(self, report, expected_counts, expected)

    def test_check_execstack(self):
        '''Test check_execstack() - execstack found execstack binary'''
        # copy /bin/ls nonexecstack.bin
        package = utils.make_snap2(output_dir=self.mkdtemp(),
                                   extra_files=['/bin/ls:nonexecstack.bin']
                                   )
        c = SnapReviewFunctional(package)
        c.check_execstack()
        report = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(report, expected_counts)

    def test_check_execstack_found_binary(self):
        '''Test check_execstack() - execstack found execstack binary'''
        output_dir = self.mkdtemp()
        fn = os.path.join(output_dir, "hasexecstack.bin")
        shutil.copyfile('/bin/ls', fn)
        # create a /bin/ls with executable stack
        cmd(['execstack', '--set-execstack', fn])

        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = [fn]
        c.check_execstack()
        report = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(report, expected_counts)

        # with how we mocked, we have the absolute path of the file in the
        # tmpdir, so verify beginning of warn only
        self.assertTrue('warn' in report)
        name = 'functional-snap-v2:execstack'
        self.assertTrue(name in report['warn'])
        self.assertTrue('text' in report['warn'][name])
        self.assertTrue(report['warn'][name]['text'].startswith("Found files with executable stack"))

    def test_check_execstack_found_binary_devmode(self):
        '''Test check_execstack() - execstack found execstack binary - devmode'''
        output_dir = self.mkdtemp()
        fn = os.path.join(output_dir, "hasexecstack.bin")
        shutil.copyfile('/bin/ls', fn)
        # create a /bin/ls with executable stack
        cmd(['execstack', '--set-execstack', fn])

        yaml = """architectures: [ all ]
name: test
version: 1.0
summary: An application
description: An application
confinement: devmode
"""
        package = utils.make_snap2(output_dir=output_dir, yaml=yaml)
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = [fn]
        c.check_execstack()
        report = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(report, expected_counts)

        # with how we mocked, we have the absolute path of the file in the
        # tmpdir, so verify beginning of info only
        self.assertTrue('info' in report)
        name = 'functional-snap-v2:execstack'
        self.assertTrue(name in report['info'])
        self.assertTrue('text' in report['info'][name])
        self.assertTrue(report['info'][name]['text'].startswith("Found files with executable stack"))

    def test_check_execstack_os(self):
        '''Test check_execstack() - os snap'''
        output_dir = self.mkdtemp()
        fn = os.path.join(output_dir, "hasexecstack.bin")
        shutil.copyfile('/bin/ls', fn)
        # create a /bin/ls with executable stack
        cmd(['execstack', '--set-execstack', fn])

        yaml = """architectures: [ all ]
name: test
version: 1.0
summary: An application
description: An application
type: os
"""
        package = utils.make_snap2(output_dir=output_dir, yaml=yaml)
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = [fn]
        c.check_execstack()
        report = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(report, expected_counts)

    def test_check_execstack_rc_nonzero(self):
        '''Test check_execstack() - execstack returns non-zero'''
        package = utils.make_snap2(output_dir=self.mkdtemp())
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = ["path/to/nonexistent/file"]
        c.check_execstack()
        report = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(report, expected_counts)
