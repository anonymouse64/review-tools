'''test_sr_lint.py: tests for the sr_lint module'''
#
# Copyright (C) 2013-2016 Canonical Ltd.
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
import os
import shutil
import tempfile

from clickreviews.common import cleanup_unpack
from clickreviews.common import check_results as common_check_results
from clickreviews.sr_lint import SnapReviewLint
import clickreviews.sr_tests as sr_tests
from clickreviews.tests import utils


class TestSnapReviewLint(sr_tests.TestSnapReview):
    """Tests for the lint review tool."""
    def setUp(self):
        '''Make sure we are snap v2'''
        super().setUp()
        self.set_test_pkgfmt("snap", "16.04")

    def _create_ports(self):
        ports = {'internal': {'int1': {"port": '8081/tcp', "negotiable": True}},
                 'external': {'ext1': {"port": '80/tcp', "negotiable": False},
                              'ext2': {"port": '88/udp'}
                              }
                 }
        return ports

    def _create_top_plugs(self):
        plugs = {'iface-bool-file': {'interface': 'bool-file',
                                     'path': '/path/to/something'},
                 'iface-network': {'interface': 'network'},
                 'iface-network-bind': {'interface': 'network-bind'},
                 # intentionally omitted
                 # 'iface-network-control': {'interface': 'network-control'},
                 }
        return plugs

    def _create_apps_plugs(self):
        plugs = {'app1': {'plugs': ['iface-network']},
                 'app2': {'plugs': ['iface-network-bind']},
                 'app3': {'plugs': ['network-control']},
                 'app4': {'plugs': ['iface-bool-file']},
                 }
        return plugs

    def _create_top_slots(self):
        slots = {'iface-slot1': {'interface': 'bool-file',
                                 'path': '/path/to/something'}}
        return slots

    def _create_apps_slots(self):
        slots = {'app1': {'slots': ['iface-slot1']}}
        return slots

    def test_all_checks_as_v2(self):
        '''Test snap v2 has checks'''
        self.set_test_pkgfmt("snap", "16.04")
        c = SnapReviewLint(self.test_name)
        c.do_checks()
        sum = 0
        for i in c.click_report:
            sum += len(c.click_report[i])
        self.assertTrue(sum != 0)

    def test_all_checks_as_v1(self):
        '''Test snap v1 has no checks'''
        self.set_test_pkgfmt("snap", "15.04")
        c = SnapReviewLint(self.test_name)
        c.do_checks()
        sum = 0
        for i in c.click_report:
            sum += len(c.click_report[i])
        self.assertTrue(sum == 0)

    def test_all_checks_as_click(self):
        '''Test click format has no checks'''
        self.set_test_pkgfmt("click", "0.4")
        c = SnapReviewLint(self.test_name)
        c.do_checks()
        sum = 0
        for i in c.click_report:
            sum += len(c.click_report[i])
        self.assertTrue(sum == 0)

    def test_check_name_toplevel(self):
        '''Test check_name - toplevel'''
        self.set_test_snap_yaml("name", "foo")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_name_flat(self):
        '''Test check_name - obsoleted flat'''
        self.set_test_snap_yaml("name", "foo.bar")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_name_reverse_domain(self):
        '''Test check_name - obsoleted reverse domain'''
        self.set_test_snap_yaml("name", "com.ubuntu.develeper.baz.foo")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_name_bad(self):
        '''Test check_name - bad'''
        self.set_test_snap_yaml("name", "foo?bar")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_name_bad2(self):
        '''Test check_name - empty'''
        self.set_test_snap_yaml("name", "")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_name_bad3(self):
        '''Test check_name - list'''
        self.set_test_snap_yaml("name", [])
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_name_bad4(self):
        '''Test check_name - dict'''
        self.set_test_snap_yaml("name", {})
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_name_missing(self):
        '''Test check_name - missing'''
        self.set_test_snap_yaml("name", None)
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_version(self):
        '''Test check_version'''
        self.set_test_snap_yaml("version", 1)
        c = SnapReviewLint(self.test_name)
        c.check_version()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_version1(self):
        '''Test check_version - integer'''
        self.set_test_snap_yaml("version", 1)
        c = SnapReviewLint(self.test_name)
        c.check_version()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_version2(self):
        '''Test check_version - float'''
        self.set_test_snap_yaml("version", 1.0)
        c = SnapReviewLint(self.test_name)
        c.check_version()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_version3(self):
        '''Test check_version - MAJOR.MINOR.MICRO'''
        self.set_test_snap_yaml("version", "1.0.1")
        c = SnapReviewLint(self.test_name)
        c.check_version()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_version4(self):
        '''Test check_version - str'''
        self.set_test_snap_yaml("version", "1.0a")
        c = SnapReviewLint(self.test_name)
        c.check_version()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_version5(self):
        '''Test check_version - alpha'''
        self.set_test_snap_yaml("version", "a.b")
        c = SnapReviewLint(self.test_name)
        c.check_version()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_version_bad(self):
        '''Test check_version - bad'''
        self.set_test_snap_yaml("version", "foo?bar")
        c = SnapReviewLint(self.test_name)
        c.check_version()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_version_bad2(self):
        '''Test check_version - empty'''
        self.set_test_snap_yaml("version", "")
        c = SnapReviewLint(self.test_name)
        c.check_version()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_version_bad3(self):
        '''Test check_version - list'''
        self.set_test_snap_yaml("version", [])
        c = SnapReviewLint(self.test_name)
        c.check_version()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_version_bad4(self):
        '''Test check_version - dict'''
        self.set_test_snap_yaml("version", {})
        c = SnapReviewLint(self.test_name)
        c.check_version()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_version_missing(self):
        '''Test check_version - missing'''
        self.set_test_snap_yaml("version", None)
        c = SnapReviewLint(self.test_name)
        c.check_version()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_type(self):
        '''Test check_type - unspecified'''
        self.set_test_snap_yaml("type", None)
        c = SnapReviewLint(self.test_name)
        c.check_type()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_type_app(self):
        '''Test check_type - app'''
        self.set_test_snap_yaml("type", "app")
        c = SnapReviewLint(self.test_name)
        c.check_type()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_type_framework(self):
        '''Test check_type - framework'''
        self.set_test_snap_yaml("type", "framework")
        c = SnapReviewLint(self.test_name)
        c.check_type()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_type_redflagged(self):
        '''Test check_type_redflagged - unspecified'''
        self.set_test_snap_yaml("type", None)
        c = SnapReviewLint(self.test_name)
        c.check_type_redflagged()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_type_redflagged_app(self):
        '''Test check_type_redflagged - app'''
        self.set_test_snap_yaml("type", "app")
        c = SnapReviewLint(self.test_name)
        c.check_type_redflagged()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_type_redflagged_gadget(self):
        '''Test check_type_redflagged - gadget'''
        self.set_test_snap_yaml("type", "gadget")
        c = SnapReviewLint(self.test_name)
        c.check_type_redflagged()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('snap_type_redflag')
        self.check_manual_review(r, name)

    def test_check_type_redflagged_kernel(self):
        '''Test check_type_redflagged - kernel'''
        self.set_test_snap_yaml("type", "kernel")
        c = SnapReviewLint(self.test_name)
        c.check_type_redflagged()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('snap_type_redflag')
        self.check_manual_review(r, name)

    def test_check_type_redflagged_os(self):
        '''Test check_type_redflagged - os'''
        self.set_test_snap_yaml("type", "os")
        c = SnapReviewLint(self.test_name)
        c.check_type_redflagged()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('snap_type_redflag')
        self.check_manual_review(r, name)

    def test_check_type_unknown(self):
        '''Test check_type - unknown'''
        self.set_test_snap_yaml("type", "nonexistent")
        c = SnapReviewLint(self.test_name)
        c.check_type()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_icon(self):
        '''Test check_icon()'''
        self.set_test_snap_yaml("icon", "someicon")
        self.set_test_snap_yaml("type", "gadget")
        self.set_test_unpack_dir = "/nonexistent"
        c = SnapReviewLint(self.test_name)
        c.pkg_files.append(os.path.join(c._get_unpack_dir(), 'someicon'))
        c.check_icon()
        r = c.click_report
        expected_counts = {'info': 4, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_icon_no_gadget(self):
        '''Test check_icon() - no gadget'''
        self.set_test_snap_yaml("icon", "someicon")
        self.set_test_unpack_dir = "/nonexistent"
        c = SnapReviewLint(self.test_name)
        c.pkg_files.append(os.path.join(c._get_unpack_dir(), 'someicon'))
        c.check_icon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_icon_unspecified(self):
        '''Test check_icon() - unspecified'''
        self.set_test_snap_yaml("icon", None)
        self.set_test_snap_yaml("type", "gadget")
        c = SnapReviewLint(self.test_name)
        c.check_icon()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_icon_empty(self):
        '''Test check_icon() - empty'''
        self.set_test_snap_yaml("icon", "")
        self.set_test_snap_yaml("type", "gadget")
        c = SnapReviewLint(self.test_name)
        c.check_icon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_icon_absolute_path(self):
        '''Test check_icon() - absolute path'''
        self.set_test_snap_yaml("icon", "/foo/bar/someicon")
        self.set_test_snap_yaml("type", "gadget")
        c = SnapReviewLint(self.test_name)
        c.pkg_files.append('/foo/bar/someicon')
        c.check_icon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_icon_missing(self):
        '''Test check_icon() - missing icon'''
        self.set_test_snap_yaml("icon", "someicon")
        self.set_test_snap_yaml("type", "gadget")
        self.set_test_unpack_dir = "/nonexistent"
        c = SnapReviewLint(self.test_name)
        # since the icon isn't in c.pkg_files, don't add it for this test
        # c.pkg_files.append(os.path.join(c._get_unpack_dir(), 'someicon'))
        c.check_icon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_architectures_bad(self):
        '''Test check_architectures() - bad (dict)'''
        self.set_test_snap_yaml("architectures", {})
        c = SnapReviewLint(self.test_name)
        c.check_architectures()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_architectures_missing(self):
        '''Test check_architectures() (missing)'''
        self.set_test_snap_yaml("architectures", None)
        c = SnapReviewLint(self.test_name)
        c.check_architectures()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architectures_all(self):
        '''Test check_architectures() (all)'''
        self.set_test_snap_yaml("architectures", ["all"])
        c = SnapReviewLint(self.test_name)
        c.check_architectures()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architectures_single_armhf(self):
        '''Test check_architectures() (single arch, armhf)'''
        self.set_test_snap_yaml("architectures", ["armhf"])
        c = SnapReviewLint(self.test_name)
        c.check_architectures()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architectures_single_arm64(self):
        '''Test check_architectures() (single arch, arm64)'''
        self.set_test_snap_yaml("architectures", ["arm64"])
        c = SnapReviewLint(self.test_name)
        c.check_architectures()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architectures_single_i386(self):
        '''Test check_architectures() (single arch, i386)'''
        self.set_test_snap_yaml("architectures", ["i386"])
        c = SnapReviewLint(self.test_name)
        c.check_architectures()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architectures_single_amd64(self):
        '''Test check_architectures() (single arch, amd64)'''
        self.set_test_snap_yaml("architectures", ["amd64"])
        c = SnapReviewLint(self.test_name)
        c.check_architectures()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architectures_single_s390x(self):
        '''Test check_architectures() (single arch, s390x)'''
        self.set_test_snap_yaml("architectures", ["s390x"])
        c = SnapReviewLint(self.test_name)
        c.check_architectures()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architectures_single_ppc64el(self):
        '''Test check_architectures() (single arch, ppc64el)'''
        self.set_test_snap_yaml("architectures", ["ppc64el"])
        c = SnapReviewLint(self.test_name)
        c.check_architectures()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architectures_single_nonexistent(self):
        '''Test check_architectures() (single nonexistent arch)'''
        self.set_test_snap_yaml("architectures", ["nonexistent"])
        c = SnapReviewLint(self.test_name)
        c.check_architectures()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snappy_valid_arch_multi(self):
        '''Test check_architectures() (valid multi)'''
        self.set_test_snap_yaml("architectures", ["amd64", "armhf"])
        c = SnapReviewLint(self.test_name)
        c.check_architectures()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snappy_valid_arch_multi2(self):
        '''Test check_architectures() (valid multi2)'''
        self.set_test_snap_yaml("architectures", ["armhf", "arm64", "i386"])
        c = SnapReviewLint(self.test_name)
        c.check_architectures()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_unknown_entries(self):
        '''Test check_unknown_entries - none'''
        c = SnapReviewLint(self.test_name)
        c.check_unknown_entries()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_unknown_entries2(self):
        '''Test check_unknown_entries - one'''
        self.set_test_snap_yaml("nonexistent", "bar")
        c = SnapReviewLint(self.test_name)
        c.check_unknown_entries()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_config(self):
        '''Test check_config()'''
        c = SnapReviewLint(self.test_name)
        self.set_test_unpack_dir("/nonexistent")
        c.pkg_files.append(os.path.join(c._get_unpack_dir(),
                           'meta/hooks/config'))
        c.check_config()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_config_nonexecutable(self):
        '''Test check_config() - not executable'''
        c = SnapReviewLint(self.test_name)
        self.set_test_unpack_dir("/nonexistent.nonexec")
        c.pkg_files.append(os.path.join(c._get_unpack_dir(),
                           'meta/hooks/config'))
        c.check_config()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_description(self):
        '''Test check_description'''
        self.set_test_snap_yaml("description", "This is a test description")
        c = SnapReviewLint(self.test_name)
        c.check_description()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_description_missing(self):
        '''Test check_description - not present'''
        self.set_test_snap_yaml("description", None)
        c = SnapReviewLint(self.test_name)
        c.check_description()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_description_bad(self):
        '''Test check_description - short'''
        self.set_test_snap_yaml("description", "a")
        c = SnapReviewLint(self.test_name)
        c.check_description()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_description_bad2(self):
        '''Test check_description - empty'''
        self.set_test_snap_yaml("description", "")
        c = SnapReviewLint(self.test_name)
        c.check_description()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_description_bad3(self):
        '''Test check_description - list'''
        self.set_test_snap_yaml("description", [])
        c = SnapReviewLint(self.test_name)
        c.check_description()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_license_agreement(self):
        '''Test check_license_agreement'''
        self.set_test_snap_yaml("license-agreement",
                                "This is a test license_agreement")
        c = SnapReviewLint(self.test_name)
        c.check_license_agreement()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_license_agreement_missing(self):
        '''Test check_license_agreement - not present'''
        self.set_test_snap_yaml("license-agreement", None)
        c = SnapReviewLint(self.test_name)
        c.check_license_agreement()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_license_agreement_bad(self):
        '''Test check_license_agreement - empty'''
        self.set_test_snap_yaml("license-agreement", "")
        c = SnapReviewLint(self.test_name)
        c.check_license_agreement()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_license_agreement_bad2(self):
        '''Test check_license_agreement - list'''
        self.set_test_snap_yaml("license-agreement", [])
        c = SnapReviewLint(self.test_name)
        c.check_license_agreement()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_license_version(self):
        '''Test check_license_version'''
        self.set_test_snap_yaml("license-version",
                                "This is a test license_version")
        c = SnapReviewLint(self.test_name)
        c.check_license_version()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_license_version_missing(self):
        '''Test check_license_version - not present'''
        self.set_test_snap_yaml("license-version", None)
        c = SnapReviewLint(self.test_name)
        c.check_license_version()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_license_version_bad(self):
        '''Test check_license_version - empty'''
        self.set_test_snap_yaml("license-version", "")
        c = SnapReviewLint(self.test_name)
        c.check_license_version()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_license_version_bad2(self):
        '''Test check_license_version - list'''
        self.set_test_snap_yaml("license-version", [])
        c = SnapReviewLint(self.test_name)
        c.check_license_version()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_summary(self):
        '''Test check_summary'''
        self.set_test_snap_yaml("summary", "This is a test summary")
        c = SnapReviewLint(self.test_name)
        c.check_summary()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_summary_missing(self):
        '''Test check_summary - not present'''
        self.set_test_snap_yaml("summary", None)
        c = SnapReviewLint(self.test_name)
        c.check_summary()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_summary_bad(self):
        '''Test check_summary - short'''
        self.set_test_snap_yaml("summary", "a")
        c = SnapReviewLint(self.test_name)
        c.check_summary()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_summary_bad2(self):
        '''Test check_summary - empty'''
        self.set_test_snap_yaml("summary", "")
        c = SnapReviewLint(self.test_name)
        c.check_summary()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_summary_bad3(self):
        '''Test check_summary - list'''
        self.set_test_snap_yaml("summary", [])
        c = SnapReviewLint(self.test_name)
        c.check_summary()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_one_command(self):
        '''Test check_apps() - one command'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/foo"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': 5, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_one_command_with_caps(self):
        '''Test check_apps() - one command'''
        self.set_test_snap_yaml("apps", {"Fo0-Bar": {"command": "bin/foo"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': 5, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_one_daemon(self):
        '''Test check_apps() - one daemon'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/foo",
                                                 "daemon": "single"},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': 5, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_two_commands(self):
        '''Test check_apps() - two commands'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/foo"},
                                         "bar": {"command": "bin/bar"},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': 8, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_command_plus_daemon(self):
        '''Test check_apps() - command and daemon'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/foo"},
                                         "bar": {"command": "bin/bar",
                                                 "daemon": "single"},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': 8, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_two_daemons(self):
        '''Test check_apps() - command and daemon'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/foo",
                                                 "daemon": "single"},
                                         "bar": {"command": "bin/bar",
                                                 "daemon": "single"},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': 8, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_missing(self):
        '''Test check_apps() - missing'''
        self.set_test_snap_yaml("apps", None)
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_bad(self):
        '''Test check_apps() - bad'''
        self.set_test_snap_yaml("apps", [])
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_bad2(self):
        '''Test check_apps() - empty'''
        self.set_test_snap_yaml("apps", {})
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_bad3(self):
        '''Test check_apps() - missing command'''
        self.set_test_snap_yaml("apps", {"foo": {"daemon": "single"},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_bad4(self):
        '''Test check_apps() - unknown field'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/foo",
                                                 "nonexistent": "abc"},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_bad5(self):
        '''Test check_apps() - invalid field'''
        self.set_test_snap_yaml("apps", {"foo": []})
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_bad6(self):
        '''Test check_apps() - empty fields'''
        self.set_test_snap_yaml("apps", {"foo": {}})
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_bad7(self):
        '''Test check_apps() - unknown field (bus-name)'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/foo",
                                                 "bus-name": "foo"},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_bad8(self):
        '''Test check_apps() - bad name with .'''
        self.set_test_snap_yaml("apps", {"foo.bar": {"command": "bin/foo"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_bad9(self):
        '''Test check_apps() - bad name with _'''
        self.set_test_snap_yaml("apps", {"foo_bar": {"command": "bin/foo"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_command(self):
        '''Test check_apps_command()'''
        cmd = "bin/foo"
        self.set_test_snap_yaml("apps", {"foo": {"command": cmd},
                                         })
        c = SnapReviewLint(self.test_name)
        c.pkg_files.append(os.path.join('/fake', cmd))
        c.check_apps_command()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_command_dotslash(self):
        '''Test check_apps_command() - starts with ./'''
        cmd = "bin/foo"
        self.set_test_snap_yaml("apps", {"foo": {"command": "./" + cmd},
                                         })
        c = SnapReviewLint(self.test_name)
        c.pkg_files.append(os.path.join('/fake', cmd))
        c.check_apps_command()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_command_missing(self):
        '''Test check_apps_command() - missing'''
        self.set_test_snap_yaml("apps", {"foo": {}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_command()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_command_empty(self):
        '''Test check_apps_command() - empty'''
        self.set_test_snap_yaml("apps", {"foo": {"command": ""},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_command()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_command_invalid(self):
        '''Test check_apps_command() - list'''
        self.set_test_snap_yaml("apps", {"foo": {"command": []},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_command()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_command_nonexistent(self):
        '''Test check_apps_command() - nonexistent'''
        cmd = "bin/foo"
        self.set_test_snap_yaml("apps", {"foo": {"command": cmd},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_command()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_command(self):
        '''Test check_apps_stop_command()'''
        cmd = "bin/foo"
        self.set_test_snap_yaml("apps", {"foo": {"stop-command": cmd},
                                         })
        c = SnapReviewLint(self.test_name)
        c.pkg_files.append(os.path.join('/fake', cmd))
        c.check_apps_stop_command()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_command_missing(self):
        '''Test check_apps_stop_command() - missing'''
        self.set_test_snap_yaml("apps", {"foo": {}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_command()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_command_empty(self):
        '''Test check_apps_stop_command() - empty'''
        self.set_test_snap_yaml("apps", {"foo": {"stop-command": ""},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_command()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_command_invalid(self):
        '''Test check_apps_stop_command() - list'''
        self.set_test_snap_yaml("apps", {"foo": {"stop-command": []},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_command()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_command_nonexistent(self):
        '''Test check_apps_stop_command() - nonexistent'''
        cmd = "bin/foo"
        self.set_test_snap_yaml("apps", {"foo": {"stop-command": cmd},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_command()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_post_stop_command(self):
        '''Test check_apps_post_stop_command()'''
        cmd = "bin/foo"
        self.set_test_snap_yaml("apps", {"foo": {"post-stop-command": cmd},
                                         })
        c = SnapReviewLint(self.test_name)
        c.pkg_files.append(os.path.join('/fake', cmd))
        c.check_apps_post_stop_command()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_post_stop_command_missing(self):
        '''Test check_apps_post_stop_command() - missing'''
        self.set_test_snap_yaml("apps", {"foo": {}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_post_stop_command()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_post_stop_command_empty(self):
        '''Test check_apps_post_stop_command() - empty'''
        self.set_test_snap_yaml("apps", {"foo": {"post-stop-command": ""},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_post_stop_command()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_post_stop_command_invalid(self):
        '''Test check_apps_post_stop_command() - list'''
        self.set_test_snap_yaml("apps", {"foo": {"post-stop-command": []},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_post_stop_command()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_post_stop_command_nonexistent(self):
        '''Test check_apps_post_stop_command() - nonexistent'''
        cmd = "bin/foo"
        self.set_test_snap_yaml("apps", {"foo": {"post-stop-command": cmd},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_post_stop_command()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_daemon_simple(self):
        '''Test check_apps_daemon() - simple'''
        entry = "simple"
        self.set_test_snap_yaml("apps", {"foo": {"daemon": entry}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_daemon()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_daemon_forking(self):
        '''Test check_apps_daemon() - forking'''
        entry = "forking"
        self.set_test_snap_yaml("apps", {"foo": {"daemon": entry}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_daemon()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_daemon_oneshot(self):
        '''Test check_apps_daemon() - oneshot'''
        entry = "oneshot"
        self.set_test_snap_yaml("apps", {"foo": {"daemon": entry}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_daemon()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_daemon_dbus(self):
        '''Test check_apps_daemon() - dbus'''
        entry = "dbus"
        self.set_test_snap_yaml("apps", {"foo": {"daemon": entry}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_daemon()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_daemon_missing(self):
        '''Test check_apps_daemon() - missing'''
        self.set_test_snap_yaml("apps", {"foo": {}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_daemon()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_daemon_empty(self):
        '''Test check_apps_daemon() - empty'''
        self.set_test_snap_yaml("apps", {"foo": {"daemon": ""},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_daemon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_daemon_invalid(self):
        '''Test check_apps_daemon() - list'''
        self.set_test_snap_yaml("apps", {"foo": {"daemon": []},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_daemon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_daemon_nonexistent(self):
        '''Test check_apps_daemon() - nonexistent'''
        entry = "nonexistent"
        self.set_test_snap_yaml("apps", {"foo": {"daemon": entry}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_daemon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_nondaemon(self):
        '''Test check_apps_nondaemon()'''
        entry = "simple"
        self.set_test_snap_yaml("apps", {"foo": {"daemon": entry,
                                                 "stop-command": "bin/bar"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_nondaemon()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_nondaemon_command(self):
        '''Test check_apps_nondaemon() - command'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/bar"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_nondaemon()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_nondaemon_plugs(self):
        '''Test check_apps_nondaemon() - plugs'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/bar",
                                                 "plugs": {}}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_nondaemon()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_nondaemon_stop(self):
        '''Test check_apps_nondaemon() - stop'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/bar",
                                                 "stop-command": "bin/bar"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_nondaemon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_nondaemon_stop_timeout(self):
        '''Test check_apps_nondaemon() - stop-timeout'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/bar",
                                                 "stop-timeout": 60}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_nondaemon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_nondaemon_restart_condition(self):
        '''Test check_apps_nondaemon() - restart-condition'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/bar",
                                                 "restart-condition":
                                                 "never"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_nondaemon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_nondaemon_post_stop_command(self):
        '''Test check_apps_nondaemon() - post-stop-command'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/bar",
                                                 "post-stop-command": "bin/bar"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_nondaemon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_nondaemon_ports(self):
        '''Test check_apps_nondaemon() - ports'''
        ports = self._create_ports()
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/bar",
                                                 "ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_nondaemon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_nondaemon_socket(self):
        '''Test check_apps_nondaemon() - socket'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/bar",
                                                 "socket": True}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_nondaemon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_nondaemon_listen_stream(self):
        '''Test check_apps_nondaemon() - listen-stream'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/bar",
                                                 "listen-stream": "@bar"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_nondaemon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_nondaemon_socket_user(self):
        '''Test check_apps_nondaemon() - socket-user'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/bar",
                                                 "socket-user": "docker"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_nondaemon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_nondaemon_socket_group(self):
        '''Test check_apps_nondaemon() - socket-group'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/bar",
                                                 "socket-group": "docker"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_nondaemon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_restart_condition_always(self):
        '''Test check_apps_restart-condition() - always'''
        entry = "always"
        self.set_test_snap_yaml("apps", {"foo": {"restart-condition": entry}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_restart_condition()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_restart_condition_never(self):
        '''Test check_apps_restart-condition() - never'''
        entry = "never"
        self.set_test_snap_yaml("apps", {"foo": {"restart-condition": entry}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_restart_condition()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_restart_condition_on_abnormal(self):
        '''Test check_apps_restart-condition() - on-abnormal'''
        entry = "on-abnormal"
        self.set_test_snap_yaml("apps", {"foo": {"restart-condition": entry}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_restart_condition()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_restart_condition_on_abort(self):
        '''Test check_apps_restart-condition() - on-abort'''
        entry = "on-abort"
        self.set_test_snap_yaml("apps", {"foo": {"restart-condition": entry}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_restart_condition()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_restart_condition_on_failure(self):
        '''Test check_apps_restart-condition() - on-failure'''
        entry = "on-failure"
        self.set_test_snap_yaml("apps", {"foo": {"restart-condition": entry}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_restart_condition()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_restart_condition_on_success(self):
        '''Test check_apps_restart-condition() - on-success'''
        entry = "on-success"
        self.set_test_snap_yaml("apps", {"foo": {"restart-condition": entry}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_restart_condition()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_restart_condition_missing(self):
        '''Test check_apps_restart-condition() - missing'''
        self.set_test_snap_yaml("apps", {"foo": {}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_restart_condition()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_restart_condition_empty(self):
        '''Test check_apps_restart-condition() - empty'''
        self.set_test_snap_yaml("apps", {"foo": {"restart-condition": ""},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_restart_condition()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_restart_condition_invalid(self):
        '''Test check_apps_restart-condition() - list'''
        self.set_test_snap_yaml("apps", {"foo": {"restart-condition": []},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_restart_condition()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_restart_condition_nonexistent(self):
        '''Test check_apps_restart-condition() - nonexistent'''
        entry = "nonexistent"
        self.set_test_snap_yaml("apps", {"foo": {"restart-condition": entry}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_restart_condition()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_ports(self):
        '''Test check_apps_ports()'''
        ports = self._create_ports()
        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': 7, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_internal(self):
        '''Test check_apps_ports() - internal'''
        ports = self._create_ports()
        del ports['external']
        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': 3, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_external(self):
        '''Test check_apps_ports() - external'''
        ports = self._create_ports()
        del ports['internal']
        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': 5, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_empty(self):
        '''Test check_apps_ports() - empty'''
        self.set_test_snap_yaml("apps", {"bar": {"ports": {}}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_invalid(self):
        '''Test check_apps_ports() - invalid'''
        self.set_test_snap_yaml("apps", {"bar": {"ports": []}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_bad_key(self):
        '''Test check_apps_ports() - bad key'''
        ports = self._create_ports()
        ports['xternal'] = ports['external']
        del ports['external']

        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_missing_internal(self):
        '''Test check_apps_ports() - missing internal'''
        ports = self._create_ports()
        del ports['internal']['int1']

        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_missing_external(self):
        '''Test check_apps_ports() - missing external'''
        ports = self._create_ports()
        del ports['external']['ext1']
        del ports['external']['ext2']

        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_missing_external_subkey(self):
        '''Test check_apps_ports() - missing external subkey'''
        ports = self._create_ports()
        del ports['external']['ext2']['port']

        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_missing_internal_subkey(self):
        '''Test check_apps_ports() - missing internal subkey'''
        ports = self._create_ports()
        del ports['internal']['int1']['port']
        del ports['internal']['int1']['negotiable']

        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_missing_internal_port_subkey(self):
        '''Test check_apps_ports() - missing internal port subkey'''
        ports = self._create_ports()
        del ports['internal']['int1']['port']

        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': 7, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_invalid_internal_subkey(self):
        '''Test check_apps_ports() - invalid internal subkey'''
        ports = self._create_ports()
        ports['internal']['int1']['prt'] = ports['internal']['int1']['port']

        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_invalid_internal_port(self):
        '''Test check_apps_ports() - invalid internal port'''
        ports = self._create_ports()
        ports['internal']['int1']['port'] = "bad/8080"

        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_invalid_external_port(self):
        '''Test check_apps_ports() - invalid external port'''
        ports = self._create_ports()
        ports['external']['ext2']['port'] = []

        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_invalid_internal_low_port(self):
        '''Test check_apps_ports() - invalid internal low port'''
        ports = self._create_ports()
        ports['internal']['int1']['port'] = "0/tcp"

        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_invalid_internal_high_port(self):
        '''Test check_apps_ports() - invalid internal high port'''
        ports = self._create_ports()
        ports['internal']['int1']['port'] = "65536/tcp"

        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_invalid_internal_negotiable(self):
        '''Test check_apps_ports() - invalid internal negotiable'''
        ports = self._create_ports()
        ports['internal']['int1']['negotiable'] = -99999999

        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_ports_invalid_internal_negotiable2(self):
        '''Test check_apps_ports() - invalid internal negotiable'''
        ports = self._create_ports()
        ports['internal']['int1']['negotiable'] = []

        self.set_test_snap_yaml("apps", {"bar": {"ports": ports}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_ports()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_timeout(self):
        '''Test check_apps_stop_timeout()'''
        self.set_test_snap_yaml("apps", {"bar": {"stop-timeout": 30}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_timeout()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_timeout_nonexistent(self):
        '''Test check_apps_stop_timeout_nonexistent()'''
        self.set_test_snap_yaml("apps", {"bar": {}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_timeout()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_timeout_granularity(self):
        '''Test check_apps_stop_timeout()'''
        self.set_test_snap_yaml("apps", {"bar": {"stop-timeout": '30s'}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_timeout()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_timeout_empty(self):
        '''Test check_apps_stop_timeout() - empty'''
        self.set_test_snap_yaml("apps", {"bar": {"stop-timeout": ''}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_timeout()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_timeout_bad(self):
        '''Test check_apps_stop_timeout() - bad'''
        self.set_test_snap_yaml("apps", {"bar": {"stop-timeout": 'a'}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_timeout()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_timeout_bad2(self):
        '''Test check_apps_stop_timeout() - bad (list)'''
        self.set_test_snap_yaml("apps", {"bar": {"stop-timeout": []}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_timeout()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_timeout_bad_granularity(self):
        '''Test check_apps_stop_timeout() - bad with granularity'''
        self.set_test_snap_yaml("apps", {"bar": {"stop-timeout": '30a'}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_timeout()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_timeout_range_low(self):
        '''Test check_apps_stop_timeout() - out of range (low)'''
        self.set_test_snap_yaml("apps", {"bar": {"stop-timeout": -1}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_timeout()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_timeout_range_high(self):
        '''Test check_apps_stop_timeout() - out of range (high)'''
        self.set_test_snap_yaml("apps", {"bar": {"stop-timeout": 61}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_timeout()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_socket(self):
        '''Test check_apps_socket()'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"socket": True,
                                                 "listen-stream":
                                                 "@%s" % name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_listen_stream_path(self):
        '''Test check_apps_listen_stream() - path'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"listen-stream":
                                                 "/tmp/%s" % name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_listen_stream()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_socket_no_listen_stream(self):
        '''Test check_apps_socket() - missing listen-stream'''
        self.set_test_snap_yaml("apps", {"bar": {"socket": True}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_socket_bad(self):
        '''Test check_apps_socket() - bad'''
        self.set_test_snap_yaml("apps", {"bar": {"socket": ""}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_socket_nonexistent(self):
        '''Test check_apps_socket() - nonexistent'''
        self.set_test_snap_yaml("apps", {"bar": {}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_listen_stream_abspkgname(self):
        '''Test check_apps_listen_stream() - @pkgname'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"listen-stream":
                                                 "@%s" % name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_listen_stream()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_listen_stream_abspkgname2(self):
        '''Test check_apps_listen_stream() - @pkgname_'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"listen-stream":
                                                 "@%s_something" % name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_listen_stream()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_listen_stream_nonexistent(self):
        '''Test check_apps_listen_stream() - nonexistent'''
        self.set_test_snap_yaml("apps", {"bar": {}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_listen_stream()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_listen_stream_bad(self):
        '''Test check_apps_listen_stream() - bad (list)'''
        self.set_test_snap_yaml("apps", {"bar": {"listen-stream": []}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_listen_stream()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_listen_stream_bad_abstract(self):
        '''Test check_apps_listen_stream() - bad (wrong name)'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"listen-stream":
                                                 "@%s/nomatch" % name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_listen_stream()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_listen_stream_bad_relative(self):
        '''Test check_apps_listen_stream() - bad (not / or @)'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"listen-stream": name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_listen_stream()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_listen_stream_bad_path(self):
        '''Test check_apps_listen_stream() - bad path'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"listen-stream":
                                                 "/var/log/%s" % name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_listen_stream()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_listen_stream_empty(self):
        '''Test check_apps_listen_stream() - empty'''
        self.set_test_snap_yaml("apps", {"bar": {"listen-stream": ""}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_listen_stream()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_socket_user(self):
        '''Test check_apps_socket_user()'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"socket-user": name,
                                                 "listen-stream":
                                                 "@%s" % name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket_user()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_socket_user_no_listen_stream(self):
        '''Test check_apps_socket_user() - missing listen-stream'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"socket-user": name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket_user()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_socket_user_bad(self):
        '''Test check_apps_socket_user() - bad user'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"socket-user": name + "-no",
                                                 "listen-stream":
                                                 "@%s" % name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket_user()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 2}
        self.check_results(r, expected_counts)

    def test_check_apps_socket_user_bad2(self):
        '''Test check_apps_socket_user() - bad (list)'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"socket-user": [],
                                                 "listen-stream":
                                                 "@%s" % name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket_user()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_socket_user_empty(self):
        '''Test check_apps_socket_user() - empty'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"socket-user": "",
                                                 "listen-stream":
                                                 "@%s" % name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket_user()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_socket_user_nonexistent(self):
        '''Test check_apps_socket_user() - nonexistent'''
        self.set_test_snap_yaml("apps", {"bar": {}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket_user()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_socket_group(self):
        '''Test check_apps_socket_group()'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"socket-group": name,
                                                 "listen-stream":
                                                 "@%s" % name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket_group()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_socket_group_no_listen_stream(self):
        '''Test check_apps_socket_group() - missing listen-stream'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"socket-group": name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket_group()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_socket_group_bad(self):
        '''Test check_apps_socket_group() - bad group'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"socket-group": name + "-no",
                                                 "listen-stream":
                                                 "@%s" % name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket_group()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 2}
        self.check_results(r, expected_counts)

    def test_check_apps_socket_group_bad2(self):
        '''Test check_apps_socket_group() - bad (list)'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"socket-group": [],
                                                 "listen-stream":
                                                 "@%s" % name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket_group()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_socket_group_empty(self):
        '''Test check_apps_socket_group() - empty'''
        name = self.test_snap_yaml['name']
        self.set_test_snap_yaml("apps", {"bar": {"socket-group": "",
                                                 "listen-stream":
                                                 "@%s" % name}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket_group()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_socket_group_nonexistent(self):
        '''Test check_apps_socket_group() - nonexistent'''
        self.set_test_snap_yaml("apps", {"bar": {}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_socket_group()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_plugs(self):
        '''Test check_plugs()'''
        plugs = self._create_top_plugs()
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': 8, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_plugs_bad_interface(self):
        '''Test check_plugs() - bad interface (list)'''
        plugs = {'iface-caps': {'interface': [],
                                'caps': ['network']}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_plugs_empty_interface(self):
        '''Test check_plugs() - empty interface'''
        plugs = {'iface-caps': {'interface': "",
                                'caps': ['network']}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_plugs_unspecified_interface(self):
        '''Test check_plugs() - unspecified interface'''
        plugs = {'bool-file': {'path': '/path/to/some/where'}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': 3, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_plugs_unknown_interface(self):
        '''Test check_plugs() - interface (unknown)'''
        plugs = {'iface-caps': {'interface': 'nonexistent',
                                'caps': ['network']}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_plugs_unknown_interface_old_security(self):
        '''Test check_plugs() - interface (old-security)'''
        plugs = {'iface-caps': {'interface': 'old-security',
                                'caps': ['network']}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_plugs_unspecified_unknown_interface(self):
        '''Test check_plugs() - unspecified interface (unknown)'''
        plugs = {'nonexistent': {'caps': ['network']}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_plugs_missing_attrib(self):
        '''Test check_plugs() - missing attrib'''
        plugs = {'bool-file': {}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_plugs_missing_attrib_explicit_interface(self):
        '''Test check_plugs() - missing attrib'''
        plugs = {'test': {'interface': 'bool-file'}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_plugs_unknown_attrib(self):
        '''Test check_plugs() - unknown attrib'''
        plugs = {'test': {'interface': 'bool-file',
                          'nonexistent': 'abc'}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_plugs_bad_attrib_caps(self):
        '''Test check_plugs() - bad attrib - bool-file'''
        plugs = {'test': {'interface': 'bool-file',
                          'path': ['invalid']}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_plugs(self):
        '''Test check_apps_plugs()'''
        plugs = self._create_top_plugs()
        apps_plugs = self._create_apps_plugs()
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("apps", apps_plugs)
        c = SnapReviewLint(self.test_name)
        c.check_apps_plugs()
        r = c.click_report
        expected_counts = {'info': 8, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_no_plugs(self):
        '''Test check_apps_plugs() - no plugs'''
        plugs = self._create_top_plugs()
        apps_plugs = {'bar': {'command': 'bin/bar'}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("apps", apps_plugs)
        c = SnapReviewLint(self.test_name)
        c.check_apps_plugs()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_plugs_bad(self):
        '''Test check_apps_plugs() - bad (dict)'''
        plugs = self._create_top_plugs()
        apps_plugs = {'bar': {'plugs': {}}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("apps", apps_plugs)
        c = SnapReviewLint(self.test_name)
        c.check_apps_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_plugs_empty(self):
        '''Test check_apps_plugs() - empty'''
        plugs = self._create_top_plugs()
        apps_plugs = {'bar': {'plugs': []}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("apps", apps_plugs)
        c = SnapReviewLint(self.test_name)
        c.check_apps_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_plugs_bad_entry(self):
        '''Test check_apps_plugs() - bad entry (dict)'''
        plugs = self._create_top_plugs()
        apps_plugs = {'bar': {'plugs': [{}]}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("apps", apps_plugs)
        c = SnapReviewLint(self.test_name)
        c.check_apps_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_plugs_unknown_entry(self):
        '''Test check_apps_plugs() - unknown'''
        plugs = self._create_top_plugs()
        apps_plugs = {'bar': {'plugs': ['nonexistent']}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("apps", apps_plugs)
        c = SnapReviewLint(self.test_name)
        c.check_apps_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots(self):
        '''Test check_slots()'''
        slots = self._create_top_slots()
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': 4, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_slots_bad_interface(self):
        '''Test check_slots() - bad interface (list)'''
        slots = {'iface-caps': {'interface': [],
                                'caps': ['network']}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_empty_interface(self):
        '''Test check_slots() - empty interface'''
        slots = {'iface-caps': {'interface': "",
                                'caps': ['network']}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_unspecified_interface(self):
        '''Test check_slots() - unspecified interface'''
        slots = {'bool-file': {'path': '/path/to/some/where'}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': 3, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_slots_unknown_interface(self):
        '''Test check_slots() - interface (unknown)'''
        slots = {'iface-caps': {'interface': 'nonexistent',
                                'caps': ['network']}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_unknown_interface_old_security(self):
        '''Test check_slots() - interface (old-security)'''
        slots = {'iface-caps': {'interface': 'old-security',
                                'caps': ['network']}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_unspecified_unknown_interface(self):
        '''Test check_slots() - unspecified interface (unknown)'''
        slots = {'nonexistent': {'caps': ['network']}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_missing_attrib(self):
        '''Test check_slots() - missing attrib'''
        slots = {'bool-file': {}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_missing_attrib_explicit_interface(self):
        '''Test check_slots() - missing attrib'''
        slots = {'test': {'interface': 'bool-file'}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_unknown_attrib(self):
        '''Test check_slots() - unknown attrib'''
        slots = {'test': {'interface': 'bool-file',
                          'nonexistent': 'abc'}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_bad_attrib_caps(self):
        '''Test check_slots() - bad attrib - bool-file'''
        slots = {'test': {'interface': 'bool-file',
                          'path': ['invalid']}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_slots(self):
        '''Test check_apps_slots()'''
        slots = self._create_top_slots()
        self.set_test_snap_yaml("slots", slots)
        apps_slots = self._create_apps_slots()
        self.set_test_snap_yaml("apps", apps_slots)
        c = SnapReviewLint(self.test_name)
        c.check_apps_slots()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_no_slots(self):
        '''Test check_apps_slots() - no slots'''
        slots = self._create_top_slots()
        apps_slots = {'bar': {'command': 'bin/bar'}}
        self.set_test_snap_yaml("slots", slots)
        self.set_test_snap_yaml("apps", apps_slots)
        c = SnapReviewLint(self.test_name)
        c.check_apps_slots()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_slots_bad(self):
        '''Test check_apps_slots() - bad (dict)'''
        slots = self._create_top_slots()
        apps_slots = {'bar': {'slots': {}}}
        self.set_test_snap_yaml("slots", slots)
        self.set_test_snap_yaml("apps", apps_slots)
        c = SnapReviewLint(self.test_name)
        c.check_apps_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_slots_empty(self):
        '''Test check_apps_slots() - empty'''
        slots = self._create_top_slots()
        apps_slots = {'bar': {'slots': []}}
        self.set_test_snap_yaml("slots", slots)
        self.set_test_snap_yaml("apps", apps_slots)
        c = SnapReviewLint(self.test_name)
        c.check_apps_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_slots_bad_entry(self):
        '''Test check_apps_slots() - bad entry (dict)'''
        slots = self._create_top_slots()
        apps_slots = {'bar': {'slots': [{}]}}
        self.set_test_snap_yaml("slots", slots)
        self.set_test_snap_yaml("apps", apps_slots)
        c = SnapReviewLint(self.test_name)
        c.check_apps_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_slots_unknown_entry(self):
        '''Test check_apps_slots() - unknown'''
        slots = self._create_top_slots()
        apps_slots = {'bar': {'slots': ['nonexistent']}}
        self.set_test_snap_yaml("slots", slots)
        self.set_test_snap_yaml("apps", apps_slots)
        c = SnapReviewLint(self.test_name)
        c.check_apps_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)


class TestSnapReviewLintNoMock(TestCase):
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

    def test_check_external_symlinks(self):
        '''Test check_external_symlinks()'''
        package = utils.make_snap2(output_dir=self.mkdtemp())
        c = SnapReviewLint(package)
        c.check_external_symlinks()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_external_symlinks_has_symlink(self):
        '''Test check_external_symlinks() - has symlink'''
        package = utils.make_snap2(output_dir=self.mkdtemp(),
                                   extra_files=['/some/where,outside']
                                   )
        c = SnapReviewLint(package)
        c.check_external_symlinks()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_external_symlinks_type_kernel(self):
        '''Test check_external_symlinks() - type kernel'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: test
version: 0.1
summary: some thing
description: some desc
architectures: [ amd64 ]
type: kernel
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=['%s:meta/snap.yaml' % path,
                                                '/some/where,outside']
                                   )
        c = SnapReviewLint(package)
        c.check_external_symlinks()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_external_symlinks_has_symlink_gadget(self):
        '''Test check_external_symlinks() - has symlink (gadget)'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: test
version: 0.1
summary: some thing
description: some desc
type: gadget
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=['%s:meta/snap.yaml' % path,
                                                '/some/where,outside']
                                   )
        c = SnapReviewLint(package)
        c.check_external_symlinks()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_external_symlinks_os(self):
        '''Test check_external_symlinks() - os'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: test
