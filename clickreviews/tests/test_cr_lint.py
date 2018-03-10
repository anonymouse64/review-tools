'''test_cr_lint.py: tests for the cr_lint module'''
#
# Copyright (C) 2013-2015 Canonical Ltd.
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

from unittest import TestCase
from unittest.mock import patch

from clickreviews.common import cleanup_unpack
from clickreviews.cr_lint import ClickReviewLint
from clickreviews.cr_lint import MINIMUM_CLICK_FRAMEWORK_VERSION
from clickreviews.frameworks import FRAMEWORKS_DATA_URL, USER_DATA_FILE
from clickreviews.tests import utils
import clickreviews.cr_tests as cr_tests

import os
import shutil
import stat
import tempfile


class TestClickReviewLint(cr_tests.TestClickReview):
    """Tests for the lint review tool."""

    def _create_hashes_yaml(self):
        # find cr_tests.py since that is what _get_statinfo() is mocked to
        # look at.
        f = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         "../cr_tests.py")
        statinfo = os.stat(f)
        self.sha512 = cr_tests._get_sha512sum(self, f)
        hashes = {'archive-sha512': self.sha512,
                  'files': [{'name': 'bin',
                             'mode': 'drwxrwxr-x'},
                            {'name': 'bin/foo',
                             'size': statinfo.st_size,
                             'mode': 'f%s' %
                                     stat.filemode(statinfo.st_mode)[1:],
                             'sha512': self.sha512},
                            {'name': 'barlink',
                             'mode': 'lrwxrwxrwx'},
                            ]
                  }
        self._test_pkg_files = []
        for i in hashes['files']:
            self._test_pkg_files.append(i['name'])
        return hashes

    def patch_frameworks(self):
        def _mock_frameworks(self, overrides=None):
            self.FRAMEWORKS = {
                'ubuntu-core-15.04': 'available',
                'ubuntu-sdk-14.10-qml-dev2': 'available',
                'ubuntu-sdk-13.10': 'deprecated',
                'ubuntu-sdk-14.10-qml-dev1': 'obsolete',
            }
            self.AVAILABLE_FRAMEWORKS = ['ubuntu-core-15.04',
                                         'ubuntu-sdk-14.10-qml-dev2']
            self.OBSOLETE_FRAMEWORKS = ['ubuntu-sdk-14.10-qml-dev1']
            self.DEPRECATED_FRAMEWORKS = ['ubuntu-sdk-13.10']
        p = patch('clickreviews.frameworks.Frameworks.__init__',
                  _mock_frameworks)
        p.start()
        self.addCleanup(p.stop)

    def test_check_architecture(self):
        '''Test check_architecture()'''
        c = ClickReviewLint(self.test_name)
        c.check_architecture()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architecture_all(self):
        '''Test check_architecture_all() - no binaries'''
        self.set_test_control("Architecture", "all")
        self.set_test_manifest("architecture", "all")
        c = ClickReviewLint(self.test_name)
        c.pkg_bin_files = []
        c.check_architecture_all()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architecture_all2(self):
        '''Test check_architecture_all() - binaries'''
        self.set_test_control("Architecture", "all")
        self.set_test_manifest("architecture", "all")
        c = ClickReviewLint(self.test_name)
        c.pkg_bin_files = ["path/to/some/compiled/binary"]
        c.check_architecture_all()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_architecture_armhf(self):
        '''Test check_architecture() - armhf'''
        self.set_test_control("Architecture", "armhf")
        c = ClickReviewLint(self.test_name)
        c.check_architecture()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architecture_i386(self):
        '''Test check_architecture() - i386'''
        self.set_test_control("Architecture", "i386")
        c = ClickReviewLint(self.test_name)
        c.check_architecture()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architecture_arm64(self):
        '''Test check_architecture() - arm64'''
        self.set_test_control("Architecture", "arm64")
        c = ClickReviewLint(self.test_name)
        c.check_architecture()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architecture_amd64(self):
        '''Test check_architecture() - amd64'''
        self.set_test_control("Architecture", "amd64")
        c = ClickReviewLint(self.test_name)
        c.check_architecture()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architecture_nonexistent(self):
        '''Test check_architecture() - nonexistent'''
        self.set_test_control("Architecture", "nonexistent")
        self.set_test_pkgfmt("click", "0.4")
        c = ClickReviewLint(self.test_name)
        c.pkg_arch = ["nonexistent"]
        c.check_architecture()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_control_architecture(self):
        '''Test check_control() (architecture)'''
        c = ClickReviewLint(self.test_name)
        c.check_control()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_control_architecture_snappy_1504(self):
        '''Test check_control() (architecture) - snappy 15.04'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        c.check_control()
        r = c.click_report
        expected_counts = {'info': 15, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_control_architecture_missing(self):
        '''Test check_control() (architecture missing)'''
        self.set_test_control("Architecture", None)
        try:
            ClickReviewLint(self.test_name)
        except KeyError:
            return
        raise Exception("Should have raised a KeyError")

    def test_check_control_matches_manifest_architecture(self):
        '''Test check_control() (architecture matches manifest)'''
        self.set_test_control("Architecture", "armhf")
        self.set_test_manifest("architecture", "armhf")
        c = ClickReviewLint(self.test_name)
        c.check_control()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_control_mismatches_manifest_architecture(self):
        '''Test check_control() (architecture mismatches manifest)'''
        self.set_test_control("Architecture", "armhf")
        self.set_test_manifest("architecture", "amd64")
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = False
        c.check_control()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_control_mismatches_manifest_architecture_snappy(self):
        '''Test check_control() (architecture mismatches manifest (snappy))'''
        self.set_test_control("Architecture", ["all"])
        self.set_test_manifest("architecture", "all")
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = True
        c.check_control()
        r = c.click_report
        expected_counts = {'info': 15, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_control_manifest_architecture_missing(self):
        '''Test check_control() (manifest architecture)'''
        self.set_test_control("Architecture", "armhf")
        self.set_test_manifest("architecture", None)
        c = ClickReviewLint(self.test_name)
        c.check_control()
        r = c.click_report

        expected = dict()
        expected['info'] = dict()
        expected['warn'] = dict()
        expected['error'] = dict()
        name = c._get_check_name('control_architecture_match')
        expected['info'][name] = {
            "text": "OK: architecture not specified in manifest"}
        self.check_results(r, expected=expected)

    def test_check_architecture_specified_needed(self):
        '''Test check_architecture_specified_needed() - no binaries'''
        self.set_test_control("Architecture", "armhf")
        self.set_test_manifest("architecture", "armhf")
        c = ClickReviewLint(self.test_name)
        c.pkg_arch = ['armhf']
        c.pkg_bin_files = []
        c.check_architecture_specified_needed()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architecture_specified_needed2(self):
        '''Test check_architecture_specified_needed2() - binaries'''
        self.set_test_control("Architecture", "armhf")
        self.set_test_manifest("architecture", "armhf")
        c = ClickReviewLint(self.test_name)
        c.pkg_bin_files = ["path/to/some/compiled/binary"]
        c.check_architecture_specified_needed()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_manifest_missing_arch(self):
        '''Test check_manifest_architecture() (missing)'''
        self.set_test_manifest("architecture", None)
        c = ClickReviewLint(self.test_name)
        c.check_manifest_architecture()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_manifest_missing_arch_snappy_1504(self):
        '''Test check_manifest_architecture() - snappy 15.04'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_manifest("architecture", None)
        c = ClickReviewLint(self.test_name)
        c.check_manifest_architecture()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_manifest_arch_all(self):
        '''Test check_manifest_architecture() (all)'''
        self.set_test_manifest("architecture", "all")
        c = ClickReviewLint(self.test_name)
        c.check_manifest_architecture()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_manifest_arch_single_armhf(self):
        '''Test check_manifest_architecture() (single arch, armhf)'''
        self.set_test_manifest("architecture", "armhf")
        c = ClickReviewLint(self.test_name)
        c.check_manifest_architecture()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_manifest_arch_single_i386(self):
        '''Test check_manifest_architecture() (single arch, i386)'''
        self.set_test_manifest("architecture", "i386")
        c = ClickReviewLint(self.test_name)
        c.check_manifest_architecture()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_manifest_arch_single_amd64(self):
        '''Test check_manifest_architecture() (single arch, amd64)'''
        self.set_test_manifest("architecture", "amd64")
        c = ClickReviewLint(self.test_name)
        c.check_manifest_architecture()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_manifest_arch_single_nonexistent(self):
        '''Test check_manifest_architecture() (single nonexistent arch)'''
        self.set_test_manifest("architecture", "nonexistent")
        c = ClickReviewLint(self.test_name)
        c.check_manifest_architecture()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_manifest_arch_single_multi(self):
        '''Test check_manifest_architecture() (single arch: invalid multi)'''
        self.set_test_manifest("architecture", "multi")
        c = ClickReviewLint(self.test_name)
        c.check_manifest_architecture()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_manifest_valid_arch_multi(self):
        '''Test check_manifest_architecture() (valid multi)'''
        arch = "multi"
        self.set_test_manifest("architecture", ["armhf"])
        self.set_test_control("Architecture", arch)
        test_name = "%s_%s_%s.click" % (self.test_control['Package'],
                                        self.test_control['Version'],
                                        arch)
        c = ClickReviewLint(test_name)
        c.check_manifest_architecture()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_manifest_valid_arch_multi2(self):
        '''Test check_manifest_architecture() (valid multi2)'''
        arch = "multi"
        self.set_test_manifest("architecture", ["armhf", "i386"])
        self.set_test_control("Architecture", arch)
        test_name = "%s_%s_%s.click" % (self.test_control['Package'],
                                        self.test_control['Version'],
                                        arch)
        c = ClickReviewLint(test_name)
        c.check_manifest_architecture()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_manifest_invalid_arch_multi_nonexistent(self):
        '''Test check_manifest_architecture() (invalid multi)'''
        arch = "multi"
        self.set_test_manifest("architecture", ["armhf", "nonexistent"])
        self.set_test_control("Architecture", arch)
        test_name = "%s_%s_%s.click" % (self.test_control['Package'],
                                        self.test_control['Version'],
                                        arch)
        c = ClickReviewLint(test_name)
        c.check_manifest_architecture()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_manifest_invalid_arch_multi_all(self):
        '''Test check_manifest_architecture() (invalid all)'''
        arch = "multi"
        self.set_test_manifest("architecture", ["armhf", "all"])
        self.set_test_control("Architecture", arch)
        test_name = "%s_%s_%s.click" % (self.test_control['Package'],
                                        self.test_control['Version'],
                                        arch)
        c = ClickReviewLint(test_name)
        c.is_snap1 = False
        c.check_manifest_architecture()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_manifest_invalid_arch_multi_multi(self):
        '''Test check_manifest_architecture() (invalid multi)'''
        arch = "multi"
        self.set_test_manifest("architecture", ["multi", "armhf"])
        self.set_test_control("Architecture", arch)
        test_name = "%s_%s_%s.click" % (self.test_control['Package'],
                                        self.test_control['Version'],
                                        arch)
        c = ClickReviewLint(test_name)
        c.check_manifest_architecture()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_control(self):
        """A very basic test to make sure check_control can be tested."""
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = False
        c.check_control()
        r = c.click_report
        expected_counts = {'info': 15, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_control_snap(self):
        """check_control with snap."""
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = True
        c.check_control()
        r = c.click_report
        expected_counts = {'info': 15, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_control_snap_missing_maintainer(self):
        """check_control with snap with missing maintainer."""
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = True
        self.set_test_control('Maintainer', None)
        c.check_control()
        r = c.click_report
        expected_counts = {'info': 15, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)
        # Lets check that the right info is triggering
        name = c._get_check_name('control_has_field:Maintainer')
        m = r['info'][name]['text']
        self.assertIn('OK (maintainer not required for snappy)', m)

    # Make the current MINIMUM_CLICK_FRAMEWORK_VERSION newer
    @patch('clickreviews.cr_lint.MINIMUM_CLICK_FRAMEWORK_VERSION',
           MINIMUM_CLICK_FRAMEWORK_VERSION + '.1')
    def test_check_control_click_framework_version(self):
        """Test that enforcing click framework versions works."""
        test_name = 'net.launchpad.click-webapps.test-app_3_all.click'
        c = ClickReviewLint(test_name)
        c.check_control()
        r = c.click_report
        # We should end up with an error as the click version is out of date
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        # Lets check that the right error is triggering
        name = c._get_check_name('control_click_version_up_to_date')
        m = r['error'][name]['text']
        self.assertIn('Click-Version is too old', m)

    def test_check_maintainer(self):
        '''Test check_maintainer()'''
        c = ClickReviewLint(self.test_name)
        c.check_maintainer()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_maintainer_empty(self):
        '''Test check_maintainer() - empty'''
        self.set_test_manifest("maintainer", "")
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = False
        c.check_maintainer()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_maintainer_empty_snap(self):
        '''Test check_maintainer() - empty (snap)'''
        self.set_test_manifest("maintainer", "")
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = True
        c.check_maintainer()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_maintainer_missing(self):
        '''Test check_maintainer() - missing (click)'''
        self.set_test_manifest("maintainer", None)
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = False
        c.check_maintainer()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_maintainer_missing_snap(self):
        '''Test check_maintainer() - missing (snap)'''
        self.set_test_manifest("maintainer", None)
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = True
        c.check_maintainer()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_maintainer_badformat(self):
        '''Test check_maintainer() - badly formatted'''
        self.set_test_manifest("maintainer", "$%^@*")
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = False
        c.check_maintainer()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_maintainer_badformat_snap(self):
        '''Test check_maintainer() - badly formatted (snap)'''
        self.set_test_manifest("maintainer", "$%^@*")
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = True
        c.check_maintainer()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_maintainer_bad_email_missing_name(self):
        '''Test check_maintainer() - bad email (missing name)'''
        self.set_test_manifest("name", "com.ubuntu.developer.user.app")
        self.set_test_manifest("maintainer",
                               "user@example.com")
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = False
        c.check_maintainer()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_maintainer_bad_email_missing_name_snap(self):
        '''Test check_maintainer() - bad email (missing name, snap)'''
        self.set_test_manifest("name", "com.ubuntu.developer.user.app")
        self.set_test_manifest("maintainer",
                               "user@example.com")
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = True
        c.check_maintainer()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_maintainer_domain_appstore(self):
        '''Test check_maintainer() - appstore domain
           (com.ubuntu.developer)'''
        self.set_test_manifest("name", "com.ubuntu.developer.user.app")
        self.set_test_manifest("maintainer",
                               "Foo User <user@example.com>")
        c = ClickReviewLint(self.test_name)
        c.check_maintainer()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_icon(self):
        '''Test check_icon()'''
        self.set_test_manifest("icon", "someicon")
        c = ClickReviewLint(self.test_name)
        c.check_icon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_icon_snappy_1504(self):
        '''Test check_icon() - snappy 15.04'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_manifest("icon", "someicon")
        c = ClickReviewLint(self.test_name)
        c.check_icon()
        r = c.click_report
        expected_counts = {'info': 3, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_icon_unspecified(self):
        '''Test check_icon()'''
        self.set_test_manifest("icon", None)
        c = ClickReviewLint(self.test_name)
        c.check_icon()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_icon_empty(self):
        '''Test check_icon() - empty'''
        self.set_test_manifest("icon", "")
        c = ClickReviewLint(self.test_name)
        c.check_icon()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_icon_absolute_path(self):
        '''Test check_icon() - absolute path'''
        self.set_test_manifest("icon", "/foo/bar/someicon")
        c = ClickReviewLint(self.test_name)
        c.check_icon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_click_local_extensions_missing(self):
        '''Testeck_click_local_extensions() - missing'''
        for k in self.test_manifest.keys():
            if k.startswith("x-"):
                self.set_test_manifest(k, None)
        c = ClickReviewLint(self.test_name)
        c.check_click_local_extensions()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_click_local_extensions_empty(self):
        '''Testeck_click_local_extensions() - empty'''
        for k in self.test_manifest.keys():
            if k.startswith("x-"):
                self.set_test_manifest(k, None)
        self.set_test_manifest("x-test", "")
        c = ClickReviewLint(self.test_name)
        c.check_click_local_extensions()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_click_local_extensions(self):
        '''Testeck_click_local_extensions()'''
        for k in self.test_manifest.keys():
            if k.startswith("x-"):
                self.set_test_manifest(k, None)
        self.set_test_manifest("x-source", {"vcs-bzr": "lp:notes-app",
                                            "vcs-bzr-revno": "209"})
        c = ClickReviewLint(self.test_name)
        c.check_click_local_extensions()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_click_local_extensions_coreapp(self):
        '''Testeck_click_local_extensions() - coreapp'''
        for k in self.test_manifest.keys():
            if k.startswith("x-"):
                self.set_test_manifest(k, None)
        self.set_test_manifest("x-source", "foo")
        c = ClickReviewLint(self.test_name)
        c.is_core_app = True
        c.check_click_local_extensions()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_click_local_extensions_snappy_1504(self):
        '''Testeck_click_local_extensions() - snappy 15.04'''
        self.set_test_pkgfmt("snap", "15.04")
        for k in self.test_manifest.keys():
            if k.startswith("x-"):
                self.set_test_manifest(k, None)
        self.set_test_manifest("x-source", {"vcs-bzr": "lp:notes-app",
                                            "vcs-bzr-revno": "209"})
        c = ClickReviewLint(self.test_name)
        c.check_click_local_extensions()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_framework(self):
        '''Test check_framework()'''
        self.patch_frameworks()
        self.set_test_manifest("framework", "ubuntu-sdk-14.10-qml-dev2")
        c = ClickReviewLint(self.test_name)
        c.check_framework()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_framework_multiple_click(self):
        '''Test check_framework() - click'''
        self.patch_frameworks()
        self.set_test_manifest("framework",
                               "ubuntu-sdk-14.10-qml-dev2,ubuntu-core-15.04")
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = False
        c.check_framework()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_framework_multiple_snappy(self):
        '''Test check_framework() - snappy'''
        self.patch_frameworks()
        self.set_test_manifest("framework",
                               "ubuntu-sdk-14.10-qml-dev2,ubuntu-core-15.04")
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = True
        c.check_framework()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    @patch('clickreviews.remote.read_cr_file')
    def test_check_framework_fetches_remote_data(self, mock_read_cr_file):
        '''Test check_framework()'''
        mock_read_cr_file.return_value = {
            'ubuntu-sdk-14.10-qml-dev2': 'available',
        }
        self.set_test_manifest("framework", "ubuntu-sdk-14.10-qml-dev2")
        c = ClickReviewLint(self.test_name)
        c.check_framework()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)
        # ensure no local fn is provided when reading frameworks
        mock_read_cr_file.assert_called_once_with(
            USER_DATA_FILE, FRAMEWORKS_DATA_URL, local_copy_fn=None)

    def test_check_framework_bad(self):
        '''Test check_framework() - bad'''
        self.patch_frameworks()
        self.set_test_manifest("framework", "nonexistent")
        c = ClickReviewLint(self.test_name)
        c.check_framework()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_framework_deprecated(self):
        '''Test check_framework() - deprecated'''
        self.patch_frameworks()
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        c.check_framework()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_framework_obsolete(self):
        '''Test check_framework() - obsolete'''
        self.patch_frameworks()
        self.set_test_manifest("framework", "ubuntu-sdk-14.10-qml-dev1")
        c = ClickReviewLint(self.test_name)
        c.check_framework()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    @patch('clickreviews.remote.read_cr_file')
    def test_check_framework_with_overrides(self, mock_read_cr_file):
        '''Test check_framework() - using overrides'''
        mock_read_cr_file.return_value = {
            'ubuntu-sdk-14.10-qml-dev2': 'available',
        }
        self.set_test_manifest("framework", "nonexistent")
        overrides = {'framework': {'nonexistent': {'state': 'available'}}}
        c = ClickReviewLint(self.test_name, overrides=overrides)
        c.check_framework()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    @patch('clickreviews.remote.read_cr_file')
    def test_check_framework_with_overrides_obsolete(self, mock_read_cr_file):
        '''Test check_framework() - using override obsoletes available'''
        fwk = 'ubuntu-sdk-14.10-qml-dev2'
        mock_read_cr_file.return_value = {
            '%s' % fwk: 'available',
        }
        self.set_test_manifest("framework", fwk)
        overrides = {'framework': {'%s' % fwk: {'state': 'obsolete'}}}
        c = ClickReviewLint(self.test_name, overrides=overrides)
        c.check_framework()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    @patch('clickreviews.remote.read_cr_file')
    def test_check_framework_with_overrides_deprecated(self, mock_read_cr_file):
        '''Test check_framework() - using override deprecates available'''
        fwk = 'ubuntu-sdk-14.10-qml-dev2'
        mock_read_cr_file.return_value = {
            '%s' % fwk: 'available',
        }
        self.set_test_manifest("framework", fwk)
        overrides = {'framework': {'%s' % fwk: {'state': 'deprecated'}}}
        c = ClickReviewLint(self.test_name, overrides=overrides)
        c.check_framework()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    @patch('clickreviews.remote.read_cr_file')
    def test_check_framework_with_malformed_overrides(self, mock_read_cr_file):
        '''Test check_framework() - using overrides'''
        mock_read_cr_file.return_value = {
            'ubuntu-sdk-14.10-qml-dev2': 'available',
        }
        self.set_test_manifest("framework", "nonexistent")
        overrides = {'nonexistent': {'state': 'available'}}
        c = ClickReviewLint(self.test_name, overrides=overrides)
        c.check_framework()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_hooks(self):
        '''Test check_hooks()'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_snappy_1504(self):
        '''Test check_hooks() - snappy 15.04'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': 5, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_multiple_desktop_apps(self):
        '''Test check_hooks() - multiple desktop apps'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        tmp = c.manifest['hooks'][self.default_appname]
        c.manifest['hooks']["another-app"] = tmp
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': 9, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_multiple_apps(self):
        '''Test check_hooks() - multiple non-desktop apps'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        tmp = dict()
        for k in c.manifest['hooks'][self.default_appname].keys():
            tmp[k] = c.manifest['hooks'][self.default_appname][k]
        tmp.pop('desktop')
        tmp['scope'] = "some-scope-exec"
        c.manifest['hooks']["some-scope"] = tmp
        tmp = dict()
        for k in c.manifest['hooks'][self.default_appname].keys():
            tmp[k] = c.manifest['hooks'][self.default_appname][k]
        tmp.pop('desktop')
        tmp['push-helper'] = "push.json"
        c.manifest['hooks']["some-push-helper"] = tmp

        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': 13, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_security_extension(self):
        '''Test check_hooks() - security extension'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        tmp = dict()
        for k in c.manifest['hooks'][self.default_appname].keys():
            tmp[k] = c.manifest['hooks'][self.default_appname][k]
        tmp['apparmor'] = "%s.json" % self.default_appname
        c.manifest['hooks'][self.default_appname] = tmp

        c.check_hooks()
        r = c.click_report
        expected = dict()
        expected['info'] = dict()
        expected['warn'] = dict()
        expected['error'] = dict()
        name = c._get_check_name(
            'sdk_security_extension', app='test-app')
        expected['info'][name] = {
            "text": "test-app.json does not end with .apparmor (ok if not using sdk)"}
        self.check_results(r, expected=expected)

    def test_check_hooks_bad_appname(self):
        '''Test check_hooks() - bad appname'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        tmp = c.manifest['hooks'][self.default_appname]
        del c.manifest['hooks'][self.default_appname]
        c.manifest['hooks']["b@d@ppn@m#"] = tmp
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_hooks_missing_apparmor(self):
        '''Test check_hooks() - missing apparmor'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        del c.manifest['hooks'][self.default_appname]['apparmor']
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_hooks_missing_apparmor_with_apparmor_profile(self):
        '''Test check_hooks() - missing apparmor with apparmor-profile'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        del c.manifest['hooks'][self.default_appname]['apparmor']
        c.manifest['hooks'][self.default_appname]['apparmor-profile'] = 'foo'
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_missing_apparmor_with_puritine(self):
        '''Test check_hooks() - missing apparmor'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        del c.manifest['hooks'][self.default_appname]['apparmor']
        c.manifest['hooks'][self.default_appname]['puritine'] = 'foo'
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': 4, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_has_desktop_and_scope(self):
        '''Test check_hooks() - desktop with scope'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        c.manifest['hooks'][self.default_appname]["scope"] = "some-binary"
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_hooks_type_oem(self):
        '''Test check_hooks() - type: oem'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        c.is_snap_oem = True
        c.check_hooks()
        r = c.click_report
        # oem type has no hooks so these should all be '0'
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_unknown_nonexistent(self):
        '''Test check_hooks_unknown() - nonexistent'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        c.manifest['hooks'][self.default_appname]["nonexistant"] = "foo"
        c.check_hooks_unknown()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_unknown_nonexistent_snappy_1504(self):
        '''Test check_hooks_unknown() - nonexistent - snappy 15.04'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        c.check_hooks_unknown()
        r = c.click_report
        expected_counts = {'info': 3, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_unknown_good(self):
        '''Test check_hooks_unknown()'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        c.check_hooks_unknown()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_unknown_type_oem(self):
        '''Test check_hooks_unknown() - type: oem'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        c.is_snap_oem = True
        c.check_hooks_unknown()
        r = c.click_report
        # oem type has no hooks so these should all be '0'
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_redflagged_payui(self):
        '''Test check_hooks_redflagged() - pay-ui'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        c.manifest['hooks'][self.default_appname]["pay-ui"] = "foo"
        c.check_hooks_redflagged()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('hooks_redflag', app='test-app')
        self.check_manual_review(r, name)

    def test_check_hooks_redflagged_payui_snappy_1504(self):
        '''Test check_hooks_redflagged() - pay-ui - snappy 15.04'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        c.check_hooks_redflagged()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_redflagged_apparmor_profile(self):
        '''Test check_hooks_redflagged() - apparmor-profile'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        c.manifest['hooks'][self.default_appname]["apparmor-profile"] = "foo"
        # snap checks are handled elsewhere
        c.is_snap1 = False
        c.check_hooks_redflagged()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('hooks_redflag', app='test-app')
        self.check_manual_review(r, name)

    def test_check_hooks_redflagged_puritine(self):
        '''Test check_hooks_redflagged() - puritine'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        c.manifest['hooks'][self.default_appname]["puritine"] = "foo"
        c.check_hooks_redflagged()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('hooks_redflag', app='test-app')
        self.check_manual_review(r, name)

    def test_pkgname_toplevel(self):
        '''Test check_pkgname - toplevel'''
        self.set_test_manifest("name", "foo")
        c = ClickReviewLint(self.test_name)
        c.check_pkgname()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_pkgname_flat(self):
        '''Test check_pkgname - flat'''
        self.set_test_manifest("name", "foo.bar")
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = False
        c.check_pkgname()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_pkgname_reverse_domain(self):
        '''Test check_pkgname - reverse domain'''
        self.set_test_manifest("name", "com.ubuntu.develeper.baz.foo")
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = False
        c.check_pkgname()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_snappy_name_toplevel_1504(self):
        '''Test check_snappy_name - toplevel - 15.04'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", "foo")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_name()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_snappy_name_flat(self):
        '''Test check_snappy_name - obsoleted flat'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", "foo.bar")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_snappy_name_reverse_domain(self):
        '''Test check_snappy_name - obsoleted reverse domain'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", "com.ubuntu.develeper.baz.foo")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_snappy_name_bad(self):
        '''Test check_snappy_name - bad'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", "foo?bar")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_snappy_name_bad2(self):
        '''Test check_snappy_name - empty'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", "")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_snappy_name_bad3(self):
        '''Test check_snappy_name - list'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", [])
        c = ClickReviewLint(self.test_name)
        c.check_snappy_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_snappy_name_bad4(self):
        '''Test check_snappy_name - dict'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", {})
        c = ClickReviewLint(self.test_name)
        c.check_snappy_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_snappy_version_1504(self):
        '''Test check_snappy_version - 15.04'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("version", 1)
        c = ClickReviewLint(self.test_name)
        c.check_snappy_version()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_snappy_version1(self):
        '''Test check_snappy_version - integer'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("version", 1)
        c = ClickReviewLint(self.test_name)
        c.check_snappy_version()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_snappy_version2(self):
        '''Test check_snappy_version - float'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("version", 1.0)
        c = ClickReviewLint(self.test_name)
        c.check_snappy_version()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_snappy_version3(self):
        '''Test check_snappy_version - MAJOR.MINOR.MICRO'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("version", "1.0.1")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_version()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_snappy_version4(self):
        '''Test check_snappy_version - str'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("version", "1.0a")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_version()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_snappy_version5(self):
        '''Test check_snappy_version - alpha'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("version", "a.b")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_version()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_snappy_version_bad(self):
        '''Test check_snappy_version - bad'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("version", "foo?bar")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_version()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_snappy_version_bad2(self):
        '''Test check_snappy_version - empty'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("version", "")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_version()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_snappy_version_bad3(self):
        '''Test check_snappy_version - list'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("version", [])
        c = ClickReviewLint(self.test_name)
        c.check_snappy_version()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_snappy_version_bad4(self):
        '''Test check_snappy_version - dict'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("version", {})
        c = ClickReviewLint(self.test_name)
        c.check_snappy_version()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_snappy_type(self):
        '''Test check_snappy_type - unspecified'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("type", None)
        c = ClickReviewLint(self.test_name)
        c.check_snappy_type()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_snappy_type_app_1504(self):
        '''Test check_snappy_type - app - 15.04'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("type", "app")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_type()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_snappy_type_framework(self):
        '''Test check_snappy_type - framework'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("type", "framework")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_type()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_snappy_type_oem(self):
        '''Test check_snappy_type - oem'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("type", "oem")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_type()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_snappy_type_redflagged_1504(self):
        '''Test check_snappy_type_redflagged - unspecified - 15.04'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("type", None)
        c = ClickReviewLint(self.test_name)
        c.check_snappy_type_redflagged()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_snappy_type_redflagged_app(self):
        '''Test check_snappy_type_redflagged - app'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("type", "app")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_type_redflagged()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_snappy_type_redflagged_framework(self):
        '''Test check_snappy_type_redflagged - framework'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("type", "framework")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_type_redflagged()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_snappy_type_redflagged_oem(self):
        '''Test check_snappy_type_redflagged - oem'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("type", "oem")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_type_redflagged()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snappy_icon_1504(self):
        '''Test check_snappy_icon() - 15.04'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("icon", "someicon")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_icon()
        r = c.click_report
        expected_counts = {'info': 3, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_icon_unspecified(self):
        '''Test check_snappy_icon() - unspecified'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("icon", None)
        c = ClickReviewLint(self.test_name)
        c.check_snappy_icon()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_icon_empty(self):
        '''Test check_snappy_icon() - empty'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("icon", "")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_icon()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_icon_absolute_path(self):
        '''Test check_snappy_icon() - absolute path'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("icon", "/foo/bar/someicon")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_icon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snappy_missing_arch(self):
        '''Test check_snappy_architecture() (missing)'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("architectures", None)
        c = ClickReviewLint(self.test_name)
        c.check_snappy_architecture()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_arch_all_deprecated(self):
        '''Test check_snappy_architecture() (deprecated, all)'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("architecture", "all")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_architecture()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_arch_amd64_deprecated(self):
        '''Test check_snappy_architecture() (deprecated, all)'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("architecture", "amd64")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_architecture()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_arch_all(self):
        '''Test check_snappy_architecture() (all)'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("architectures", ["all"])
        c = ClickReviewLint(self.test_name)
        c.check_snappy_architecture()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_arch_single_armhf(self):
        '''Test check_snappy_architecture() (single arch, armhf)'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("architectures", ["armhf"])
        c = ClickReviewLint(self.test_name)
        c.check_snappy_architecture()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_arch_single_arm64(self):
        '''Test check_snappy_architecture() (single arch, arm64)'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("architectures", ["arm64"])
        c = ClickReviewLint(self.test_name)
        c.check_snappy_architecture()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_arch_single_i386(self):
        '''Test check_snappy_architecture() (single arch, i386)'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("architectures", ["i386"])
        c = ClickReviewLint(self.test_name)
        c.check_snappy_architecture()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_arch_single_amd64(self):
        '''Test check_snappy_architecture() (single arch, amd64)'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("architectures", ["amd64"])
        c = ClickReviewLint(self.test_name)
        c.check_snappy_architecture()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_arch_single_nonexistent(self):
        '''Test check_snappy_architecture() (single nonexistent arch)'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("architectures", ["nonexistent"])
        c = ClickReviewLint(self.test_name)
        c.check_snappy_architecture()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snappy_arch_single_multi(self):
        '''Test check_snappy_architecture() (single arch: invalid multi)'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("architectures", "multi")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_architecture()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snappy_valid_arch_multi(self):
        '''Test check_snappy_architecture() (valid multi)'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("architectures", ["armhf"])
        test_name = "%s_%s_%s.snap" % (self.test_control['Package'],
                                       self.test_control['Version'],
                                       "armhf")
        c = ClickReviewLint(test_name)
        c.check_snappy_architecture()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_valid_arch_multi2(self):
        '''Test check_snappy_architecture() (valid multi2)'''
        self.set_test_pkgfmt("snap", "15.04")
        arch = "multi"
        self.set_test_pkg_yaml("architectures", ["armhf", "i386"])
        test_name = "%s_%s_%s.snap" % (self.test_control['Package'],
                                       self.test_control['Version'],
                                       arch)
        c = ClickReviewLint(test_name)
        c.check_snappy_architecture()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_invalid_arch_multi_nonexistent(self):
        '''Test check_snappy_architecture() (invalid multi)'''
        self.set_test_pkgfmt("snap", "15.04")
        arch = "multi"
        self.set_test_pkg_yaml("architectures", ["armhf", "nonexistent"])
        test_name = "%s_%s_%s.snap" % (self.test_control['Package'],
                                       self.test_control['Version'],
                                       arch)
        c = ClickReviewLint(test_name)
        c.check_snappy_architecture()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snappy_invalid_arch_multi_all(self):
        '''Test check_snappy_architecture() (invalid all)'''
        self.set_test_pkgfmt("snap", "15.04")
        arch = "multi"
        self.set_test_pkg_yaml("architectures", ["armhf", "all"])
        test_name = "%s_%s_%s.snap" % (self.test_control['Package'],
                                       self.test_control['Version'],
                                       arch)
        c = ClickReviewLint(test_name)
        c.check_snappy_architecture()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_invalid_arch_multi_multi(self):
        '''Test check_snappy_architecture() (invalid multi)'''
        self.set_test_pkgfmt("snap", "15.04")
        arch = "multi"
        self.set_test_pkg_yaml("architectures", ["multi", "armhf"])
        test_name = "%s_%s_%s.snap" % (self.test_control['Package'],
                                       self.test_control['Version'],
                                       arch)
        c = ClickReviewLint(test_name)
        c.check_snappy_architecture()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snappy_unknown_entries(self):
        '''Test check_snappy_unknown_entries - none'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", "foo")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_unknown_entries()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_unknown_entries2(self):
        '''Test check_snappy_unknown_entries - one'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("nonexistent", "bar")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_unknown_entries()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_unknown_obsoleted(self):
        '''Test check_snappy_unknown_entries - obsoleted'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("maintainer", "bar")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_unknown_entries()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        # Lets check that the right warning is triggering
        name = c._get_check_name('snappy_unknown')
        m = r['error'][name]['text']
        self.assertIn("unknown entries in package.yaml: 'maintainer' "
                      "(maintainer obsoleted)", m)

    def test_check_snappy_readme_md(self):
        '''Test check_snappy_readme_md()'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", self.test_name.split('_')[0])
        self.set_test_readme_md("%s - some description" %
                                self.test_name.split('_')[0])
        c = ClickReviewLint(self.test_name)
        c.check_snappy_readme_md()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_readme_md_bad(self):
        '''Test check_snappy_readme_md() - short'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", "prettylong.name")
        self.set_test_readme_md("abc")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_readme_md()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_readme_md_bad2(self):
        '''Test check_snappy_readme_md() - missing'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", self.test_name.split('_')[0])
        self.set_test_readme_md(None)
        c = ClickReviewLint(self.test_name)
        c.check_snappy_readme_md()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snappy_services_and_binaries1(self):
        '''Test check_snappy_services_and_binaries() - different'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", self.test_name.split('_')[0])
        self.set_test_pkg_yaml("services", [{"name": "foo",
                                             "start": "bin/foo"}])
        self.set_test_pkg_yaml("binaries", [{"name": "bar"}])
        c = ClickReviewLint(self.test_name)
        c.check_snappy_services_and_binaries()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_services_and_binaries2(self):
        '''Test check_snappy_services_and_binaries() - different (exec)'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", self.test_name.split('_')[0])
        self.set_test_pkg_yaml("services", [{"name": "foo",
                                             "start": "bin/foo"}])
        self.set_test_pkg_yaml("binaries", [{"name": "bar",
                                             "exec": "bin/foo"}])
        c = ClickReviewLint(self.test_name)
        c.check_snappy_services_and_binaries()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_services_and_binaries3(self):
        '''Test check_snappy_services_and_binaries() - same'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", self.test_name.split('_')[0])
        self.set_test_pkg_yaml("services", [{"name": "foo",
                                             "start": "bin/foo"}])
        self.set_test_pkg_yaml("binaries", [{"name": "foo"}])
        c = ClickReviewLint(self.test_name)
        c.check_snappy_services_and_binaries()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 2}
        self.check_results(r, expected_counts)

        name = c._get_check_name('snappy_in_services', extra='foo')
        m = r['error'][name]['text']
        self.assertIn("'foo' in both 'services' and 'binaries'", m)
        name = c._get_check_name('snappy_in_binaries', extra='foo')
        m = r['error'][name]['text']
        self.assertIn("'foo' in both 'services' and 'binaries'", m)

    def test_check_snappy_services_and_binaries4(self):
        '''Test check_snappy_services_and_binaries() - same (subdir)'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", self.test_name.split('_')[0])
        self.set_test_pkg_yaml("services", [{"name": "foo",
                                             "start": "bin/foo"}])
        self.set_test_pkg_yaml("binaries", [{"name": "bin/foo"}])
        c = ClickReviewLint(self.test_name)
        c.check_snappy_services_and_binaries()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 2}
        self.check_results(r, expected_counts)

        name = c._get_check_name('snappy_in_services', extra='foo')
        m = r['error'][name]['text']
        self.assertIn("'foo' in both 'services' and 'binaries'", m)
        name = c._get_check_name('snappy_in_binaries', extra='foo')
        m = r['error'][name]['text']
        self.assertIn("'foo' in both 'services' and 'binaries'", m)

    def test_check_snappy_services_and_binaries5(self):
        '''Test check_snappy_services_and_binaries() - same (exec, subdir)'''
        self.set_test_pkgfmt("snap", "15.04")
        self.set_test_pkg_yaml("name", self.test_name.split('_')[0])
        self.set_test_pkg_yaml("services", [{"name": "foo",
                                             "start": "bin/foo"}])
        self.set_test_pkg_yaml("binaries", [{"name": "foo",
                                             "exec": "bin/foo"}])
        c = ClickReviewLint(self.test_name)
        c.check_snappy_services_and_binaries()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 2}
        self.check_results(r, expected_counts)

        name = c._get_check_name('snappy_in_services', extra='foo')
        m = r['error'][name]['text']
        self.assertIn("'foo' in both 'services' and 'binaries'", m)
        name = c._get_check_name('snappy_in_binaries', extra='foo')
        m = r['error'][name]['text']
        self.assertIn("'foo' in both 'services' and 'binaries'", m)

    def test_check_snappy_hashes_click(self):
        '''Test check_snappy_hashes() - click'''
        self.set_test_pkgfmt("click", "0.4")
        c = ClickReviewLint(self.test_name)
        c.is_snap1 = False
        c.check_snappy_hashes()
        r = c.click_report
        # clicks don't have hashes.yaml, so should have no output
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_hashes_archive_sha512_missing(self):
        '''Test check_snappy_hashes() - archive-sha512 missing'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snappy_hashes_archive_sha512_invalid(self):
        '''Test check_snappy_hashes() - archive-sha512 invalid'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        yaml['archive-sha512'] = 'deadbeef'
        self.set_test_hashes_yaml(yaml)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('hashes_archive-sha512_valid')
        m = r['error'][name]['text']
        self.assertIn("hash mismatch: 'deadbeef' != '%s'" % self.sha512, m)

    def test_check_snappy_hashes_archive_files_missing(self):
        '''Test check_snappy_hashes() - files missing'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        del yaml['files']
        self.set_test_hashes_yaml(yaml)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('hashes_files_present')
        m = r['error'][name]['text']
        self.assertIn("'files' not found in hashes.yaml", m)

    def test_check_snappy_hashes_archive_files_ok(self):
        '''Test check_snappy_hashes() - ok'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        c.pkg_files = self._test_pkg_files
        self.set_test_hashes_yaml(yaml)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': 4, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_hashes_1504(self):
        '''Test check_snappy_hashes() - 15.04'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        c.pkg_files = self._test_pkg_files
        self.set_test_hashes_yaml(yaml)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': 4, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_hashes_archive_files_missing_name(self):
        '''Test check_snappy_hashes() - missing name'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        del yaml['files'][0]['name']
        self.set_test_hashes_yaml(yaml)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snappy_hashes_archive_files_missing_mode(self):
        '''Test check_snappy_hashes() - missing mode'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        del yaml['files'][0]['mode']
        self.set_test_hashes_yaml(yaml)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snappy_hashes_archive_files_malformed_mode(self):
        '''Test check_snappy_hashes() - malformed mode'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        yaml['files'][0]['mode'] += 'extra'
        self.set_test_hashes_yaml(yaml)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snappy_hashes_archive_files_bad_mode_entry(self):
        '''Test check_snappy_hashes() - bad mode entry'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        count = 0
        orig_mode = None
        for e in yaml['files']:
            s = list(yaml['files'][count]['mode'])
            if e['name'] == 'bin/foo':
                # keep track of the other parts of the on disk mode
                orig_mode = s
                orig_mode[3] = 'S'
                s[3] = 'S'
            yaml['files'][count]['mode'] = "".join(s)
            count += 1
        self.set_test_hashes_yaml(yaml)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('file_mode')
        m = r['error'][name]['text']
        self.assertIn("found errors in hashes.yaml: unusual mode '%s' for entry 'bin/foo'" % "".join(orig_mode), m)

    def test_check_snappy_hashes_archive_files_mode_world_write(self):
        '''Test check_snappy_hashes() - mode world write'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        count = 0
        for e in yaml['files']:
            s = list(e['mode'])
            if e['name'] == 'bin/foo' or e['name'] == 'bin':
                s[-2] = 'w'
                s[-5] = 'w'
            yaml['files'][count]['mode'] = "".join(s)
            count += 1
        self.set_test_hashes_yaml(yaml)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('file_mode')
        m = r['error'][name]['text']
        self.assertIn("found errors in hashes.yaml: 'bin' is world-writable, mode 'frw-rw-rw-' for 'bin/foo' is world-writable", m)

    def test_check_snappy_hashes_archive_files_mode_mismatch(self):
        '''Test check_snappy_hashes() - mode mismatch'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        count = 0
        orig_mode = None
        for e in yaml['files']:
            if e['mode'].startswith('f'):
                # keep track of the other parts of the on disk mode
                orig_mode = e['mode'][1:]
                yaml['files'][count]['mode'] = "f---------"
                break
            count += 1
        self.set_test_hashes_yaml(yaml)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('file_mode')
        m = r['error'][name]['text']
        self.assertIn("found errors in hashes.yaml: mode '---------' != '%s' for 'bin/foo'" % orig_mode, m)

    def test_check_snappy_hashes_archive_files_mode_bad_symlink(self):
        '''Test check_snappy_hashes() - mode bad symlink'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        yaml['files'].append({'name': 'badlink', 'mode': 'lrwxrwxr-x'})
        self.set_test_hashes_yaml(yaml)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('file_mode')
        m = r['error'][name]['text']
        self.assertIn("found errors in hashes.yaml: unusual mode 'lrwxrwxr-x' for entry 'badlink'", m)

    def test_check_snappy_hashes_archive_files_mode_devices(self):
        '''Test check_snappy_hashes() - mode devices'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        yaml['files'].append({'name': 'badblock', 'mode': 'brw-rw-r--'})
        yaml['files'].append({'name': 'badchar', 'mode': 'crw-rw-r--'})
        self.set_test_hashes_yaml(yaml)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('file_mode')
        m = r['error'][name]['text']
        self.assertIn("found errors in hashes.yaml: illegal file mode 'b': 'brw-rw-r--' for 'badblock', illegal file mode 'c': 'crw-rw-r--' for 'badchar'", m)

    def test_check_snappy_hashes_archive_files_missing_size(self):
        '''Test check_snappy_hashes() - missing size'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        count = 0
        for e in yaml['files']:
            if e['mode'].startswith('f'):
                del yaml['files'][count]['size']
                break
            count += 1
        self.set_test_hashes_yaml(yaml)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snappy_hashes_archive_files_invalid_size(self):
        '''Test check_snappy_hashes() - invalid size'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        count = 0
        for e in yaml['files']:
            if e['mode'].startswith('f'):
                orig_size = e['size']
                new_size = orig_size + 1
                yaml['files'][count]['size'] = new_size
                break
            count += 1
        self.set_test_hashes_yaml(yaml)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('file_mode')
        m = r['error'][name]['text']
        self.assertIn("found errors in hashes.yaml: size " +
                      "%d != %d for 'bin/foo'" % (new_size, orig_size), m)

    def test_check_snappy_hashes_archive_files_missing_sha512(self):
        '''Test check_snappy_hashes() - missing sha512'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        count = 0
        for e in yaml['files']:
            if e['mode'].startswith('f'):
                del yaml['files'][count]['sha512']
                break
            count += 1
        self.set_test_hashes_yaml(yaml)
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snappy_hashes_extra(self):
        '''Test check_snappy_hashes() - extra'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        yaml = self._create_hashes_yaml()
        self.set_test_hashes_yaml(yaml)
        c.pkg_files = self._test_pkg_files
        c.pkg_files.append("extrafile")
        c.check_snappy_hashes()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('hashes_extra_files')
        m = r['error'][name]['text']
        self.assertIn("found extra files not listed in hashes.yaml: extrafile",
                      m)

    def test_snappy_config(self):
        '''Test check_snappy_config()'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        c.unpack_dir = "/nonexistent"
        c.pkg_files.append(os.path.join(c.unpack_dir, 'meta/hooks/config'))
        c.check_snappy_config()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_snappy_config_nonexecutable(self):
        '''Test check_snappy_config() - not executable'''
        self.set_test_pkgfmt("snap", "15.04")
        c = ClickReviewLint(self.test_name)
        c.unpack_dir = "/nonexistent.nonexec"
        c.pkg_files.append(os.path.join(c.unpack_dir,
                                        'meta/hooks/config'))
        c.check_snappy_config()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_external_symlinks_puritine(self):
        '''Test check_external_symlinks - puritine'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        c.manifest['hooks'][self.default_appname]["puritine"] = "foo"
        c.check_external_symlinks()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)
        name = c._get_check_name('external_symlinks')
        m = r['info'][name]['text']
        self.assertIn("SKIPPED: puritine", m)

    def test_check_md5sums_puritine(self):
        '''Test check_md5sums - puritine'''
        self.set_test_manifest("framework", "ubuntu-sdk-13.10")
        c = ClickReviewLint(self.test_name)
        c.manifest['hooks'][self.default_appname]["puritine"] = "foo"
        c.check_md5sums()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)
        name = c._get_check_name('md5sums')
        m = r['info'][name]['text']
        self.assertIn("SKIPPED: puritine", m)


class ClickReviewLintTestCase(TestCase):
    """Tests without mocks where they are not needed."""
    def setUp(self):
        # XXX cleanup_unpack() is required because global variables
        # UNPACK_DIR, RAW_UNPACK_DIR, PKG_FILES and PKG_BIN_FILES are
        # initialised to None at module load time, but updated when a real
        # (non-Mock) test runs, such as here. While, at the same time, two of
        # the existing tests using mocks depend on both global vars being None.
        # Ideally, those global vars should be refactored away.
        self.addCleanup(cleanup_unpack)
        super().setUp()

    def mkdtemp(self):
        """Create a temp dir which is cleaned up after test."""
        tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp_dir)
        return tmp_dir

    def test_check_dot_click_root(self):
        package = utils.make_click(extra_files=['.click/'],
                                   output_dir=self.mkdtemp())
        c = ClickReviewLint(package)

        c.check_dot_click()

        errors = list(c.click_report['error'].keys())
        self.assertEqual(errors, ['lint:dot_click'])
