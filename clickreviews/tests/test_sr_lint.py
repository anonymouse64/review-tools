'''test_sr_lint.py: tests for the sr_lint module'''
#
# Copyright (C) 2013-2018 Canonical Ltd.
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
import platform
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
        plugs = {'iface-content': {'interface': 'content',
                                   'target': '/path/to/something'},
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
                 'app4': {'plugs': ['iface-content']},
                 }
        return plugs

    def _create_top_slots(self):
        slots = {'iface-bool-file': {'interface': 'bool-file',
                                     'path': '/path/to/something'},
                 'iface-content': {'interface': 'content',
                                   'read': ['/path/to/somewhere'],
                                   'write': ['/path/to/somewhere/else']},
                 'iface-content-modern': {'interface': 'content',
                                          'source': {'read': ['$SNAP/a',
                                                              '$SNAP/b',
                                                              ],
                                                     'write': ['$SNAP/c'],
                                                     },
                                          },
                 'iface-serial-port': {'interface': 'serial-port',
                                       'path': '/path/to/something'},
                 }
        return slots

    def _create_apps_slots(self):
        slots = {'app1': {'slots': ['iface-bool-file']},
                 'app2': {'slots': ['iface-content']},
                 'app3': {'slots': ['iface-serial-port']},
                 }
        return slots

    def _create_manifest_yaml(self):
        m = {}
        for i in "name", "version", "description", "summary":
            m[i] = self.test_snap_yaml[i]
        m['build-packages'] = []
        m['build-snaps'] = []
        m['image-info'] = {}
        m['parts'] = {
            'mypart': {
                'build-packages': [],
                'installed-packages': [],
                'installed-snaps': [],
                'plugin': 'nil',
                'prime': [],
                'stage': [],
                'stage-packages': [],
                'uname': 'Linux',
            }
        }

        return m

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

    def test_check_name_toplevel_startswith_number(self):
        '''Test check_name - toplevel starts with number'''
        self.set_test_snap_yaml("name", "01game")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_name_toplevel_maxlen_for_store(self):
        '''Test check_name - toplevel maxlen for store'''
        self.set_test_snap_yaml("name", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa40chars")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_name_toplevel_minlen_for_store(self):
        '''Test check_name - toplevel minlen for store'''
        self.set_test_snap_yaml("name", "aa")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_name_toplevel_too_long_for_store(self):
        '''Test check_name - toplevel too long for store'''
        self.set_test_snap_yaml("name", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa41chars")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:name_valid'
        expected['error'][name] = {"text": "malformed 'name': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa41chars' (length '41' exceeds store limit '40')"}
        self.check_results(r, expected=expected)

    def test_check_name_toplevel_too_short_for_store(self):
        '''Test check_name - toplevel too short for store'''
        self.set_test_snap_yaml("name", "a")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:name_valid'
        expected['error'][name] = {"text": "malformed 'name': 'a' (length '1' below store limit '2')"}
        self.check_results(r, expected=expected)

    def test_check_name_toplevel_efficient(self):
        '''Test check_name - toplevel is efficient'''
        self.set_test_snap_yaml("name", "u-94903713687486543234157734673284536758")
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
        '''Test check_name - bad - ?'''
        self.set_test_snap_yaml("name", "foo?bar")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_name_bad1(self):
        '''Test check_name - bad - /'''
        self.set_test_snap_yaml("name", "foo/bar")
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

    def test_check_name_bad5(self):
        '''Test check_name - bad - --'''
        self.set_test_snap_yaml("name", "foo--bar")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_name_bad6(self):
        '''Test check_name - bad - endswith -'''
        self.set_test_snap_yaml("name", "foo-bar-")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_name_bad6b(self):
        '''Test check_name - bad - startswith -'''
        self.set_test_snap_yaml("name", "-foo-bar")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_name_bad7(self):
        '''Test check_name - bad - cap'''
        self.set_test_snap_yaml("name", "foo-Bar")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_name_bad8(self):
        '''Test check_name - bad - all numbers'''
        self.set_test_snap_yaml("name", "01")
        c = SnapReviewLint(self.test_name)
        c.check_name()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_name_bad9(self):
        '''Test check_name - bad - all numbers and dashes'''
        self.set_test_snap_yaml("name", "0-1")
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

    def test_check_version_bad5(self):
        '''Test check_version - too long'''
        self.set_test_snap_yaml("version", "1.0.20160315-alpha2-git.c6fadc4+test1")
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

    def test_check_type_redflagged_snapd(self):
        '''Test check_type_redflagged - snapd'''
        self.set_test_snap_yaml("type", "snapd")
        c = SnapReviewLint(self.test_name)
        c.check_type_redflagged()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('snap_type_redflag')
        self.check_manual_review(r, name)

    def test_check_type_redflagged_os_whitelisted_core(self):
        '''Test check_type_redflagged - os (core)'''
        self.set_test_snap_yaml("type", "os")
        self.set_test_snap_yaml("name", "core")
        c = SnapReviewLint(self.test_name)
        c.check_type_redflagged()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:snap_type_redflag'
        expected['info'][name] = {"text": "OK (override 'core' for 'type: os')"}
        self.check_results(r, expected=expected)

    def test_check_type_redflagged_os_whitelisted_ubuntu_core(self):
        '''Test check_type_redflagged - os (ubuntu-core)'''
        self.set_test_snap_yaml("type", "os")
        self.set_test_snap_yaml("name", "ubuntu-core")
        c = SnapReviewLint(self.test_name)
        c.check_type_redflagged()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:snap_type_redflag'
        expected['info'][name] = {"text": "OK (override 'ubuntu-core' for 'type: os')"}
        self.check_results(r, expected=expected)

    def test_check_type_redflagged_kernel_whitelisted(self):
        '''Test check_type_redflagged - kernel'''
        self.set_test_snap_yaml("type", "kernel")
        self.set_test_snap_yaml("name", "pc-kernel")
        c = SnapReviewLint(self.test_name)
        c.check_type_redflagged()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:snap_type_redflag'
        expected['info'][name] = {"text": "OK (override 'pc-kernel' for 'type: kernel')"}
        self.check_results(r, expected=expected)

    def test_check_type_redflagged_gadget_whitelisted(self):
        '''Test check_type_redflagged - gadget'''
        self.set_test_snap_yaml("type", "gadget")
        self.set_test_snap_yaml("name", "pc")
        c = SnapReviewLint(self.test_name)
        c.check_type_redflagged()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:snap_type_redflag'
        expected['info'][name] = {"text": "OK (override 'pc' for 'type: gadget')"}
        self.check_results(r, expected=expected)

    def test_check_type_redflagged_snapd_whitelisted(self):
        '''Test check_type_redflagged - snapd whitelisted'''
        self.set_test_snap_yaml("type", "snapd")
        self.set_test_snap_yaml("name", "snapd")
        c = SnapReviewLint(self.test_name)
        c.check_type_redflagged()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:snap_type_redflag'
        expected['info'][name] = {"text": "OK (override 'snapd' for 'type: snapd')"}
        self.check_results(r, expected=expected)

    def test_check_type_redflagged_base(self):
        '''Test check_type_redflagged - base'''
        self.set_test_snap_yaml("type", "base")
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

    def test_check_architectures_bad_entry(self):
        '''Test check_architectures() - bad (dict)'''
        self.set_test_snap_yaml("architectures", [{}])
        c = SnapReviewLint(self.test_name)
        c.check_architectures()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_assumes_missing(self):
        '''Test check_assumes() - missing'''
        self.set_test_snap_yaml("assumes", None)
        c = SnapReviewLint(self.test_name)
        c.check_assumes()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_assumes_empty(self):
        '''Test check_assumes() - empty'''
        self.set_test_snap_yaml("assumes", [])
        c = SnapReviewLint(self.test_name)
        c.check_assumes()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_assumes_bad(self):
        '''Test check_assumes() - bad'''
        self.set_test_snap_yaml("assumes", {})
        c = SnapReviewLint(self.test_name)
        c.check_assumes()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_assumes_bad_entry(self):
        '''Test check_assumes() - bad entry'''
        self.set_test_snap_yaml("assumes", [{}])
        c = SnapReviewLint(self.test_name)
        c.check_assumes()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_assumes(self):
        '''Test check_assumes()'''
        self.set_test_snap_yaml("assumes", ['name', 'version'])
        c = SnapReviewLint(self.test_name)
        c.check_assumes()
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

    def test_check_apps_one_command_capitalized(self):
        '''Test check_apps() - one command (capitalized)'''
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

    def test_check_apps_bad10(self):
        '''Test check_apps() - bad name with /'''
        self.set_test_snap_yaml("apps", {"foo/bar": {"command": "bin/foo"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_bad11(self):
        '''Test check_apps() - bad name ends with -'''
        self.set_test_snap_yaml("apps", {"foo-bar-": {"command": "bin/foo"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_bad12(self):
        '''Test check_apps() - bad name with --'''
        self.set_test_snap_yaml("apps", {"foo--bar": {"command": "bin/foo"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_hooks_one_entry(self):
        '''Test check_hooks() - one entry'''
        self.set_test_snap_yaml("hooks", {"foo": {}})
        c = SnapReviewLint(self.test_name)
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': 4, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_one_entry_capitalized(self):
        '''Test check_hooks() - one entry (capitalized)'''
        self.set_test_snap_yaml("hooks", {"Fo0-Bar": {}})
        c = SnapReviewLint(self.test_name)
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': 4, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_two_entries(self):
        '''Test check_hooks() - two entries'''
        self.set_test_snap_yaml("hooks", {"foo": {},
                                          "bar": {},
                                          })
        c = SnapReviewLint(self.test_name)
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': 6, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_missing(self):
        '''Test check_hooks() - missing'''
        self.set_test_snap_yaml("hooks", None)
        c = SnapReviewLint(self.test_name)
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_bad(self):
        '''Test check_hooks() - bad'''
        self.set_test_snap_yaml("hooks", [])
        c = SnapReviewLint(self.test_name)
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_hooks_bad1(self):
        '''Test check_hooks() - empty'''
        self.set_test_snap_yaml("hooks", {})
        c = SnapReviewLint(self.test_name)
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_hooks_nokeys(self):
        '''Test check_hooks() - no keys'''
        hooks_plugs = {'bar1': None}
        self.set_test_snap_yaml("hooks", hooks_plugs)
        c = SnapReviewLint(self.test_name)
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': 3, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_bad2(self):
        '''Test check_hooks() - unknown field'''
        self.set_test_snap_yaml("hooks", {"foo": {"nonexistent": "abc"}})
        c = SnapReviewLint(self.test_name)
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_bad3(self):
        '''Test check_hooks() - invalid field'''
        self.set_test_snap_yaml("hooks", {"foo": []})
        c = SnapReviewLint(self.test_name)
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_hooks_bad4(self):
        '''Test check_hooks() - bad name with .'''
        self.set_test_snap_yaml("hooks", {"foo.bar": {}})
        c = SnapReviewLint(self.test_name)
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_hooks_bad5(self):
        '''Test check_hooks() - bad name with _'''
        self.set_test_snap_yaml("hooks", {"foo_bar": {}})
        c = SnapReviewLint(self.test_name)
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_hooks_bad6(self):
        '''Test check_hooks() - bad name with /'''
        self.set_test_snap_yaml("hooks", {"foo/bar": {}})
        c = SnapReviewLint(self.test_name)
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_hooks_bad7(self):
        '''Test check_hooks() - bad name ends with -'''
        self.set_test_snap_yaml("hooks", {"foo-bar-": {}})
        c = SnapReviewLint(self.test_name)
        c.check_hooks()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_hooks_bad8(self):
        '''Test check_hooks() - bad name with --'''
        self.set_test_snap_yaml("hooks", {"foo--bar": {}})
        c = SnapReviewLint(self.test_name)
        c.check_hooks()
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

    def test_check_apps_one_command_with_args(self):
        '''Test check_apps() - one command with args'''
        cmd = "bin/foo"
        self.set_test_snap_yaml("apps", {"foo": {"command": "%s -c bar" % cmd}})
        c = SnapReviewLint(self.test_name)
        c.pkg_files.append(os.path.join('/fake', cmd))
        c.check_apps_command()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_one_command_with_space(self):
        '''Test check_apps() - one command with space'''
        cmd = "bin/foo bar"
        self.set_test_snap_yaml("apps", {"foo": {"command": "'%s'" % cmd}})
        c = SnapReviewLint(self.test_name)
        c.pkg_files.append(os.path.join('/fake', cmd))
        c.check_apps_command()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_one_command_with_space_with_args(self):
        '''Test check_apps() - one command with space with args'''
        cmd = "bin/foo bar"
        self.set_test_snap_yaml("apps", {"foo": {"command": "'%s' -c foo" % cmd}})
        c = SnapReviewLint(self.test_name)
        c.pkg_files.append(os.path.join('/fake', cmd))
        c.check_apps_command()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_one_command_with_unmatched_startquote(self):
        '''Test check_apps() - one command with unmatched startquote'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "'bin/foo bar"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_command()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_one_command_with_unmatched_midquote(self):
        '''Test check_apps() - one command with unmatched midquote'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/foo'bar"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_command()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_completer(self):
        '''Test check_apps_completer()'''
        cmd = "bin/foo"
        self.set_test_snap_yaml("apps", {"foo": {"completer": cmd},
                                         })
        c = SnapReviewLint(self.test_name)
        c.pkg_files.append(os.path.join('/fake', cmd))
        c.check_apps_completer()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_completer_dotslash(self):
        '''Test check_apps_completer() - starts with ./'''
        cmd = "bin/foo"
        self.set_test_snap_yaml("apps", {"foo": {"completer": "./" + cmd},
                                         })
        c = SnapReviewLint(self.test_name)
        c.pkg_files.append(os.path.join('/fake', cmd))
        c.check_apps_completer()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_completer_missing(self):
        '''Test check_apps_completer() - missing'''
        self.set_test_snap_yaml("apps", {"foo": {}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_completer()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_completer_empty(self):
        '''Test check_apps_completer() - empty'''
        self.set_test_snap_yaml("apps", {"foo": {"completer": ""},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_completer()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_completer_invalid(self):
        '''Test check_apps_completer() - list'''
        self.set_test_snap_yaml("apps", {"foo": {"completer": []},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_completer()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_completer_nonexistent(self):
        '''Test check_apps_completer() - nonexistent'''
        cmd = "bin/foo"
        self.set_test_snap_yaml("apps", {"foo": {"completer": cmd},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_completer()
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

    def test_check_apps_reload_command(self):
        '''Test check_apps_reload_command()'''
        cmd = "bin/foo"
        self.set_test_snap_yaml("apps", {"foo": {"reload-command": cmd},
                                         })
        c = SnapReviewLint(self.test_name)
        c.pkg_files.append(os.path.join('/fake', cmd))
        c.check_apps_reload_command()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_reload_command_missing(self):
        '''Test check_apps_reload_command() - missing'''
        self.set_test_snap_yaml("apps", {"foo": {}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_reload_command()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_reload_command_empty(self):
        '''Test check_apps_reload_command() - empty'''
        self.set_test_snap_yaml("apps", {"foo": {"reload-command": ""},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_reload_command()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_reload_command_invalid(self):
        '''Test check_apps_reload_command() - list'''
        self.set_test_snap_yaml("apps", {"foo": {"reload-command": []},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_reload_command()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_reload_command_nonexistent(self):
        '''Test check_apps_reload_command() - nonexistent'''
        cmd = "bin/foo"
        self.set_test_snap_yaml("apps", {"foo": {"reload-command": cmd},
                                         })
        c = SnapReviewLint(self.test_name)
        c.check_apps_reload_command()
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

    def test_check_apps_daemon_notify(self):
        '''Test check_apps_daemon() - notify'''
        entry = "notify"
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
                                                 "stop-timeout": 59}})
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

    def test_check_apps_nondaemon_refresh_mode(self):
        '''Test check_apps_nondaemon() - refresh-mode'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/bar",
                                                 "refresh-mode": "endure"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_nondaemon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_nondaemon_stop_mode(self):
        '''Test check_apps_nondaemon() - stop-mode'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/bar",
                                                 "stop-mode": "sigterm"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_nondaemon()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_nondaemon_timer(self):
        '''Test check_apps_nondaemon() - timer'''
        self.set_test_snap_yaml("apps", {"foo": {"command": "bin/bar",
                                                 "timer": "0:00-24:00/96"}})
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

    def test_check_apps_stop_timeout_granularity_ms(self):
        '''Test check_apps_stop_timeout() - ms'''
        self.set_test_snap_yaml("apps", {"bar": {"stop-timeout": '30ms'}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_timeout()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_timeout_granularity_m(self):
        '''Test check_apps_stop_timeout() - m'''
        self.set_test_snap_yaml("apps", {"bar": {"stop-timeout": '30m'}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_timeout()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_timeout_granularity_ns(self):
        '''Test check_apps_stop_timeout() - ns'''
        self.set_test_snap_yaml("apps", {"bar": {"stop-timeout": '30ns'}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_timeout()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_timeout_granularity_us(self):
        '''Test check_apps_stop_timeout() - us'''
        self.set_test_snap_yaml("apps", {"bar": {"stop-timeout": '30us'}})
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
        plugs = {'iface-bad': {'interface': []}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_plugs_empty_interface(self):
        '''Test check_plugs() - empty interface'''
        plugs = {'iface-empty': {'interface': ""}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_plugs_unspecified_interface(self):
        '''Test check_plugs() - unspecified interface'''
        plugs = {'content': {'target': '/path/to/some/where'}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': 3, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_plugs_unknown_interface(self):
        '''Test check_plugs() - interface (unknown)'''
        plugs = {'iface-unknown': {'interface': 'nonexistent'}}
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

    def test_check_plugs_unknown_attrib(self):
        '''Test check_plugs() - unknown attrib'''
        plugs = {'test': {'interface': 'content',
                          'target': 'foo',
                          'nonexistent': 'abc'}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_plugs_bad_attrib_content(self):
        '''Test check_plugs() - bad attrib - content'''
        plugs = {'test': {'interface': 'content',
                          'target': ['invalid']}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_plugs_wrong_attrib_content(self):
        '''Test check_plugs() - content (used slot attrib with plug)'''
        plugs = {'test': {'interface': 'content',
                          'target': 'foo',
                          'read': '/path/to/something'}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_plugs_browser_support_bad(self):
        '''Test check_plugs() - browser-support bad attribute'''
        plugs = {'test': {'interface': 'browser-support',
                          'allow-sandbox': 'Y'}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': None, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_plugs_abbreviated(self):
        '''Test check_plugs() - abbreviated'''
        self.set_test_snap_yaml("plugs", {'nm': 'network-manager'})
        c = SnapReviewLint(self.test_name)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
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

    def test_check_hooks_plugs(self):
        '''Test check_hooks_plugs()'''
        plugs = self._create_top_plugs()
        hooks_plugs = self._create_apps_plugs()
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("hooks", hooks_plugs)
        c = SnapReviewLint(self.test_name)
        c.check_hooks_plugs()
        r = c.click_report
        expected_counts = {'info': 8, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_no_plugs(self):
        '''Test check_hooks_plugs() - no plugs'''
        plugs = self._create_top_plugs()
        hooks_plugs = {'bar': {}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("hooks", hooks_plugs)
        c = SnapReviewLint(self.test_name)
        c.check_hooks_plugs()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_hooks_plugs_bad(self):
        '''Test check_hooks_plugs() - bad (dict)'''
        plugs = self._create_top_plugs()
        hooks_plugs = {'bar': {'plugs': {}}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("hooks", hooks_plugs)
        c = SnapReviewLint(self.test_name)
        c.check_hooks_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_hooks_plugs_empty(self):
        '''Test check_hooks_plugs() - empty'''
        plugs = self._create_top_plugs()
        hooks_plugs = {'bar': {'plugs': []}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("hooks", hooks_plugs)
        c = SnapReviewLint(self.test_name)
        c.check_hooks_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_hooks_plugs_bad_entry(self):
        '''Test check_hooks_plugs() - bad entry (dict)'''
        plugs = self._create_top_plugs()
        hooks_plugs = {'bar': {'plugs': [{}]}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("hooks", hooks_plugs)
        c = SnapReviewLint(self.test_name)
        c.check_hooks_plugs()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_hooks_plugs_unknown_entry(self):
        '''Test check_hooks_plugs() - unknown'''
        plugs = self._create_top_plugs()
        hooks_plugs = {'bar': {'plugs': ['nonexistent']}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("hooks", hooks_plugs)
        c = SnapReviewLint(self.test_name)
        c.check_hooks_plugs()
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
        expected_counts = {'info': 16, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_slots_bad_interface(self):
        '''Test check_slots() - bad interface (list)'''
        slots = {'iface-bad': {'interface': []}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_empty_interface(self):
        '''Test check_slots() - empty interface'''
        slots = {'iface-empty': {'interface': ""}}
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

    def test_check_slots_wrong_attrib_content(self):
        '''Test check_slots() - content (used plug attrib with slot)'''
        slots = {'test': {'interface': 'content',
                          'read': ['lib0'],
                          'target': '/path/to/something'}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_wrong_attrib_content_source_with_read(self):
        '''Test check_slots() - content (used 'source' with 'read')'''
        slots = {'test': {'interface': 'content',
                          'read': ['lib0'],
                          'source': {'read': ['$SNAP/a']}}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_wrong_attrib_content_source_with_write(self):
        '''Test check_slots() - content (used 'source' with 'write')'''
        slots = {'test': {'interface': 'content',
                          'write': ['lib0'],
                          'source': {'write': ['$SNAP/a']}}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_content_legacy(self):
        '''Test check_slots() - content (legacy)'''
        slots = {'test': {'interface': 'content',
                          'write': ['lib0']}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_interface_content_slot_source()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_slots_content_source_read(self):
        '''Test check_slots() - content (source read)'''
        slots = {'test': {'interface': 'content',
                          'source': {'read': ['$SNAP/a']}}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_interface_content_slot_source()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_slots_content_source_write(self):
        '''Test check_slots() - content (source write)'''
        slots = {'test': {'interface': 'content',
                          'source': {'write': ['$SNAP/a']}}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_interface_content_slot_source()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_slots_content_source_read_write(self):
        '''Test check_slots() - content (source read and write)'''
        # mpris just for testing it is ignored
        slots = {'mpris': {'interface': 'mpris'},
                 'test': {'interface': 'content',
                          'source': {'read': ['$SNAP/a',
                                              '$SNAP/b'],
                                     'write': ['$SNAP/c',
                                               '$SNAP/d']}}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_interface_content_slot_source()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_slots_content_source_bad(self):
        '''Test check_slots() - content (source bad)'''
        slots = {'test': {'interface': 'content',
                          'source': []}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_interface_content_slot_source()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_content_source_unknown(self):
        '''Test check_slots() - content (source unknown)'''
        slots = {'test': {'interface': 'content',
                          'source': {'unknown': ['$SNAP/a']}}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_interface_content_slot_source()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_content_source_bad_read(self):
        '''Test check_slots() - content (bad read)'''
        slots = {'test': {'interface': 'content',
                          'source': {'read': {}}}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_interface_content_slot_source()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_content_source_bad_read_value(self):
        '''Test check_slots() - content (bad read)'''
        slots = {'test': {'interface': 'content',
                          'source': {'read': [{}]}}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_interface_content_slot_source()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_content_source_read_in_write(self):
        '''Test check_slots() - content (read in write)'''
        slots = {'test': {'interface': 'content',
                          'source': {'read': ['$SNAP/a',
                                              '$SNAP/b'],
                                     'write': ['$SNAP/c',
                                               '$SNAP/b']}}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_interface_content_slot_source()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_gpio(self):
        '''Test check_slots() - gpio'''
        slots = {'test': {'interface': 'gpio',
                          'number': 65}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': 4, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_slots_gpio_bad(self):
        '''Test check_slots() - gpio - bad (string)'''
        slots = {'test': {'interface': 'gpio',
                          'number': 'a4'}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_serial_port_path(self):
        '''Test check_slots() - serial-port - path'''
        slots = {'test': {'interface': 'serial-port',
                          'path': '/dev/ttyS0'}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': 4, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_slots_serial_port_usb(self):
        '''Test check_slots() - serial-port - usb'''
        slots = {'test': {'interface': 'serial-port',
                          'usb-vendor': 0xdeadbeef,
                          'usb-product': 0x01234567,
                          'path': 'serial-port-foo'}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': 6, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_slots_serial_port_missing(self):
        '''Test check_slots() - serial-port - missing'''
        slots = {'test': {'interface': 'serial-port'}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_serial_port_usb_misspelled(self):
        '''Test check_slots() - serial-port - usb'''
        slots = {'test': {'interface': 'serial-port',
                          'usb-vend0r': 0xdeadbeef,
                          'usb-product': 0x01234567,
                          'path': 'serial-port-foo'}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 2}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:slots_required_attributes:test'
        expected['error'][name] = {"text": "missing required slots attributes for interface 'serial-port' (path, path/usb-vendor/usb-product)"}
        name = 'lint-snap-v2:slots_attributes:test:usb-vend0r'
        expected['error'][name] = {"text": "unknown attribute 'usb-vend0r' for interface 'serial-port' (slots)"}
        self.check_results(r, expected=expected)

    def test_check_slots_unknown_interface(self):
        '''Test check_slots() - interface (unknown)'''
        slots = {'iface-unknown': {'interface': 'nonexistent'}}
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

    def test_check_slots_unknown_attrib(self):
        '''Test check_slots() - unknown attrib'''
        slots = {'test': {'interface': 'bool-file',
                          'path': '/path/to/some/where',
                          'nonexistent': 'abc'}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_bad_attrib_boolfile(self):
        '''Test check_slots() - bad attrib - bool-file'''
        slots = {'test': {'interface': 'bool-file',
                          'path': ['invalid']}}
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_slots_abbreviated(self):
        '''Test check_slots() - abbreviated'''
        self.set_test_snap_yaml("slots", {'nm': 'network-manager'})
        c = SnapReviewLint(self.test_name)
        c.check_slots()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
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
        expected_counts = {'info': 6, 'warn': 0, 'error': 0}
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

    def test_check_epoch_simple(self):
        '''Test check_epoch - simple integer'''
        self.set_test_snap_yaml("epoch", 2)
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_epoch_simple_transition(self):
        '''Test check_epoch - simple transition'''
        self.set_test_snap_yaml("epoch", "3*")
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_epoch_simple_zero(self):
        '''Test check_epoch - simple 0'''
        self.set_test_snap_yaml("epoch", 0)
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_epoch_simple_bad(self):
        '''Test check_epoch - string'''
        self.set_test_snap_yaml("epoch", "abc")
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_epoch_simple_bad_negative(self):
        '''Test check_epoch - negative'''
        self.set_test_snap_yaml("epoch", -1)
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_epoch_simple_bad_negative_transition(self):
        '''Test check_epoch - negative transition'''
        self.set_test_snap_yaml("epoch", "-1*")
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_epoch_simple_bad_decimal(self):
        '''Test check_epoch - decimal'''
        self.set_test_snap_yaml("epoch", 1.01)
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_epoch_full_empty(self):
        '''Test check_epoch - full - empty'''
        self.set_test_snap_yaml("epoch", {})
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_epoch_full_unknown(self):
        '''Test check_epoch - full - unknown'''
        self.set_test_snap_yaml("epoch", {'bad': [1]})
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_epoch_full_read(self):
        '''Test check_epoch - full read'''
        self.set_test_snap_yaml("epoch", {'read': [3, 4, 5]})
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_epoch_full_read_zero(self):
        '''Test check_epoch - zero'''
        self.set_test_snap_yaml("epoch", {'read': [0, 1]})
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_epoch_full_read_bad_transition(self):
        '''Test check_epoch - bad full read (transition)'''
        self.set_test_snap_yaml("epoch", {'read': ["3*"]})
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_epoch_full_read_bad_int(self):
        '''Test check_epoch - bad full read - int'''
        self.set_test_snap_yaml("epoch", {'read': 3})
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_epoch_full_read_bad_negative(self):
        '''Test check_epoch - bad full read - negative'''
        self.set_test_snap_yaml("epoch", {'read': [1, -2, 3]})
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_epoch_full_write(self):
        '''Test check_epoch - full write'''
        self.set_test_snap_yaml("epoch", {'write': [3, 4, 5]})
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_epoch_full_write_bad_transition(self):
        '''Test check_epoch - bad full write (transition)'''
        self.set_test_snap_yaml("epoch", {'write': ["3*"]})
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_epoch_full_write_bad_int(self):
        '''Test check_epoch - bad full write - int'''
        self.set_test_snap_yaml("epoch", {'write': 3})
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_epoch_full_read_write(self):
        '''Test check_epoch - full read/write'''
        self.set_test_snap_yaml("epoch", {'read': [3, 4, 5],
                                          'write': [4, 5]})
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_epoch_full_read_write_bad_transition(self):
        '''Test check_epoch - bad full read/write (transition)'''
        self.set_test_snap_yaml("epoch", {'read': [3, 4, 5],
                                          'write': ["3*"]})
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_epoch_full_read_write_bad_int(self):
        '''Test check_epoch - bad full read/write - int'''
        self.set_test_snap_yaml("epoch", {'read': 3,
                                          'write': [4, 5]})
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_epoch_missing(self):
        '''Test check_epoch - not present'''
        self.set_test_snap_yaml("epoch", None)
        c = SnapReviewLint(self.test_name)
        c.check_epoch()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_confinement_strict(self):
        '''Test check_confinement - strict'''
        self.set_test_snap_yaml("confinement", "strict")
        c = SnapReviewLint(self.test_name)
        c.check_confinement()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:confinement_valid'
        expected['info'][name] = {"text": "OK"}
        self.check_results(r, expected=expected)

    def test_check_confinement_devmode(self):
        '''Test check_confinement - devmode'''
        self.set_test_snap_yaml("confinement", "devmode")
        c = SnapReviewLint(self.test_name)
        c.check_confinement()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_confinement_classic(self):
        '''Test check_confinement - classic'''
        self.set_test_snap_yaml("confinement", "classic")
        c = SnapReviewLint(self.test_name)
        c.check_confinement()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:confinement_classic'
        expected['error'][name] = {"text": "(NEEDS REVIEW) confinement 'classic' not allowed. If your snap needs classic confinement to function, please make a request for this snap to use classic by creating a new topic in the forum using the 'store' category and detail the technical reasons why classic is required."}
        self.check_results(r, expected=expected)

    def test_check_confinement_classic_allowed(self):
        '''Test check_confinement - classic'''
        self.set_test_snap_yaml("confinement", "classic")
        overrides = {
            'snap_allow_classic': True
        }

        c = SnapReviewLint(self.test_name, overrides=overrides)
        c.check_confinement()
        r = c.click_report
        expected_counts = {'info': 3, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:confinement_classic'
        expected['info'][name] = {"text": "OK (confinement 'classic' allowed)"}
        self.check_results(r, expected=expected)

    def test_check_confinement_classic_with_plugs(self):
        '''Test check_confinement - classic'''
        self.set_test_snap_yaml("confinement", "classic")
        overrides = {
            'snap_allow_classic': True
        }
        self.set_test_snap_yaml("plugs", {})

        c = SnapReviewLint(self.test_name, overrides=overrides)
        c.check_confinement()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:confinement_classic_with_interfaces'
        expected['error'][name] = {"text": "confinement 'classic' not allowed with plugs/slots"}
        self.check_results(r, expected=expected)

    def test_check_confinement_classic_with_slots(self):
        '''Test check_confinement - classic'''
        self.set_test_snap_yaml("confinement", "classic")
        overrides = {
            'snap_allow_classic': True
        }
        self.set_test_snap_yaml("slots", {})

        c = SnapReviewLint(self.test_name, overrides=overrides)
        c.check_confinement()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:confinement_classic_with_interfaces'
        expected['error'][name] = {"text": "confinement 'classic' not allowed with plugs/slots"}
        self.check_results(r, expected=expected)

    def test_check_confinement_classic_with_app_plugs(self):
        '''Test check_confinement - classic'''
        self.set_test_snap_yaml("confinement", "classic")
        overrides = {
            'snap_allow_classic': True
        }

        apps_plugs = {'bar': {'plugs': []}}
        self.set_test_snap_yaml("apps", apps_plugs)

        c = SnapReviewLint(self.test_name, overrides=overrides)
        c.check_confinement()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:confinement_classic_with_interfaces'
        expected['error'][name] = {"text": "confinement 'classic' not allowed with plugs/slots"}
        self.check_results(r, expected=expected)

    def test_check_confinement_os(self):
        '''Test check_confinement - os'''
        self.set_test_snap_yaml("confinement", "strict")
        self.set_test_snap_yaml("type", "os")
        c = SnapReviewLint(self.test_name)
        c.check_confinement()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:confinement_valid'
        expected['info'][name] = {"text": "'confinement' should not be used with 'type: os'"}
        self.check_results(r, expected=expected)

    def test_check_confinement_kernel(self):
        '''Test check_confinement - kernel'''
        self.set_test_snap_yaml("confinement", "strict")
        self.set_test_snap_yaml("type", "kernel")
        c = SnapReviewLint(self.test_name)
        c.check_confinement()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:confinement_valid'
        expected['info'][name] = {"text": "OK"}
        self.check_results(r, expected=expected)

    def test_check_confinement_gadget(self):
        '''Test check_confinement - gadget'''
        self.set_test_snap_yaml("confinement", "strict")
        self.set_test_snap_yaml("type", "gadget")
        c = SnapReviewLint(self.test_name)
        c.check_confinement()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:confinement_valid'
        expected['info'][name] = {"text": "OK"}
        self.check_results(r, expected=expected)

    def test_check_confinement_missing(self):
        '''Test check_confinement - missing'''
        self.set_test_snap_yaml("confinement", None)
        c = SnapReviewLint(self.test_name)
        c.check_confinement()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_confinement_nonexistent(self):
        '''Test check_confinement - nonexistent'''
        self.set_test_snap_yaml("confinement", "nonexistent")
        c = SnapReviewLint(self.test_name)
        c.check_confinement()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_confinement_bad(self):
        '''Test check_confinement - bad (boolean)'''
        self.set_test_snap_yaml("confinement", True)
        c = SnapReviewLint(self.test_name)
        c.check_confinement()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_confinement_bad2(self):
        '''Test check_confinement - bad (yaml true)'''
        self.set_test_snap_yaml("confinement", 'true')
        c = SnapReviewLint(self.test_name)
        c.check_confinement()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_grade_stable(self):
        '''Test check_grade - stable'''
        self.set_test_snap_yaml("grade", "stable")
        c = SnapReviewLint(self.test_name)
        c.check_grade()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = {
            'error': {},
            'warn': {},
            'info': {
                'lint-snap-v2:grade_valid': {
                    "text": "OK"
                },
            },
        }
        self.check_results(r, expected=expected)

    def test_check_grade_devel(self):
        '''Test check_grade - devel'''
        self.set_test_snap_yaml("grade", "devel")
        c = SnapReviewLint(self.test_name)
        c.check_grade()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_grade_os(self):
        '''Test check_grade - os'''
        self.set_test_snap_yaml("grade", "stable")
        self.set_test_snap_yaml("type", "os")
        c = SnapReviewLint(self.test_name)
        c.check_grade()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = {
            'error': {},
            'warn': {},
            'info': {
                'lint-snap-v2:grade_valid': {
                    "text": "OK"
                },
            },
        }
        self.check_results(r, expected=expected)

    def test_check_grade_kernel(self):
        '''Test check_grade - kernel'''
        self.set_test_snap_yaml("grade", "stable")
        self.set_test_snap_yaml("type", "kernel")
        c = SnapReviewLint(self.test_name)
        c.check_grade()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = {
            'error': {},
            'warn': {},
            'info': {
                'lint-snap-v2:grade_valid': {
                    "text": "OK"
                },
            },
        }
        self.check_results(r, expected=expected)

    def test_check_grade_gadget(self):
        '''Test check_grade - gadget'''
        self.set_test_snap_yaml("grade", "stable")
        self.set_test_snap_yaml("type", "gadget")
        c = SnapReviewLint(self.test_name)
        c.check_grade()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = {
            'error': {},
            'warn': {},
            'info': {
                'lint-snap-v2:grade_valid': {
                    "text": "OK"
                },
            },
        }
        self.check_results(r, expected=expected)

    def test_check_grade_missing(self):
        '''Test check_grade - missing'''
        self.set_test_snap_yaml("grade", None)
        c = SnapReviewLint(self.test_name)
        c.check_grade()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_grade_nonexistent(self):
        '''Test check_grade - nonexistent'''
        self.set_test_snap_yaml("grade", "nonexistent")
        c = SnapReviewLint(self.test_name)
        c.check_grade()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_grade_bad_booleans(self):
        '''Test check_grade - bad booleans values'''
        bad_values = (
            True,
            'true',
        )
        for v in bad_values:
            self.set_test_snap_yaml("grade", v)
            c = SnapReviewLint(self.test_name)
            c.check_grade()
            r = c.click_report
            expected_counts = {'info': None, 'warn': 0, 'error': 1}
            self.check_results(r, expected_counts)

    def test_check_base(self):
        '''Test check_base'''
        self.set_test_snap_yaml("base", "bare")
        c = SnapReviewLint(self.test_name)
        c.check_base()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = {
            'error': {},
            'warn': {},
            'info': {
                'lint-snap-v2:base_valid': {
                    "text": "OK"
                },
            },
        }
        self.check_results(r, expected=expected)

    def test_check_base_bad(self):
        '''Test check_base - bad values'''
        bad_values = (
            True,
            [],
        )
        for v in bad_values:
            self.set_test_snap_yaml("base", v)
            c = SnapReviewLint(self.test_name)
            c.check_base()
            r = c.click_report
            expected_counts = {'info': None, 'warn': 0, 'error': 1}
            self.check_results(r, expected_counts)

    def test_check_base_missing(self):
        '''Test check_base - missing'''
        self.set_test_snap_yaml("base", None)
        c = SnapReviewLint(self.test_name)
        c.check_base()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_base_with_invalid_type(self):
        '''Test check_grade - kernel'''
        bad_types = (
            "base",
            "core",
            "kernel",
            "os",
        )
        for v in bad_types:
            self.set_test_snap_yaml("base", "bare")
            self.set_test_snap_yaml("type", v)
            c = SnapReviewLint(self.test_name)
            c.check_base()
            r = c.click_report

            expected = {
                'info': {},
                'warn': {},
                'error': {
                    'lint-snap-v2:base_valid': {
                        "text": "'base' should not be used with 'type: %s'" % v
                    },
                },
            }
        self.check_results(r, expected=expected)

    def test_check_base_interfaces_none(self):
        '''Test check_base_interfaces - no plugs or slots'''
        self.set_test_snap_yaml("type", "base")
        c = SnapReviewLint(self.test_name)
        c.check_base_interfaces()
        r = c.click_report
        expected_counts = {'info': 4, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_base_interfaces_top(self):
        '''Test check_base_interfaces - top plugs and slots'''
        self.set_test_snap_yaml("type", "base")
        plugs = self._create_top_plugs()
        self.set_test_snap_yaml("plugs", plugs)
        slots = self._create_top_slots()
        self.set_test_snap_yaml("slots", slots)
        c = SnapReviewLint(self.test_name)
        c.check_base_interfaces()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 2}
        self.check_results(r, expected_counts)

    def test_check_base_interfaces_apps_plugs(self):
        '''Test check_base_interfaces - apps plugs'''
        self.set_test_snap_yaml("type", "base")
        apps_plugs = self._create_apps_plugs()
        self.set_test_snap_yaml("apps", apps_plugs)
        c = SnapReviewLint(self.test_name)
        c.check_base_interfaces()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 4}
        self.check_results(r, expected_counts)

    def test_check_base_interfaces_apps_slots(self):
        '''Test check_base_interfaces - apps slots'''
        self.set_test_snap_yaml("type", "base")
        apps_slots = self._create_apps_slots()
        self.set_test_snap_yaml("apps", apps_slots)
        c = SnapReviewLint(self.test_name)
        c.check_base_interfaces()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 3}
        self.check_results(r, expected_counts)

    def test_check_environment(self):
        '''Test check_environment'''
        env = {'ENV1': "value",
               'ENV2': "value2",
               'ENV3': 1,
               'ENV4': 1.2,
               }
        self.set_test_snap_yaml("environment", env)
        c = SnapReviewLint(self.test_name)
        c.check_environment()
        r = c.click_report
        expected_counts = {'info': 9, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_environment(self):
        '''Test check_environment'''
        env = {'ENV1': "value",
               'ENV2': "value2",
               }
        apps = {'app1': {'environment': env},
                'app2': {'environment': env},
                'app3': {'environment': env},
                'app4': {'environment': env},
                }

        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewLint(self.test_name)
        c.check_apps_environment()
        r = c.click_report
        expected_counts = {'info': 20, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_environment_bad_equal(self):
        '''Test check_environment - bad - ='''
        env = {'ENV1=': "value",
               }
        self.set_test_snap_yaml("environment", env)
        c = SnapReviewLint(self.test_name)
        c.check_environment()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_environment_bad_null(self):
        '''Test check_environment - bad - \0'''
        env = {'E\0NV1': "value",
               }
        self.set_test_snap_yaml("environment", env)
        c = SnapReviewLint(self.test_name)
        c.check_environment()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_environment_not_portable(self):
        '''Test check_environment - not portable: starts with number'''
        env = {'1ENV': "value",
               }
        self.set_test_snap_yaml("environment", env)
        c = SnapReviewLint(self.test_name)
        c.check_environment()
        r = c.click_report
        expected_counts = {'info': 3, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_environment_not_portable2(self):
        '''Test check_environment - not portable - lower case'''
        env = {'EnV1': "value",
               }
        self.set_test_snap_yaml("environment", env)
        c = SnapReviewLint(self.test_name)
        c.check_environment()
        r = c.click_report
        expected_counts = {'info': 3, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_environment_unusual(self):
        '''Test check_environment - unusual'''
        env = {'En:V1': "value",
               }
        self.set_test_snap_yaml("environment", env)
        c = SnapReviewLint(self.test_name)
        c.check_environment()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_environment_bad_env(self):
        '''Test check_environment - bad env - list'''
        env = []
        self.set_test_snap_yaml("environment", env)
        c = SnapReviewLint(self.test_name)
        c.check_environment()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_environment_bad_value(self):
        '''Test check_environment - bad value - list'''
        env = {'ENV1': [],
               }
        self.set_test_snap_yaml("environment", env)
        c = SnapReviewLint(self.test_name)
        c.check_environment()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_aliases(self):
        '''Test check_apps_aliases'''
        apps = {'app1': {'aliases': ['foo']},
                'app2': {'aliases': ['bar', 'app2-bar']},
                'app3': {},
                }

        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewLint(self.test_name)
        c.check_apps_aliases()
        r = c.click_report
        expected_counts = {'info': 5, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:aliases_valid:app1'
        expected['info'][name] = {"text": "DEPRECATED: support for using 'aliases' in the yaml is being removed and will be replaced with snap declarations. Please request a snap declaration via the forum."}
        self.check_results(r, expected=expected)

    def test_check_apps_aliases_empty(self):
        '''Test check_apps_aliases (empty)'''
        apps = {'app1': {'aliases': []}}

        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewLint(self.test_name)
        c.check_apps_aliases()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_aliases_dict(self):
        '''Test check_apps_aliases (dict)'''
        apps = {'app1': {'aliases': {}}}

        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewLint(self.test_name)
        c.check_apps_aliases()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_aliases_bad(self):
        '''Test check_apps_aliases (bad)'''
        apps = {'app1': {'aliases': ['foo/bar']}}

        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewLint(self.test_name)
        c.check_apps_aliases()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_aliases_dupe(self):
        '''Test check_apps_aliases (dupe)'''
        apps = {'app1': {'aliases': ['foo']},
                'app2': {'aliases': ['bar', 'foo']},
                }

        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewLint(self.test_name)
        c.check_apps_aliases()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_license(self):
        '''Test check_license'''
        self.set_test_snap_yaml("license", "GPL-3.0")
        c = SnapReviewLint(self.test_name)
        c.check_license()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_license_empty(self):
        '''Test check_license - empty'''
        self.set_test_snap_yaml("license", "")
        c = SnapReviewLint(self.test_name)
        c.check_license()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_license_missing(self):
        '''Test check_license - not present'''
        self.set_test_snap_yaml("license", None)
        c = SnapReviewLint(self.test_name)
        c.check_license()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_license_invalid(self):
        '''Test check_license - invalid'''
        self.set_test_snap_yaml("license", [])
        c = SnapReviewLint(self.test_name)
        c.check_license()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_sockets_valid_listen_stream_snap_data(self):
        '''Test check_apps_sockets() - valid listen-stream SNAP_DATA'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": "$SNAP_DATA/sock"
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_sockets_valid_listen_stream_snap_common(self):
        '''Test check_apps_sockets() - valid listen-stream SNAP_COMMON'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": "$SNAP_COMMON/sock"
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_sockets_valid_listen_stream_abstract(self):
        '''Test check_apps_sockets() - valid listen-stream abstract'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": "@snap.foo.bar"
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_sockets_valid_listen_stream_port(self):
        '''Test check_apps_sockets() - valid listen-stream port'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": 8080
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_sockets_valid_listen_stream_port_str(self):
        '''Test check_apps_sockets() - valid listen-stream port as str'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": "8080"
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_sockets_invalid_sockname(self):
        '''Test check_apps_sockets() - bad sockname'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "b@d": {
                        "listen-stream": 8080
                    }
                }
            }
        })
        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_sockets_invalid_listen_stream_typ(self):
        '''Test check_apps_sockets() - bad listen-stream type'''
        self.set_test_snap_yaml("apps", {"foo": {"sockets": []}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_sockets_listen_stream_missing(self):
        '''Test check_apps_sockets() - listen-stream missing'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "socket-mode": "0666"
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_sockets_invalid_listen_stream_port_str(self):
        '''Test check_apps_sockets() - invalid listen-stream port as str'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": "bad"
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_sockets_invalid_listen_stream_port_empty(self):
        '''Test check_apps_sockets() - invalid listen-stream port empty'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": ""
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_sockets_invalid_listen_stream_port_range(self):
        '''Test check_apps_sockets() - invalid listen-stream port range'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": 0
                    },
                    "sock2": {
                        "listen-stream": 65536
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 2}
        self.check_results(r, expected_counts)

    def test_check_sockets_invalid_listen_stream_port_type(self):
        '''Test check_apps_sockets() - invalid listen-stream port type'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": []
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_sockets_invalid_listen_stream_path_dotdot(self):
        '''Test check_apps_sockets() - invalid listen-stream path ..'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": "$SNAP_DATA/../sock"
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_sockets_invalid_listen_stream_path_abspath(self):
        '''Test check_apps_sockets() - invalid listen-stream abspath'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": "/run/sock"
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_sockets_invalid_listen_stream_abstract(self):
        '''Test check_apps_sockets() - invalid listen-stream abstract'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": "@snap.other.bar"
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_sockets_invalid_socket_mode_type(self):
        '''Test check_apps_sockets() - listen-stream type'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": "$SNAP_DATA/sock",
                        "socket-mode": []
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_sockets_invalid_socket_mode_empty(self):
        '''Test check_apps_sockets() - socket-mode empty'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": "$SNAP_DATA/sock",
                        "socket-mode": ""
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_sockets_invalid_socket_mode_range(self):
        '''Test check_apps_sockets() - socket-mode range'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": "$SNAP_DATA/sock",
                        "socket-mode": 0
                    },
                    "sock2": {
                        "listen-stream": "$SNAP_DATA/sock",
                        "socket-mode": "778"
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 2}
        self.check_results(r, expected_counts)

    def test_check_sockets_invalid_socket_mode_not_with_file(self):
        '''Test check_apps_sockets() - socket-mode not with file'''
        self.set_test_snap_yaml("apps", {
            "foo": {
                "sockets": {
                    "sock1": {
                        "listen-stream": "@snap.foo.cmd",
                        "socket-mode": "666"
                    },
                    "sock2": {
                        "listen-stream": "127.0.0.1:8080",
                        "socket-mode": "666"
                    }
                }
            }
        })

        c = SnapReviewLint(self.test_name)
        c.check_apps_sockets()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 2}
        self.check_results(r, expected_counts)

    def test_check_base_allowed(self):
        '''Test check_base - allowed'''
        self.set_test_snap_yaml("base", "allowed")
        c = SnapReviewLint(self.test_name)
        c.check_base()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_base_redflagged(self):
        '''Test check_base - redflagged'''
        self.set_test_snap_yaml("base", "solus-runtime-gaming")
        c = SnapReviewLint(self.test_name)
        c.check_base()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)
        name = c._get_check_name('base_allowed')
        self.check_manual_review(r, name)

    def test_check_base_redflagged_whitelisted(self):
        '''Test check_base - redflagged base, whitelisted app'''
        self.set_test_snap_yaml("base", "solus-runtime-gaming")
        self.set_test_snap_yaml("name", "linux-steam-integration")
        c = SnapReviewLint(self.test_name)
        c.check_base()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:base_allowed'
        expected['info'][name] = {"text": "OK"}
        self.check_results(r, expected=expected)

    def test_check_apps_common_id(self):
        '''Test check_apps_common_id()'''
        entry = "org.example.foo.desktop"
        self.set_test_snap_yaml("apps", {"foo": {"common-id": entry}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_common_id()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_common_id_bad(self):
        '''Test check_apps_common_id() - bad'''
        self.set_test_snap_yaml("apps", {"foo": {"common-id": []}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_common_id()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_common_id_duplicated(self):
        '''Test check_apps_common_id() - duplicated'''
        entry = "org.example.foo.desktop"
        self.set_test_snap_yaml("apps", {"foo": {"common-id": entry},
                                         "bar": {"common-id": entry}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_common_id()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_layout(self):
        '''Test check_layout()'''
        self.set_test_snap_yaml(
            "layout", {
                '/etc/demo': {
                    'bind': '$SNAP_COMMON/etc/demo'
                },
                '/etc/demo.cfg': {
                    'symlink': '$SNAP_COMMON/etc/demo.conf'
                },
                '/etc/demo.conf': {
                    'bind-file': '$SNAP_COMMON/etc/demo.conf'
                },
                '/opt/demo': {
                    'bind': '$SNAP/opt/demo'
                },
                '/usr/share/demo': {
                    'bind': '$SNAP/usr/share/demo'
                },
                '/var/cache/demo': {
                    'bind': '$SNAP_DATA/var/cache/demo'
                },
                '/var/lib/demo': {
                    'bind': '$SNAP_DATA/var/lib/demo'
                },
            })
        c = SnapReviewLint(self.test_name)
        c.check_layout()
        r = c.click_report
        expected_counts = {'info': 21, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_layout_bad(self):
        '''Test check_layout() - bad (list)'''
        self.set_test_snap_yaml("layout", [])
        c = SnapReviewLint(self.test_name)
        c.check_layout()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_layout_empty(self):
        '''Test check_layout() - bad (empty)'''
        self.set_test_snap_yaml("layout", {})
        c = SnapReviewLint(self.test_name)
        c.check_layout()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_layout_target_bad_val(self):
        '''Test check_layout() - bad target (list)'''
        self.set_test_snap_yaml("layout", {'/etc/demo': []})
        c = SnapReviewLint(self.test_name)
        c.check_layout()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_layout_target_bad_empty(self):
        '''Test check_layout() - bad target (empty)'''
        self.set_test_snap_yaml("layout", {'/etc/demo': {}})
        c = SnapReviewLint(self.test_name)
        c.check_layout()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_layout_target_bad(self):
        '''Test check_layout() - bad target (normpath)'''
        self.set_test_snap_yaml(
            "layout", {
                '/etc/../demo': {
                    'bind': '$SNAP_COMMON/etc/demo'
                },
            })
        c = SnapReviewLint(self.test_name)
        c.check_layout()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_layout_source_bad_prefix(self):
        '''Test check_layout() - bad source (prefix)'''
        self.set_test_snap_yaml(
            "layout", {
                '/etc/demo': {
                    'bind': '/bad/etc/demo'
                },
            })
        c = SnapReviewLint(self.test_name)
        c.check_layout()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_layout_source_bad_val(self):
        '''Test check_layout() - bad source (list)'''
        self.set_test_snap_yaml(
            "layout", {
                '/etc/demo': {
                    'bind': []
                },
            })
        c = SnapReviewLint(self.test_name)
        c.check_layout()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_layout_source_bad(self):
        '''Test check_layout() - bad source (normpath)'''
        self.set_test_snap_yaml(
            "layout", {
                '/etc/demo': {
                    'bind': '$SNAP_COMMON/etc/../demo'
                },
            })
        c = SnapReviewLint(self.test_name)
        c.check_layout()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_layout_source_bad_type(self):
        '''Test check_layout() - bad source (type)'''
        self.set_test_snap_yaml(
            "layout", {
                '/etc/demo': {
                    'nonexistent': '$SNAP_COMMON/etc/demo'
                },
            })
        c = SnapReviewLint(self.test_name)
        c.check_layout()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_refresh_mode(self):
        '''Test check_apps_refresh_mode()'''
        self.set_test_snap_yaml("apps", {"foo": {"refresh-mode": "endure"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_refresh_mode()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_refresh_mode_bad(self):
        '''Test check_apps_refresh_mode() - bad'''
        self.set_test_snap_yaml("apps", {"foo": {"refresh-mode": []}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_refresh_mode()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_refresh_mode_unknown(self):
        '''Test check_apps_refresh_mode() - unknown'''
        self.set_test_snap_yaml("apps", {"foo": {"refresh-mode":
                                                 "nonexistent"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_refresh_mode()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_mode(self):
        '''Test check_apps_stop_mode()'''
        self.set_test_snap_yaml("apps", {"foo": {"stop-mode": "sigterm"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_mode()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_mode_bad(self):
        '''Test check_apps_stop_mode() - bad'''
        self.set_test_snap_yaml("apps", {"foo": {"stop-mode": []}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_mode()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_stop_mode_unknown(self):
        '''Test check_apps_stop_mode() - unknown'''
        self.set_test_snap_yaml("apps", {"foo": {"stop-mode":
                                                 "nonexistent"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_stop_mode()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snap_manifest(self):
        '''Test check_snap_manifest()'''
        m = self._create_manifest_yaml()
        for f in m:
            self.set_test_snap_manifest_yaml(f, m[f])
        c = SnapReviewLint(self.test_name)
        c.check_snap_manifest()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_snap_manifest_toplevel_missing(self):
        '''Test check_snap_manifest() - missing toplevel key'''
        m = self._create_manifest_yaml()
        for f in m:
            if f != 'build-packages':
                self.set_test_snap_manifest_yaml(f, m[f])
        c = SnapReviewLint(self.test_name)
        c.check_snap_manifest()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snap_manifest_toplevel_wrong(self):
        '''Test check_snap_manifest() - wrong toplevel key type'''
        m = self._create_manifest_yaml()
        for f in m:
            if f != 'build-packages':
                self.set_test_snap_manifest_yaml(f, m[f])
        self.set_test_snap_manifest_yaml('build-packages', {})
        c = SnapReviewLint(self.test_name)
        c.check_snap_manifest()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snap_manifest_toplevel_optional_wrong(self):
        '''Test check_snap_manifest() - wrong toplevel optional key type'''
        m = self._create_manifest_yaml()
        for f in m:
            if f != 'parts':
                self.set_test_snap_manifest_yaml(f, m[f])
        self.set_test_snap_manifest_yaml('parts', "")
        c = SnapReviewLint(self.test_name)
        c.check_snap_manifest()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snap_manifest_toplevel_unknown(self):
        '''Test check_snap_manifest() - unknown toplevel key'''
        m = self._create_manifest_yaml()
        for f in m:
            self.set_test_snap_manifest_yaml(f, m[f])
        self.set_test_snap_manifest_yaml('unknown', {})
        c = SnapReviewLint(self.test_name)
        c.check_snap_manifest()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snap_manifest_part_missing(self):
        '''Test check_snap_manifest() - missing part key'''
        m = self._create_manifest_yaml()
        for f in m:
            if f != 'parts':
                self.set_test_snap_manifest_yaml(f, m[f])
        del m['parts']['mypart']['build-packages']
        self.set_test_snap_manifest_yaml('parts', m['parts'])
        c = SnapReviewLint(self.test_name)
        c.check_snap_manifest()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_snap_manifest_part_wrong(self):
        '''Test check_snap_manifest() - wrong part key type'''
        m = self._create_manifest_yaml()
        for f in m:
            if f != 'parts':
                self.set_test_snap_manifest_yaml(f, m[f])
        m['parts']['mypart']['build-packages'] = {}
        self.set_test_snap_manifest_yaml('parts', m['parts'])
        c = SnapReviewLint(self.test_name)
        c.check_snap_manifest()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_timer(self):
        '''Test check_apps_timer()'''
        good = ["0:00-24:00/96",
                "9:00-11:00,,20:00-22:00",
                "9:00-11:00/2,,20:00",
                "9:00~11:00/2,,20:00",
                "mon,10:00,,fri,15:00",
                "mon-fri,10:00-11:00",
                "fri-mon,10:00-11:00",
                "mon5,10:00",
                "mon2,10:00",
                "mon2,mon1,10:00",
                "mon1-mon3,10:00",
                "mon,10:00~12:00,,fri,15:00",
                "23:00~24:00/4",
                "23:00~01:00/4",
                "23:00-01:00/4",
                "24:00",
                ]
        for timer in good:
            self.set_test_snap_yaml("apps", {"bar": {"timer": timer}})
            c = SnapReviewLint(self.test_name)
            c.check_apps_timer()
            r = c.click_report
            expected_counts = {'info': 1, 'warn': 0, 'error': 0}
            self.check_results(r, expected_counts)

    def test_check_apps_timer_bad_dict(self):
        '''Test check_apps_timer() - bad dict'''
        self.set_test_snap_yaml("apps", {"bar": {"timer": {}}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_timer()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_timer_bad_timer(self):
        '''Test check_apps_timer() - bad timer'''
        self.set_test_snap_yaml("apps", {"bar": {"timer": "m0n5,1o:oo"}})
        c = SnapReviewLint(self.test_name)
        c.check_apps_timer()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_before_after_with_before(self):
        '''Test check_apps_before_after() - before'''
        self.set_test_snap_yaml("apps", {
                                "bar": {},
                                "baz": {"before": ["bar"]},
                                })
        c = SnapReviewLint(self.test_name)
        c.check_apps_before_after()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_before_after_with_after(self):
        '''Test check_apps_before_after() - after'''
        self.set_test_snap_yaml("apps", {
                                "bar": {},
                                "baz": {"after": ["bar"]},
                                })
        c = SnapReviewLint(self.test_name)
        c.check_apps_before_after()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_before_after_with_both(self):
        '''Test check_apps_before_after() - both'''
        self.set_test_snap_yaml("apps", {
                                "bar": {},
                                "baz": {"after": ["bar"]},
                                "norf": {"before": ["bar"]},
                                })
        c = SnapReviewLint(self.test_name)
        c.check_apps_before_after()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_apps_before_after_empty(self):
        '''Test check_apps_before_after() - empty'''
        self.set_test_snap_yaml("apps", {
                                "bar": {},
                                "baz": {"before": []},
                                })
        c = SnapReviewLint(self.test_name)
        c.check_apps_before_after()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_before_after_bad(self):
        '''Test check_apps_before_after() - bad'''
        self.set_test_snap_yaml("apps", {
                                "bar": {},
                                "baz": {"before": "bad"},
                                })
        c = SnapReviewLint(self.test_name)
        c.check_apps_before_after()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_before_after_bad_entry(self):
        '''Test check_apps_before_after() - bad'''
        self.set_test_snap_yaml("apps", {
                                "bar": {},
                                "baz": {"before": [{}]},
                                })
        c = SnapReviewLint(self.test_name)
        c.check_apps_before_after()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_apps_before_after_nonexistent(self):
        '''Test check_apps_before_after() - bad'''
        self.set_test_snap_yaml("apps", {
                                "bar": {},
                                "baz": {"before": ["nonexistent"]},
                                })
        c = SnapReviewLint(self.test_name)
        c.check_apps_before_after()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_unicode_fields(self):
        '''Test check_unicode_fields()'''
        c = SnapReviewLint(self.test_name)
        c.check_unicode_fields()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_unicode_fields_description_newline(self):
        '''Test check_unicode_fields() - description (newline)'''
        self.set_test_snap_yaml("description", "invalid\nnewline")
        c = SnapReviewLint(self.test_name)
        c.check_unicode_fields()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_unicode_fields_description_invalid_unicode(self):
        '''Test check_unicode_fields() - description (invalid unicode)'''
        self.set_test_snap_yaml("description", "new\ninvalid \u200b")
        c = SnapReviewLint(self.test_name)
        c.check_unicode_fields()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:valid_unicode'
        expected['error'][name] = {"text": "found errors in file output: 'description' invalid: control/private unicode characters not allowed"}
        self.check_results(r, expected=expected)

    def test_check_unicode_fields_summary_invalid_unicode(self):
        '''Test check_unicode_fields() - summary (invalid unicode)'''
        self.set_test_snap_yaml("summary", "invalid \u200b")
        c = SnapReviewLint(self.test_name)
        c.check_unicode_fields()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:valid_unicode'
        expected['error'][name] = {"text": "found errors in file output: 'summary' invalid: control/private unicode characters not allowed"}
        self.check_results(r, expected=expected)

    def test_check_unicode_fields_summary_invalid_newline(self):
        '''Test check_unicode_fields() - summary (invalid newline)'''
        self.set_test_snap_yaml("summary", "invalid\nnewline")
        c = SnapReviewLint(self.test_name)
        c.check_unicode_fields()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)


class TestSnapReviewLintNoMock(TestCase):
    """Tests without mocks where they are not needed."""
    def setUp(self):
        # XXX cleanup_unpack() is required because global variables
        # UNPACK_DIR, RAW_UNPACK_DIR, PKG_FILES, and PKG_BIN_FILES are
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

    def test_check_external_symlinks_has_symlink_libc6(self):
        '''Test check_external_symlinks() - has symlink for libc6'''
        package = utils.make_snap2(output_dir=self.mkdtemp(),
                                   extra_files=['/usr/lib/x86_64-linux-gnu/libmvec.so,libmvec.so']
                                   )
        c = SnapReviewLint(package)
        c.check_external_symlinks()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_external_symlinks_has_symlink_libc6_ld_linux(self):
        '''Test check_external_symlinks() - ld-linux-x86-64.so.2'''
        package = utils.make_snap2(output_dir=self.mkdtemp(),
                                   extra_files=['/lib64/ld-linux-x86-64.so.2,ld-linux-x86-64.so.2']
                                   )
        c = SnapReviewLint(package)
        c.check_external_symlinks()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_external_symlinks_has_symlink_to_snap(self):
        '''Test check_external_symlinks() - /snap/<pkgname>/...'''
        package = utils.make_snap2(output_dir=self.mkdtemp(),
                                   extra_files=['/snap/test/current/foo,/snap/test/current/foo']
                                   )
        c = SnapReviewLint(package)
        c.check_external_symlinks()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_external_symlinks_has_symlink_to_snap_data(self):
        '''Test check_external_symlinks() - /var/snap/<pkgname>/...'''
        package = utils.make_snap2(output_dir=self.mkdtemp(),
                                   extra_files=['/var/snap/test/current/foo,/var/snap/test/current/foo']
                                   )
        c = SnapReviewLint(package)
        c.check_external_symlinks()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_external_symlinks_has_symlink_override(self):
        '''Test check_external_symlinks() - has symlink for override'''
        # update the overrides for this snap
        from clickreviews.overrides import common_external_symlink_override
        common_external_symlink_override['test'] = "usr/lib/snapd/snap-device-helper"
        package = utils.make_snap2(output_dir=self.mkdtemp(),
                                   extra_files=['/usr/lib/snapd/snap-device-helper,anything']
                                   )
        c = SnapReviewLint(package)
        c.check_external_symlinks()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
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

    def test_check_external_symlinks_base(self):
        '''Test check_external_symlinks() - base'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: test
version: 0.1
summary: some thing
description: some desc
type: base
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
        if platform.machine() == 'x86_64':
            expected_counts = {'info': None, 'warn': 0, 'error': 1}
        else:  # ignore test on non-amd64
            expected_counts = {'info': None, 'warn': 0, 'error': None}  # pragma: nocover
        self.check_results(r, expected_counts)

    def test_check_architecture_all_skips_pyc(self):
        '''Test check_architecture_all() - skips .pyc'''
        # copy /bin/ls to foo.pyc since ls is a binary
        package = utils.make_snap2(output_dir=self.mkdtemp(),
                                   extra_files=['/bin/ls:foo.pyc']
                                   )
        c = SnapReviewLint(package)
        c.check_architecture_all()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_architecture_all_has_binary_gadget(self):
        '''Test check_architecture_all() - has binary - gadget'''
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
                                                '/bin/ls:ls'
                                                ]
                                   )
        c = SnapReviewLint(package)
        c.check_architecture_all()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:valid_contents_for_architecture'
        if platform.machine() == 'x86_64':
            expected['info'][name] = {"text": "found binaries for architecture 'all': ls (ok for 'type: gadget')"}
        else:  # ignore test on non-amd64
            pass
        self.check_results(r, expected=expected)

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
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:architecture_specified_needed:amd64'
        expected['info'][name] = {"text": "Could not find compiled binaries for architecture 'amd64'"}
        self.check_results(r, expected=expected)

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

    def test_check_valid_hook_configure(self):
        '''Test check_valid_hook() - configure'''
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=['meta/hooks/configure?755']
                                   )
        c = SnapReviewLint(package)
        c.check_valid_hook()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_valid_hook_configure_nonexecutable(self):
        '''Test check_valid_hook() - configure not executable'''
        package = utils.make_snap2(output_dir=self.mkdtemp(),
                                   extra_files=['meta/hooks/configure']
                                   )
        c = SnapReviewLint(package)
        c.check_valid_hook()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_valid_hook_install(self):
        '''Test check_valid_hook() - install'''
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=['meta/hooks/install?755']
                                   )
        c = SnapReviewLint(package)
        c.check_valid_hook()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_valid_hook_install_nonexecutable(self):
        '''Test check_valid_hook() - install not executable'''
        package = utils.make_snap2(output_dir=self.mkdtemp(),
                                   extra_files=['meta/hooks/install']
                                   )
        c = SnapReviewLint(package)
        c.check_valid_hook()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_valid_hook_unknown(self):
        '''Test check_valid_hook() - unknown'''
        package = utils.make_snap2(output_dir=self.mkdtemp(),
                                   extra_files=['meta/hooks/unknown?755']
                                   )
        c = SnapReviewLint(package)
        c.check_valid_hook()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_valid_hook_connect_plug_home(self):
        '''Test check_valid_hook() - connect-plug-home'''
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=['meta/hooks/connect-plug-home?755']
                                   )
        c = SnapReviewLint(package)
        c.check_valid_hook()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_iffy(self):
        '''Test check_iffy()'''
        package = utils.make_snap2(output_dir=self.mkdtemp())
        c = SnapReviewLint(package)
        c.check_iffy()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_iffy_vimswp(self):
        '''Test check_iffy() - vim .swp'''
        package = utils.make_snap2(output_dir=self.mkdtemp(),
                                   extra_files=['.foo.swp',
                                                'bar/baz/.norf.swp']
                                   )
        c = SnapReviewLint(package)
        c.check_iffy()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:iffy_files'
        expected['warn'][name] = {"text": "found potentially sensitive files in package: .foo.swp, bar/baz/.norf.swp"}
        self.check_results(r, expected=expected)

    def test_check_plugs_lp1579201(self):
        '''Test check_plugs() - 1579201'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: test
version: 0.1
summary: some thing
description: some desc
architectures: [ amd64 ]
plugs:
    network: null
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=['%s:meta/snap.yaml' % path]
                                   )
        c = SnapReviewLint(package)
        c.check_plugs()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_meta_gui_desktop_app_plug(self):
        '''Test check_meta_gui_desktop() - app plug'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
apps:
  testme:
    command: bin/foo
    plugs: [ unity7 ]
'''
        with open(path, 'w') as f:
            f.write(content)

        desktop = os.path.join(output_dir, 'test.desktop')
        content = '''
[Desktop Entry]
Version=1.0
Name=Test
GenericName=Test Generic
Exec=testme
Terminal=false
Type=Application
'''
        with open(desktop, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                       '%s:meta/gui/test.desktop' % desktop,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_meta_gui_desktop_no_plugs(self):
        '''Test check_meta_gui_desktop() - top plug reference'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
apps:
  testme:
    command: bin/foo
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': 0, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_meta_gui_desktop_app_plug_reference(self):
        '''Test check_meta_gui_desktop() - app plug reference'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
plugs:
  ref:
    interface: unity7
apps:
  testme:
    command: bin/foo
    plugs: [ ref ]
'''
        with open(path, 'w') as f:
            f.write(content)

        desktop = os.path.join(output_dir, 'test.desktop')
        content = '''
[Desktop Entry]
Version=1.0
Name=Test
GenericName=Test Generic
Exec=testme
Terminal=false
Type=Application
'''
        with open(desktop, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                       '%s:meta/gui/test.desktop' % desktop,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_meta_gui_desktop_top_plug(self):
        '''Test check_meta_gui_desktop() - top plug'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
plugs:
  unity7: null
apps:
  testme:
    command: bin/foo
'''
        with open(path, 'w') as f:
            f.write(content)

        desktop = os.path.join(output_dir, 'test.desktop')
        content = '''
[Desktop Entry]
Version=1.0
Name=Test
GenericName=Test Generic
Exec=testme
Terminal=false
Type=Application
'''
        with open(desktop, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                       '%s:meta/gui/test.desktop' % desktop,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_meta_gui_desktop_top_plug_reference(self):
        '''Test check_meta_gui_desktop() - top plug reference'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
plugs:
  ref:
    interface: unity7
apps:
  testme:
    command: bin/foo
'''
        with open(path, 'w') as f:
            f.write(content)

        desktop = os.path.join(output_dir, 'test.desktop')
        content = '''
[Desktop Entry]
Version=1.0
Name=Test
GenericName=Test Generic
Exec=testme
Terminal=false
Type=Application
'''
        with open(desktop, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                       '%s:meta/gui/test.desktop' % desktop,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_meta_gui_desktop_app_plug_second_command(self):
        '''Test check_meta_gui_desktop() - app plug second command'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
apps:
  testme:
    command: bin/foo
  other:
    command: bin/foo
    plugs: [ unity7 ]
'''
        with open(path, 'w') as f:
            f.write(content)

        desktop = os.path.join(output_dir, 'test.desktop')
        content = '''
[Desktop Entry]
Version=1.0
Name=Test
GenericName=Test Generic
Exec=testme.other
Terminal=false
Type=Application
'''
        with open(desktop, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                       '%s:meta/gui/test.desktop' % desktop,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': 2, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_meta_gui_desktop_no_apps(self):
        '''Test check_meta_gui_desktop() - no apps'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
plugs:
  unity7: null
'''
        with open(path, 'w') as f:
            f.write(content)

        desktop = os.path.join(output_dir, 'test.desktop')
        content = '''
[Desktop Entry]
Version=1.0
Name=Test
GenericName=Test Generic
Exec=testme
Terminal=false
Type=Application
'''
        with open(desktop, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                       '%s:meta/gui/test.desktop' % desktop,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

    def test_check_meta_gui_desktop_missing_app_plug(self):
        '''Test check_meta_gui_desktop() - missing - app plug'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
apps:
  testme:
    command: bin/foo
    plugs: [ unity7 ]
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:meta_gui_desktop'
        expected['warn'][name] = {"text": "desktop interfaces (unity7) specified without a corresponding meta/gui/*.desktop file. If using snapcraft, please see https://snapcraft.io/docs/build-snaps/metadata#fixed-assets. Otherwise, please provide a desktop file in meta/gui/*.desktop (it should reference one of the 'apps' from your snapcraft/snap.yaml)."}
        self.check_results(r, expected=expected)

    def test_check_meta_gui_desktop_missing_app_plug_exception(self):
        '''Test check_meta_gui_desktop() - missing - app plug - exception'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: ffscreencast
version: 0.1
summary: some thing
description: some desc
apps:
  testme:
    command: bin/foo
    plugs: [ x11 ]
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:meta_gui_desktop'
        expected['info'][name] = {"text": "OK (overidden)"}
        self.check_results(r, expected=expected)

    def test_check_meta_gui_desktop_missing_app_plug_reference(self):
        '''Test check_meta_gui_desktop() - missing - app plug'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
plugs:
  ref:
    interface: unity7
apps:
  testme:
    command: bin/foo
    plugs: [ ref ]
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:meta_gui_desktop'
        expected['warn'][name] = {"text": "desktop interfaces (unity7) specified without a corresponding meta/gui/*.desktop file. If using snapcraft, please see https://snapcraft.io/docs/build-snaps/metadata#fixed-assets. Otherwise, please provide a desktop file in meta/gui/*.desktop (it should reference one of the 'apps' from your snapcraft/snap.yaml)."}
        self.check_results(r, expected=expected)

    def test_check_meta_gui_desktop_missing_app_plug_reference2(self):
        '''Test check_meta_gui_desktop() - missing - top plug'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
plugs:
  ref:
    interface: unity7
apps:
  testme:
    command: bin/foo
    plugs: [ ref ]
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:meta_gui_desktop'
        expected['warn'][name] = {"text": "desktop interfaces (unity7) specified without a corresponding meta/gui/*.desktop file. If using snapcraft, please see https://snapcraft.io/docs/build-snaps/metadata#fixed-assets. Otherwise, please provide a desktop file in meta/gui/*.desktop (it should reference one of the 'apps' from your snapcraft/snap.yaml)."}
        self.check_results(r, expected=expected)

    def test_check_meta_gui_desktop_missing_app_plug_reference3(self):
        '''Test check_meta_gui_desktop() - missing - app plug - ref'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
plugs:
  ref: unity7
apps:
  testme:
    command: bin/foo
    plugs: [ ref ]
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:meta_gui_desktop'
        expected['warn'][name] = {"text": "desktop interfaces (unity7) specified without a corresponding meta/gui/*.desktop file. If using snapcraft, please see https://snapcraft.io/docs/build-snaps/metadata#fixed-assets. Otherwise, please provide a desktop file in meta/gui/*.desktop (it should reference one of the 'apps' from your snapcraft/snap.yaml)."}
        self.check_results(r, expected=expected)

    def test_check_meta_gui_desktop_missing_top_plug_null(self):
        '''Test check_meta_gui_desktop() - missing - top plug - null'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
plugs:
  unity7: null
apps:
  testme:
    command: bin/foo
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:meta_gui_desktop'
        expected['warn'][name] = {"text": "desktop interfaces (unity7) specified without a corresponding meta/gui/*.desktop file. If using snapcraft, please see https://snapcraft.io/docs/build-snaps/metadata#fixed-assets. Otherwise, please provide a desktop file in meta/gui/*.desktop (it should reference one of the 'apps' from your snapcraft/snap.yaml)."}
        self.check_results(r, expected=expected)

    def test_check_meta_gui_desktop_missing_top_plug(self):
        '''Test check_meta_gui_desktop() - missing - top plug'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
plugs:
  ref:
    interface: unity7
apps:
  testme:
    command: bin/foo
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:meta_gui_desktop'
        expected['warn'][name] = {"text": "desktop interfaces (unity7) specified without a corresponding meta/gui/*.desktop file. If using snapcraft, please see https://snapcraft.io/docs/build-snaps/metadata#fixed-assets. Otherwise, please provide a desktop file in meta/gui/*.desktop (it should reference one of the 'apps' from your snapcraft/snap.yaml)."}
        self.check_results(r, expected=expected)

    def test_check_meta_gui_desktop_missing_top_plug_ref(self):
        '''Test check_meta_gui_desktop() - missing - top plug - ref'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
plugs:
  ref: unity7
apps:
  testme:
    command: bin/foo
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:meta_gui_desktop'
        expected['warn'][name] = {"text": "desktop interfaces (unity7) specified without a corresponding meta/gui/*.desktop file. If using snapcraft, please see https://snapcraft.io/docs/build-snaps/metadata#fixed-assets. Otherwise, please provide a desktop file in meta/gui/*.desktop (it should reference one of the 'apps' from your snapcraft/snap.yaml)."}
        self.check_results(r, expected=expected)

    def test_check_meta_gui_desktop_missing_exec(self):
        '''Test check_meta_gui_desktop() - missing Exec='''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
apps:
  testme:
    command: bin/foo
    plugs: [ unity7 ]
'''
        with open(path, 'w') as f:
            f.write(content)

        desktop = os.path.join(output_dir, 'test.desktop')
        content = '''
[Desktop Entry]
Version=1.0
Name=Test
GenericName=Test Generic
Terminal=false
Type=Application
'''
        with open(desktop, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                       '%s:meta/gui/test.desktop' % desktop,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 0, 'error': 1}
        self.check_results(r, expected_counts)

    def test_check_meta_gui_desktop_missing_mir_kiosk(self):
        '''Test check_meta_gui_desktop() - missing - mir-kiosk'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
plugs:
  foo:
    interface: content
    default-provider: mir-kiosk
apps:
  testme:
    command: bin/foo
    plugs: [ x11 ]
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': 1, 'warn': 0, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:meta_gui_desktop'
        expected['info'][name] = {"text": "OK (using x11 with mir-kiosk)"}
        self.check_results(r, expected=expected)

    def test_check_meta_gui_desktop_missing_not_mir_kiosk(self):
        '''Test check_meta_gui_desktop() - missing - not mir-kiosk'''
        output_dir = self.mkdtemp()
        path = os.path.join(output_dir, 'snap.yaml')
        content = '''
name: testme
version: 0.1
summary: some thing
description: some desc
plugs:
  foo:
    interface: content
    default-provider: something-else
apps:
  testme:
    command: bin/foo
    plugs: [ x11 ]
'''
        with open(path, 'w') as f:
            f.write(content)

        package = utils.make_snap2(output_dir=output_dir,
                                   extra_files=[
                                       '%s:meta/snap.yaml' % path,
                                   ]
                                   )
        c = SnapReviewLint(package)
        c.check_meta_gui_desktop()
        r = c.click_report
        expected_counts = {'info': None, 'warn': 1, 'error': 0}
        self.check_results(r, expected_counts)

        expected = dict()
        expected['error'] = dict()
        expected['warn'] = dict()
        expected['info'] = dict()
        name = 'lint-snap-v2:meta_gui_desktop'
        expected['warn'][name] = {"text": "desktop interfaces (x11) specified without a corresponding meta/gui/*.desktop file. If using snapcraft, please see https://snapcraft.io/docs/build-snaps/metadata#fixed-assets. Otherwise, please provide a desktop file in meta/gui/*.desktop (it should reference one of the 'apps' from your snapcraft/snap.yaml)."}
        self.check_results(r, expected=expected)