version: 0.1
summary: some thing
description: some desc
type: os
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=['%s:meta/snap.yaml' % path]
                                   )
        c = SnapReviewLint(package)
        c.check_external_symlinks()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architecture_all(self):
        '''Test check_architecture_all()'''
        package = utils.make_snap2(output_dir=self.mkdtemp())
        c = SnapReviewLint(package)
        c.check_architecture_all()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architecture_all_amd64(self):
        '''Test check_architecture_all() - amd64'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: test
version: 0.1
summary: some thing
description: some desc
architectures: [ amd64 ]
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=['%s:meta/snap.yaml' % path]
                                   )
        c = SnapReviewLint(package)
        c.check_architecture_all()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architecture_all_has_binary(self):
        '''Test check_architecture_all() - has binary'''
        package = utils.make_snap2(output_dir=self.mkdtemp(),
                                   extra_files=['/bin/ls:ls']
                                   )
        c = SnapReviewLint(package)
        c.check_architecture_all()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_architecture_specified_needed_has_binary(self):
        '''Test check_architecture_specified_needed() - has binary'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: test
version: 0.1
summary: some thing
description: some desc
architectures: [ amd64 ]
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=['%s:meta/snap.yaml' % path,
                                                '/bin/ls:ls'
                                                ]
                                   )
        c = SnapReviewLint(package)
        c.check_architecture_specified_needed()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architecture_specified_needed(self):
        '''Test check_architecture_specified_needed()'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: test
version: 0.1
summary: some thing
description: some desc
architectures: [ amd64 ]
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=['%s:meta/snap.yaml' % path]
                                   )
        c = SnapReviewLint(package)
        c.check_architecture_specified_needed()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_vcs(self):
        '''Test check_vcs()'''
        package = utils.make_snap2(output_dir=self.mkdtemp())
        c = SnapReviewLint(package)
        c.check_vcs()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_vcs_bzrignore(self):
        '''Test check_vcs() - .bzrignore'''
        package = utils.make_snap2(output_dir=self.mkdtemp(),
                                   extra_files=['.bzrignore']
                                   )
        c = SnapReviewLint(package)
        c.check_vcs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)