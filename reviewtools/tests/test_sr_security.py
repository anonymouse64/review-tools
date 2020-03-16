"""test_sr_security.py: tests for the sr_security module"""
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

from __future__ import print_function
from unittest import TestCase
import os
import re
import shutil
import tempfile
import yaml

from reviewtools.common import cleanup_unpack
from reviewtools.common import check_results as common_check_results
from reviewtools.sr_security import SnapReviewSecurity
import reviewtools.sr_tests as sr_tests
from reviewtools.tests import utils


class TestSnapReviewSecurity(sr_tests.TestSnapReview):
    """Tests for the security lint review tool."""

    def setUp(self):
        super().setUp()
        self.set_test_pkgfmt("snap", "16.04")

    def _create_top_plugs(self):
        plugs = {"iface-network": {"interface": "network"}, "network-bind": {}}
        return plugs

    def _create_apps_plugs(self):
        plugs = {
            "app1": {"plugs": ["iface-network"]},
            "app2": {"plugs": ["network-bind"]},
            "app3": {"plugs": ["iface-network", "network-bind"]},
        }
        return plugs

    def _create_top_slots(self):
        slots = {"iface-slot1": {"interface": "network"}, "network-bind": {}}
        return slots

    def _create_apps_slots(self):
        slots = {
            "app4": {"slots": ["iface-slot1"]},
            "app5": {"slots": ["network-bind"]},
        }
        return slots

    # The next two checks just make sure every check is run. One with the
    # default snap from the tests and one empty. We do it this way so as not
    # to add separate tests for short-circuit returns like:
    #   if 'apps' not in self.snap_yaml:
    #     return
    def test_all_checks_as_v2(self):
        """Test snap v2 has checks"""
        self.set_test_pkgfmt("snap", "16.04")

        plugs = self._create_top_plugs()
        self.set_test_snap_yaml("plugs", plugs)

        slots = self._create_top_slots()
        self.set_test_snap_yaml("slots", slots)

        apps = {}
        apps_plugs = self._create_apps_plugs()
        apps_slots = self._create_apps_slots()
        for key in apps_plugs:
            apps[key] = apps_plugs[key]
        for key in apps_slots:
            apps[key] = apps_slots[key]

        c = SnapReviewSecurity(self.test_name)
        c.do_checks()
        sum = 0
        for i in c.review_report:
            sum += len(c.review_report[i])
        self.assertTrue(sum != 0)

    def test_all_checks_as_empty_v2(self):
        """Test snap v2 has checks - (mostly) empty yaml"""
        self.set_test_pkgfmt("snap", "16.04")
        tmp = []
        for key in self.test_snap_yaml:
            if key not in ["name", "version"]:  # required
                tmp.append(key)
        for key in tmp:
            self.set_test_snap_yaml(key, None)
        c = SnapReviewSecurity(self.test_name)
        c.do_checks()
        sum = 0
        for i in c.review_report:
            sum += len(c.review_report[i])
        self.assertTrue(sum != 0)

    def test_check_security_plugs_browser_support_with_daemon_top_plugs(self):
        """ Test check_security_plugs() - daemon with toplevel plugs"""
        plugs = {"browser": {"interface": "browser-support"}}
        self.set_test_snap_yaml("plugs", plugs)
        apps = {"app1": {"plugs": ["browser"], "daemon": "simple"}}
        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewSecurity(self.test_name)
        c.check_security_plugs_browser_support_with_daemon()
        report = c.review_report
        expected_counts = {"info": None, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_security_plugs_browser_support_no_daemon_top_plugs(self):
        """ Test check_security_plugs() - no daemon with toplevel plugs"""
        plugs = {"browser": {"interface": "browser-support"}}
        self.set_test_snap_yaml("plugs", plugs)
        apps = {"app1": {"plugs": ["browser"]}}
        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewSecurity(self.test_name)
        c.check_security_plugs_browser_support_with_daemon()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_security_plugs_browser_support_with_daemon_top_plugs2(self):
        """ Test check_security_plugs() - daemon with toplevel plugs, no interface"""
        plugs = {"browser-support": {}}
        self.set_test_snap_yaml("plugs", plugs)
        apps = {"app1": {"daemon": "simple"}}
        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewSecurity(self.test_name)
        c.check_security_plugs_browser_support_with_daemon()
        report = c.review_report
        expected_counts = {"info": None, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_security_plugs_browser_support_no_daemon_top_plugs2(self):
        """ Test check_security_plugs() - no daemon with toplevel plugs, no interface"""
        plugs = {"browser-support": {}}
        self.set_test_snap_yaml("plugs", plugs)
        apps = {"app1": {}}
        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewSecurity(self.test_name)
        c.check_security_plugs_browser_support_with_daemon()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_security_plugs_browser_support_with_daemon(self):
        """ Test check_security_plugs() - daemon with plugs"""
        apps = {"app1": {"plugs": ["browser-support"], "daemon": "simple"}}
        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewSecurity(self.test_name)
        c.check_security_plugs_browser_support_with_daemon()
        report = c.review_report
        expected_counts = {"info": None, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_security_plugs_browser_support_no_daemon(self):
        """ Test check_security_plugs() - no daemon with plugs"""
        apps = {"app1": {"plugs": ["browser-support"]}}
        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewSecurity(self.test_name)
        c.check_security_plugs_browser_support_with_daemon()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_security_plugs_browser_support_with_daemon_no_browser_support(self):
        """ Test check_security_plugs() - daemon without browser-support"""
        apps = {"app1": {"plugs": ["network"], "daemon": "simple"}}
        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewSecurity(self.test_name)
        c.check_security_plugs_browser_support_with_daemon()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_security_plugs_browser_support_no_plugs(self):
        """ Test check_security_plugs() - daemon without browser-support"""
        apps = {"app1": {"daemon": "simple"}}
        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewSecurity(self.test_name)
        c.check_security_plugs_browser_support_with_daemon()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_security_plugs_browser_support_multiple(self):
        """ Test check_security_plugs() - multiple apps"""
        plugs = {"browser": {"interface": "browser-support"}}
        self.set_test_snap_yaml("plugs", plugs)
        apps = {"app1": {"plugs": ["browser"]}, "app2": {"daemon": "simple"}}
        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewSecurity(self.test_name)
        c.check_security_plugs_browser_support_with_daemon()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_security_plugs_browser_support_daemon_override(self):
        """ Test check_security_plugs() - browser-support w/ daemon override"""
        apps = {"app1": {"plugs": ["browser-support"], "daemon": "simple"}}
        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewSecurity(self.test_name)

        # update the overrides with our snap
        from reviewtools.overrides import sec_browser_support_overrides

        sec_browser_support_overrides.append(self.test_snap_yaml["name"])
        # run the test
        c.check_security_plugs_browser_support_with_daemon()
        # then cleanup the overrides
        sec_browser_support_overrides.remove(self.test_snap_yaml["name"])

        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)
        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:daemon_with_browser-support:app1"
        expected["info"][name] = {
            "text": "OK (allowing 'daemon' with 'browser-support')"
        }
        self.check_results(report, expected=expected)

    def test_check_apparmor_profile_name_length(self):
        """Test check_apparmor_profile_name_length()"""
        apps = {"app1": {"plugs": ["iface-caps"]}}
        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewSecurity(self.test_name)
        c.check_apparmor_profile_name_length()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_apparmor_profile_name_length_no_plugs(self):
        """Test check_apparmor_profile_name_length()"""
        apps = {"app1": {}}
        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewSecurity(self.test_name)
        c.check_apparmor_profile_name_length()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_apparmor_profile_name_length_bad(self):
        """Test check_apparmor_profile_name_length() - too long"""
        self.set_test_snap_yaml("name", "A" * 253)
        apps = {"app1": {"plugs": ["iface-caps"]}}
        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewSecurity(self.test_name)
        c.check_apparmor_profile_name_length()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

    def test_check_apparmor_profile_name_length_bad2(self):
        """Test check_apparmor_profile_name_length() - longer than advised"""
        self.set_test_snap_yaml("name", "A" * 100)
        apps = {"app1": {"plugs": ["iface-caps"]}}
        self.set_test_snap_yaml("apps", apps)
        c = SnapReviewSecurity(self.test_name)
        c.check_apparmor_profile_name_length()
        report = c.review_report
        expected_counts = {"info": None, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_squashfs_files(self):
        """Test check_squashfs_files()"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

drwxrwxr-x root/root                38 2016-03-11 12:25 squashfs-root
drwxrwxr-x root/root                88 2016-03-03 13:51 squashfs-root/bin
-rwxrwxr-x root/root                31 2016-02-12 10:07 squashfs-root/bin/echo
-rwxrwxr-x root/root                27 2016-02-12 10:07 squashfs-root/bin/env
-rwxrwxr-x root/root               274 2016-02-12 10:07 squashfs-root/bin/evil
-rwxrwxr-x root/root               209 2016-03-11 12:26 squashfs-root/bin/sh
-rwxrwxr-x root/root               436 2016-02-12 10:19 squashfs-root/bin/showdev
-rwxrwxr-x root/root               701 2016-02-12 10:19 squashfs-root/bin/usehw
drwxrwxr-x root/root                48 2016-03-11 12:26 squashfs-root/meta
-rw-rw-r-- root/root             18267 2016-02-12 10:07 squashfs-root/meta/icon.png
-rw-rw-r-- root/root               813 2016-03-11 12:26 squashfs-root/meta/snap.yaml
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_squashfs_files_no_override(self):
        """Test check_squashfs_files()"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

drwxrwxr-x root/root                38 2016-03-11 12:25 squashfs-root
-rwsr-xr-x root/root                31 2016-02-12 10:07 squashfs-root/test
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files"
        expected["error"][name] = {
            "text": "found errors in file output: unusual mode 'rwsr-xr-x' for entry './test'"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_override(self):
        """Test check_squashfs_files()"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

drwxrwxr-x root/root                38 2016-03-11 12:25 squashfs-root
-rwsr-xr-x root/root                31 2016-02-12 10:07 squashfs-root/test
"""
        self.set_test_unsquashfs_lls(out)

        # update the overrides
        from reviewtools.overrides import sec_mode_overrides

        sec_mode_overrides["foo"] = {"./test": "rwsr-xr-x"}
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        # clean up
        del sec_mode_overrides["foo"]
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_squashfs_files_override_list(self):
        """Test check_squashfs_files()"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

drwxrwxr-x root/root                38 2016-03-11 12:25 squashfs-root
-rwsr-xr-x root/root                31 2016-02-12 10:07 squashfs-root/test
"""
        self.set_test_unsquashfs_lls(out)

        # update the overrides
        from reviewtools.overrides import sec_mode_overrides

        sec_mode_overrides["foo"] = {"./test": ["rwsr-sr-x", "rwsr-xr-x"]}
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        # clean up
        del sec_mode_overrides["foo"]
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_squashfs_files_short_output(self):
        """Test check_squashfs_files() - short output"""
        out = """output
too
short
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

    def test_check_squashfs_files_bad_mode_invalid_type(self):
        """Test check_squashfs_files() - bad mode - invalid type"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

:rwxrwxr-x root/root                38 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files"
        expected["error"][name] = {
            "text": "found errors in file output: unknown type ':' for entry './foo'"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_line(self):
        """Test check_squashfs_files() - bad line"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rwxrwxr-x root/root                38 2016-03-11
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files_malformed_line"
        expected["error"][name] = {
            "text": "malformed lines in unsquashfs output: 'wrong number of fields in '-rwxrwxr-x root/root                38 2016-03-11''"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_mode_length(self):
        """Test check_squashfs_files() - bad mode - length"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rwxrwxr-xx root/root                38 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files_malformed_line"
        expected["error"][name] = {
            "text": "malformed lines in unsquashfs output: 'mode 'rwxrwxr-xx' malformed for './foo''"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_mode_suid(self):
        """Test check_squashfs_files() - bad mode - suid"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rwsrwxr-x root/root                38 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files"
        expected["error"][name] = {
            "text": "found errors in file output: unusual mode 'rwsrwxr-x' for entry './foo'"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_mode_suid_ubuntu_core(self):
        """Test check_squashfs_files() - bad mode - unknown suid ubuntu-core"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rwsrwxr-x root/root                38 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        self.set_test_snap_yaml("name", "ubuntu-core")
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files"
        expected["error"][name] = {
            "text": "found errors in file output: unusual mode 'rwsrwxr-x' for entry './foo'"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_mode_suid_ubuntu_core_sudo(self):
        """Test check_squashfs_files() - mode - sudo suid on ubuntu-core"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rwsr-xr-x root/root                38 2016-03-11 12:25 squashfs-root/usr/bin/sudo
"""
        self.set_test_unsquashfs_lls(out)
        self.set_test_snap_yaml("name", "ubuntu-core")
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_squashfs_files_mode_suid_bare_sudo(self):
        """Test check_squashfs_files() - mode - sudo suid on bare"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rwsr-xr-x root/root                38 2016-03-11 12:25 squashfs-root/usr/bin/sudo
"""
        self.set_test_unsquashfs_lls(out)
        self.set_test_snap_yaml("name", "bare")
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files"
        expected["error"][name] = {
            "text": "found errors in file output: unusual mode 'rwsr-xr-x' for entry './usr/bin/sudo'"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_mode_suid_chrome_test_sandbox(self):
        """Test check_squashfs_files() - mode - chrome-sandbox with chrome-test
        """
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rwsr-xr-x root/root             14528 2016-08-02 18:18 squashfs-root/opt/google/chrome/chrome-sandbox
"""
        self.set_test_unsquashfs_lls(out)
        self.set_test_snap_yaml("name", "chrome-test")
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_squashfs_files_mode_openwrt_tmp(self):
        """Test check_squashfs_files() - mode - openwrt /tmp"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rwxrwxrwt root/root             14528 2016-08-02 18:18 squashfs-root/rootfs/tmp
"""
        self.set_test_unsquashfs_lls(out)
        self.set_test_snap_yaml("name", "openwrt")
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_squashfs_files_mode_sticky_dir(self):
        """Test check_squashfs_files() - mode - sticky dir"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

drwxrwxrwt root/root                38 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_squashfs_files_bad_mode_sticky_file(self):
        """Test check_squashfs_files() - bad mode - sticky file"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rwxrwxrwt root/root                38 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files"
        expected["error"][name] = {
            "text": "found errors in file output: unusual mode 'rwxrwxrwt' for entry './foo'"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_mode_symlink(self):
        """Test check_squashfs_files() - bad mode - symlink"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

lrwxrwxrw- root/root                38 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files"
        expected["error"][name] = {
            "text": "found errors in file output: unusual mode 'rwxrwxrw-' for symlink './foo'"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_type_block_os(self):
        """Test check_squashfs_files() - type - block os"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

brw-rw-rw- root/root                8,  0 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        self.set_test_snap_yaml("type", "os")
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_squashfs_files_type_block_base(self):
        """Test check_squashfs_files() - type - block os"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

brw-rw-rw- root/root                8,  0 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        self.set_test_snap_yaml("type", "base")
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_squashfs_files_bad_type_block(self):
        """Test check_squashfs_files() - bad type - block"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

brw-rw-rw- root/root                8,  0 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files"
        expected["error"][name] = {
            "text": "found errors in file output: file type 'b' not allowed (./foo)"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_type_char(self):
        """Test check_squashfs_files() - bad type - char"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

crw-rw-rw- root/root                8,  0 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files"
        expected["error"][name] = {
            "text": "found errors in file output: file type 'c' not allowed (./foo)"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_type_pipe(self):
        """Test check_squashfs_files() - bad type - pipe"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

prw-rw-rw- root/root                8,  0 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files"
        expected["error"][name] = {
            "text": "found errors in file output: file type 'p' not allowed (./foo)"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_type_socket(self):
        """Test check_squashfs_files() - bad type - block"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

srw-rw-rw- root/root                8,  0 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files"
        expected["error"][name] = {
            "text": "found errors in file output: file type 's' not allowed (./foo)"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_owner(self):
        """Test check_squashfs_files() - bad owner"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rw-rw-r-- bad                8 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files_malformed_line"
        expected["error"][name] = {
            "text": "malformed lines in unsquashfs output: 'user/group 'bad' malformed for './foo''"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_user(self):
        """Test check_squashfs_files() - bad user"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rw-rw-r-- bad/root                8 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files"
        expected["error"][name] = {
            "text": "found errors in file output: unusual user/group 'bad/root' for './foo'"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_group(self):
        """Test check_squashfs_files() - bad group"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rw-rw-r-- root/bad                8 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files"
        expected["error"][name] = {
            "text": "found errors in file output: unusual user/group 'root/bad' for './foo'"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_user_other_os(self):
        """Test check_squashfs_files() - user - other os"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rw-rw-r-- other/root                8 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        self.set_test_snap_yaml("type", "os")
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_squashfs_files_bad_major(self):
        """Test check_squashfs_files() - bad major"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

crw-rw-rw- root/root                a,  0 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        self.set_test_snap_yaml("type", "os")
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files_malformed_line"
        expected["error"][name] = {
            "text": "malformed lines in unsquashfs output: 'major 'a' malformed for './foo''"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_major2(self):
        """Test check_squashfs_files() - bad major 2"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

crw-rw-rw- root/root                a,120 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        self.set_test_snap_yaml("type", "os")
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files_malformed_line"
        expected["error"][name] = {
            "text": "malformed lines in unsquashfs output: 'major 'a' malformed for './foo''"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_minor(self):
        """Test check_squashfs_files() - bad minor"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

brw-rw-rw- root/root                8,  a 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        self.set_test_snap_yaml("type", "os")
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files_malformed_line"
        expected["error"][name] = {
            "text": "malformed lines in unsquashfs output: 'minor 'a' malformed for './foo''"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_minor2(self):
        """Test check_squashfs_files() - bad minor 2"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

brw-rw-rw- root/root                8,12a 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        self.set_test_snap_yaml("type", "os")
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files_malformed_line"
        expected["error"][name] = {
            "text": "malformed lines in unsquashfs output: 'minor '12a' malformed for './foo''"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_size(self):
        """Test check_squashfs_files() - bad size"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rw-rw-rw- root/root                a 2016-03-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files_malformed_line"
        expected["error"][name] = {
            "text": "malformed lines in unsquashfs output: 'size 'a' malformed for './foo''"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_date(self):
        """Test check_squashfs_files() - bad date"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rw-rw-rw- root/root                8 2016-0e-11 12:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files_malformed_line"
        expected["error"][name] = {
            "text": "malformed lines in unsquashfs output: 'date '2016-0e-11' malformed for './foo''"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_time(self):
        """Test check_squashfs_files() - bad time"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

-rw-rw-rw- root/root                8 2016-03-11 z2:25 squashfs-root/foo
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files_malformed_line"
        expected["error"][name] = {
            "text": "malformed lines in unsquashfs output: 'time 'z2:25' malformed for './foo''"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_files_bad_squashfs_root(self):
        """Test check_squashfs_files() - bad squashfs-root and meta"""
        out = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

drwx------ root/root                38 2016-03-11 12:25 squashfs-root
drwx------ root/root                48 2016-03-11 12:26 squashfs-root/meta
-rw-rw-r-- root/root               813 2016-03-11 12:26 squashfs-root/meta/snap.yaml
"""
        self.set_test_unsquashfs_lls(out)
        c = SnapReviewSecurity(self.test_name)
        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_files"
        expected["error"][name] = {
            "text": "found errors in file output: unable to read or access files in 'squashfs-root' due to mode 'rwx------', unable to read or access files in 'squashfs-root/meta' due to mode 'rwx------'"
        }
        self.check_results(report, expected=expected)

    def test__allowed_iface_reference_no_key(self):
        """Test _allowed_iface_reference() - missing key is ok"""
        plugs = {"not-overidden": {"interface": "network"}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewSecurity(self.test_name)
        c._allowed_iface_reference("plugs", "network")
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test__allowed_iface_reference_not_overidden(self):
        """Test _allowed_iface_reference() - not overidden"""
        plugs = {"not-overidden": {"interface": "test-iface"}}
        self.set_test_snap_yaml("plugs", plugs)
        c = SnapReviewSecurity(self.test_name)
        c._allowed_iface_reference("plugs", "test-iface")
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test__allowed_iface_reference_unknown(self):
        """Test _allowed_iface_reference() - unknown"""
        plugs = {"unknown-ref": {"interface": "test-iface"}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("name", "test-app")
        # add this snap to the override
        from reviewtools.overrides import sec_iface_ref_overrides

        sec_iface_ref_overrides["test-iface"] = {}
        c = SnapReviewSecurity(self.test_name)
        c._allowed_iface_reference("plugs", "test-iface")
        # then clean up
        del sec_iface_ref_overrides["test-iface"]
        report = c.review_report
        expected_counts = {"info": 0, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:interface-reference:unknown-ref:test-iface"
        expected["warn"][name] = {
            "text": "override not found for 'plugs/unknown-ref'. Use of the test-iface interface is reserved for vetted publishers. If your snap legitimately requires this access, please make a request in the forum using the 'store-requests' category (https://forum.snapcraft.io/c/store-requests), or if you would prefer to keep this private, the 'sensitive' category."
        }
        self.check_results(report, expected=expected)

    def test__allowed_iface_reference_known(self):
        """Test check__allowed_iface_reference() - known"""
        plugs = {"known-ref": {"interface": "test-iface"}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("name", "test-app")
        # add this snap to the override
        from reviewtools.overrides import sec_iface_ref_overrides

        sec_iface_ref_overrides["test-iface"] = {"test-app": ["known-ref"]}
        c = SnapReviewSecurity(self.test_name)
        c._allowed_iface_reference("plugs", "test-iface")
        # then clean up
        del sec_iface_ref_overrides["test-iface"]
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:interface-reference:known-ref:test-iface"
        expected["info"][name] = {"text": "OK"}
        self.check_results(report, expected=expected)

    def test__allowed_iface_reference_known_same(self):
        """Test check__allowed_iface_reference() - known ref is same"""
        plugs = {"test-iface": {"interface": "test-iface"}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("name", "test-app")
        # add this snap to the override
        from reviewtools.overrides import sec_iface_ref_overrides

        sec_iface_ref_overrides["test-iface"] = {"test-app": ["test-iface"]}
        c = SnapReviewSecurity(self.test_name)
        c._allowed_iface_reference("plugs", "test-iface")
        # then clean up
        del sec_iface_ref_overrides["test-iface"]
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:interface-reference:test-iface:test-iface"
        expected["info"][name] = {"text": "OK"}
        self.check_results(report, expected=expected)

    def test__allowed_iface_reference_disallowed(self):
        """Test check__allowed_iface_reference() - disallowed"""
        plugs = {"disallowed": {"interface": "test-iface"}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("name", "test-app")
        # add this snap to the override
        from reviewtools.overrides import sec_iface_ref_overrides

        sec_iface_ref_overrides["test-iface"] = {"test-app": ["known-ref"]}
        c = SnapReviewSecurity(self.test_name)
        c._allowed_iface_reference("plugs", "test-iface")
        # then clean up
        del sec_iface_ref_overrides["test-iface"]
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:interface-reference:disallowed:test-iface"
        expected["error"][name] = {
            "text": "interface reference 'disallowed' not allowed. Please use one of: known-ref"
        }
        self.check_results(report, expected=expected)

    def test_check_personal_files_interface_reference_known(self):
        """Test check_personal_files_interface_reference() - known"""
        plugs = {"known-ref": {"interface": "personal-files"}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("name", "test-app")
        # add this snap to the override
        from reviewtools.overrides import sec_iface_ref_overrides

        sec_iface_ref_overrides["personal-files"]["test-app"] = ["known-ref"]
        c = SnapReviewSecurity(self.test_name)
        c.check_personal_files_iface_reference()
        # then clean up
        del sec_iface_ref_overrides["personal-files"]["test-app"]
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:interface-reference:known-ref:personal-files"
        expected["info"][name] = {"text": "OK"}
        self.check_results(report, expected=expected)

    def test_check_system_files_interface_reference_disallowed(self):
        """Test check_system_files_interface_reference() - disallowed"""
        plugs = {"disallowed": {"interface": "system-files"}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("name", "test-app")
        # add this snap to the override
        from reviewtools.overrides import sec_iface_ref_overrides

        sec_iface_ref_overrides["system-files"]["test-app"] = ["known-ref"]
        c = SnapReviewSecurity(self.test_name)
        c.check_system_files_iface_reference()
        # then clean up
        del sec_iface_ref_overrides["system-files"]["test-app"]
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:interface-reference:disallowed:system-files"
        expected["error"][name] = {
            "text": "interface reference 'disallowed' not allowed. Please use one of: known-ref"
        }
        self.check_results(report, expected=expected)

    def test_check_personal_files_interface_references_known(self):
        """Test check_personal_files_interface_reference() - two known"""
        plugs = {
            "known-ref": {"interface": "personal-files"},
            "known-ref2": {"interface": "personal-files"},
        }
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("name", "test-app")
        # add this snap to the override
        from reviewtools.overrides import sec_iface_ref_overrides

        sec_iface_ref_overrides["personal-files"]["test-app"] = [
            "known-ref",
            "known-ref2",
        ]
        c = SnapReviewSecurity(self.test_name)
        c.check_personal_files_iface_reference()
        # then clean up
        del sec_iface_ref_overrides["personal-files"]["test-app"]
        report = c.review_report
        expected_counts = {"info": 2, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:interface-reference:known-ref:personal-files"
        expected["info"][name] = {"text": "OK"}
        self.check_results(report, expected=expected)
        name = "security-snap-v2:interface-reference:known-ref2:personal-files"
        expected["info"][name] = {"text": "OK"}
        self.check_results(report, expected=expected)

    def test_check_system_files_interface_references_one_disallowed(self):
        """Test check_system_files_interface_reference() - one disallowed"""
        plugs = {
            "known-ref": {"interface": "system-files"},
            "disallowed": {"interface": "system-files"},
        }
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("name", "test-app")
        # add this snap to the override
        from reviewtools.overrides import sec_iface_ref_overrides

        sec_iface_ref_overrides["system-files"]["test-app"] = ["known-ref"]
        c = SnapReviewSecurity(self.test_name)
        c.check_system_files_iface_reference()
        # then clean up
        del sec_iface_ref_overrides["system-files"]["test-app"]
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:interface-reference:known-ref:system-files"
        expected["info"][name] = {"text": "OK"}
        self.check_results(report, expected=expected)
        name = "security-snap-v2:interface-reference:disallowed:system-files"
        expected["error"][name] = {
            "text": "interface reference 'disallowed' not allowed. Please use one of: known-ref"
        }
        self.check_results(report, expected=expected)

    def test_check_system_files_interface_references_both_disallowed(self):
        """Test check_system_files_interface_reference() - both disallowed"""
        plugs = {
            "disallowed": {"interface": "system-files"},
            "disallowed2": {"interface": "system-files"},
        }
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("name", "test-app")
        # add this snap to the override
        from reviewtools.overrides import sec_iface_ref_overrides

        sec_iface_ref_overrides["system-files"]["test-app"] = ["known-ref"]
        c = SnapReviewSecurity(self.test_name)
        c.check_system_files_iface_reference()
        # then clean up
        del sec_iface_ref_overrides["system-files"]["test-app"]
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 2}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:interface-reference:disallowed:system-files"
        expected["error"][name] = {
            "text": "interface reference 'disallowed' not allowed. Please use one of: known-ref"
        }
        self.check_results(report, expected=expected)
        name = "security-snap-v2:interface-reference:disallowed2:system-files"
        expected["error"][name] = {
            "text": "interface reference 'disallowed2' not allowed. Please use one of: known-ref"
        }
        self.check_results(report, expected=expected)

    def _setup_base_declaration(self, c):
        # setup minimized base declaration
        decl = yaml.safe_load(
            """
plugs:
slots:
  iface:
    allow-installation:
      slot-snap-type:
      - core
  other:
    allow-installation:
      slot-snap-type:
      - core
"""
        )
        c.base_declaration = decl

    def test_check_interface_reference_matches_base_decl(self):
        """Test check_interface_reference_matches_base_decl()"""
        for obj in ["null", {"interface": "iface"}]:
            plugs = {"iface": obj}
            self.set_test_snap_yaml("plugs", plugs)
            self.set_test_snap_yaml("name", "test-app")

            c = SnapReviewSecurity(self.test_name)
            self._setup_base_declaration(c)
            c.check_interface_reference_matches_base_decl()
            report = c.review_report
            expected_counts = {"info": 0, "warn": 0, "error": 0}
            self.check_results(report, expected_counts)

    def test_check_interface_reference_matches_base_decl_found(self):
        """Test check_interface_reference_matches_base_decl() - found match"""
        plugs = {"other": {"interface": "iface"}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("name", "test-app")

        c = SnapReviewSecurity(self.test_name)
        self._setup_base_declaration(c)
        c.check_interface_reference_matches_base_decl()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:interface-reference-matches-base-decl:other"
        expected["warn"][name] = {
            "text": "interface reference 'other' found in base declaration"
        }
        self.check_results(report, expected=expected)

    def test_check_interface_reference_matches_base_decl_override(self):
        """Test check_interface_reference_matches_base_decl() - found match"""
        plugs = {"other": {"interface": "iface"}}
        self.set_test_snap_yaml("plugs", plugs)
        self.set_test_snap_yaml("name", "test-app")
        # update the overrides with our snap
        from reviewtools.overrides import sec_iface_ref_matches_base_decl_overrides

        sec_iface_ref_matches_base_decl_overrides["test-app"] = [("iface", "other")]
        c = SnapReviewSecurity(self.test_name)
        self._setup_base_declaration(c)
        c.check_interface_reference_matches_base_decl()
        # then clean up
        del sec_iface_ref_matches_base_decl_overrides["test-app"]

        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test__mode_in_override(self):
        """Test check__mode_in_override()"""
        # update the overrides
        from reviewtools.overrides import sec_mode_overrides

        pkg = "review-tools-testsuite"

        tests = [
            # pkgname, f, m, override, exp
            (None, "/fn", "rwxr-xr-x", None, False),
            (pkg, "/fn", "rwxr-xr-x", {"/test": "rwxrwxrwt"}, False),
            (pkg, "/test", "--x--x--x", {"/test": "rwxrwxrwt"}, False),
            (pkg, "/test", "--x--x--x", {"/test": ["rwxrwxrwt", "rwxrwxrwT"]}, False),
            (pkg, "/test", "rwxrwxrwt", {"/test": "rwxrwxrwt"}, True),
            (pkg, "/test", "rwxrwxrwt", {"/test": ["rwxrwxrwT", "rwxrwxrwt"]}, True),
        ]
        for (p, f, m, override, exp) in tests:
            if p is not None:
                sec_mode_overrides[p] = override
            c = SnapReviewSecurity(self.test_name)
            res = c._mode_in_override(p, f, m)
            self.assertEqual(exp, res)

            # then clean up
            if p is not None:
                del sec_mode_overrides[p]


class TestSnapReviewSecurityNoMock(TestCase):
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

    def check_results(
        self, report, expected_counts={"info": 1, "warn": 0, "error": 0}, expected=None
    ):
        common_check_results(self, report, expected_counts, expected)

    def test_check_squashfs_resquash(self):
        """Test check_squashfs_resquash()"""
        package = utils.make_snap2(output_dir=self.mkdtemp())
        c = SnapReviewSecurity(package)
        c.check_squashfs_resquash()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_squashfs_resquash_lzo(self):
        """Test check_squashfs_resquash() - lzo"""
        package = utils.make_snap2(output_dir=self.mkdtemp(), compression="lzo")
        c = SnapReviewSecurity(package)
        c.check_squashfs_resquash()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)
        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_compression"
        expected["error"][name] = {
            "text": "compression algorithm 'lzo' not allowed"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_resquash_lzo_override(self):
        """Test check_squashfs_resquash() - lzo override"""
        package = utils.make_snap2(output_dir=self.mkdtemp(), compression="lzo")
        c = SnapReviewSecurity(package)
        # update the overrides with our snap
        from reviewtools.overrides import sec_compression_overrides
        sec_compression_overrides["test"] = ["lzo"]
        # run the test
        c.check_squashfs_resquash()
        # then cleanup the overrides
        del sec_compression_overrides["test"]

        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)
        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_repack_checksum"
        expected["info"][name] = {
            "text": "OK"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_resquash_lzo_override_wrong(self):
        """Test check_squashfs_resquash() - lzo override"""
        package = utils.make_snap2(output_dir=self.mkdtemp(), compression="lzo")
        c = SnapReviewSecurity(package)
        # update the overrides with our snap
        from reviewtools.overrides import sec_compression_overrides
        sec_compression_overrides["test"] = ["xz"]
        # run the test
        c.check_squashfs_resquash()
        # then cleanup the overrides
        del sec_compression_overrides["test"]

        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)
        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_compression"
        expected["error"][name] = {
            "text": "compression algorithm 'lzo' not allowed"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_resquash_gzip(self):
        """Test check_squashfs_resquash() - gzip"""
        package = utils.make_snap2(output_dir=self.mkdtemp(), compression="gzip")
        c = SnapReviewSecurity(package)
        c.check_squashfs_resquash()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)
        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_compression"
        expected["error"][name] = {
            "text": "unsupported compression algorithm 'gzip'"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_resquash_no_fstime(self):
        """Test check_squashfs_resquash() - no -fstime"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        # fake unsquashfs
        unsquashfs = os.path.join(output_dir, "unsquashfs")
        content = """#!/bin/sh
if [ "$1" = "-stat" ]; then
    cat <<EOM
...
Compression xz
Number of fragments 0
...
EOM
    exit 0
fi
echo test error: -fstime failure
exit 1
"""
        with open(unsquashfs, "w") as f:
            f.write(content)
        os.chmod(unsquashfs, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        c.check_squashfs_resquash()
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": None, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_squashfs_resquash_unsquash_fail_stat(self):
        """Test check_squashfs_resquash() - -s failure"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        # fake unsquashfs
        unsquashfs = os.path.join(output_dir, "unsquashfs")
        content = """#!/bin/sh
if [ "$1" = "-fstime" ]; then
    exit 0
fi
echo test error: unsquashfs failure
exit 1
"""
        with open(unsquashfs, "w") as f:
            f.write(content)
        os.chmod(unsquashfs, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        c.check_squashfs_resquash()
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

    def test_check_squashfs_resquash_unsquash_fail_fragments(self):
        """Test check_squashfs_resquash() - fragments"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        # fake unsquashfs
        unsquashfs = os.path.join(output_dir, "unsquashfs")
        content = """#!/bin/sh
if [ "$1" = "-fstime" ]; then
    exit 0
fi
if [ "$1" = "-stat" ]; then
    cat <<EOM
...
Compression xz
Number of fragments 3
...
EOM
    exit 0
fi
echo test error: unsquashfs failure
exit 1
"""
        with open(unsquashfs, "w") as f:
            f.write(content)
        os.chmod(unsquashfs, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        os.environ["SNAP_ENFORCE_RESQUASHFS"] = "1"
        c.check_squashfs_resquash()
        os.environ.pop("SNAP_ENFORCE_RESQUASHFS")
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_fragments"
        expected["error"][name] = {
            "text": "The squashfs was built without '-no-fragments'. Please ensure the snap is created with either 'snapcraft pack <DIR>' (using snapcraft >= 2.38) or 'mksquashfs <dir> <snap> -noappend -comp xz -all-root -no-xattrs -no-fragments'. If using electron-builder, please upgrade to latest stable (>= 20.14.7). See https://forum.snapcraft.io/t/automated-reviews-and-snapcraft-2-38/4982/17 for details."
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_resquash_unsquash_fragments_override(self):
        """Test check_squashfs_resquash() - fragments - override"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        # fake unsquashfs
        unsquashfs = os.path.join(output_dir, "unsquashfs")
        content = """#!/bin/sh
if [ "$1" = "-stat" ]; then
    cat <<EOM
...
Compression xz
Number of fragments 3
...
EOM
fi
exit 0
"""
        with open(unsquashfs, "w") as f:
            f.write(content)
        os.chmod(unsquashfs, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        os.environ["SNAP_ENFORCE_RESQUASHFS"] = "1"
        # add this snap to the override
        from reviewtools.overrides import sec_resquashfs_overrides

        sec_resquashfs_overrides.append("test")
        c.check_squashfs_resquash()
        # then clean up
        sec_resquashfs_overrides.remove("test")
        os.environ.pop("SNAP_ENFORCE_RESQUASHFS")
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_fragments"
        expected["info"][name] = {
            "text": "OK (check not enforced for this snap): The squashfs was built without '-no-fragments'. Please ensure the snap is created with either 'snapcraft pack <DIR>' (using snapcraft >= 2.38) or 'mksquashfs <dir> <snap> -noappend -comp xz -all-root -no-xattrs -no-fragments'. If using electron-builder, please upgrade to latest stable (>= 20.14.7). See https://forum.snapcraft.io/t/automated-reviews-and-snapcraft-2-38/4982/17 for details."
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_resquash_unsquashfs_fail(self):
        """Test check_squashfs_resquash() - unsquashfs failure"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        # fake unsquashfs
        unsquashfs = os.path.join(output_dir, "unsquashfs")
        content = """#!/bin/sh
if [ "$1" = "-fstime" ]; then
    exit 0
fi
if [ "$1" = "-stat" ]; then
    cat <<EOM
...
Compression xz
Number of fragments 0
...
EOM
    exit 0
fi
echo test error: unsquashfs failure
exit 1
"""
        with open(unsquashfs, "w") as f:
            f.write(content)
        os.chmod(unsquashfs, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        os.environ["SNAP_ENFORCE_RESQUASHFS"] = "1"
        c.check_squashfs_resquash()
        os.environ.pop("SNAP_ENFORCE_RESQUASHFS")
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

    def test_check_squashfs_resquash_unsquashfs_comp_fail(self):
        """Test check_squashfs_resquash() - unsquashfs detect compression"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        # fake unsquashfs
        unsquashfs = os.path.join(output_dir, "unsquashfs")
        content = """#!/bin/sh
if [ "$1" = "-fstime" ]; then
    exit 0
fi
if [ "$1" = "-stat" ]; then
    cat <<EOM
...
Compression b@d
Number of fragments 0
...
EOM
    exit 0
fi
echo test error: unsquashfs failure
exit 1
"""
        with open(unsquashfs, "w") as f:
            f.write(content)
        os.chmod(unsquashfs, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        os.environ["SNAP_ENFORCE_RESQUASHFS"] = "1"
        c.check_squashfs_resquash()
        os.environ.pop("SNAP_ENFORCE_RESQUASHFS")
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)
        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_compression"
        expected["error"][name] = {
            "text": "could not determine compression algorithm"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_resquash_mksquashfs_fail(self):
        """Test check_squashfs_resquash() - mksquashfs failure"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        # fake mksquashfs
        mksquashfs = os.path.join(output_dir, "mksquashfs")
        content = """#!/bin/sh
echo test error: mksquashfs failure
exit 1
"""
        with open(mksquashfs, "w") as f:
            f.write(content)
        os.chmod(mksquashfs, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        os.environ["SNAP_ENFORCE_RESQUASHFS"] = "1"
        c.check_squashfs_resquash()
        os.environ.pop("SNAP_ENFORCE_RESQUASHFS")
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

    def test_check_squashfs_resquash_sha512sum_fail(self):
        """Test check_squashfs_resquash() - sha512sum failure"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        # fake sha512sum
        sha512sum = os.path.join(output_dir, "sha512sum")
        content = """#!/bin/sh
bn=`basename "$1"`
if [ "$bn" = "test_1.0_all.snap" ]; then
    echo test error: sha512sum failure
    exit 1
fi
exit 0
"""
        with open(sha512sum, "w") as f:
            f.write(content)
        os.chmod(sha512sum, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        os.environ["SNAP_ENFORCE_RESQUASHFS"] = "1"
        c.check_squashfs_resquash()
        os.environ.pop("SNAP_ENFORCE_RESQUASHFS")
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

    def test_check_squashfs_resquash_sha512sum_fail_repacked(self):
        """Test check_squashfs_resquash() - sha512sum failure (repacked)"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        # fake sha512sum
        sha512sum = os.path.join(output_dir, "sha512sum")
        content = """#!/bin/sh
bn=`basename "$1"`
if [ "$bn" != "test_1.0_all.snap" ]; then
    echo test error: sha512sum failure
    exit 1
fi
echo deadbeef $1
exit 0
"""
        with open(sha512sum, "w") as f:
            f.write(content)
        os.chmod(sha512sum, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        os.environ["SNAP_ENFORCE_RESQUASHFS"] = "1"
        c.check_squashfs_resquash()
        os.environ.pop("SNAP_ENFORCE_RESQUASHFS")
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

    def test_check_squashfs_resquash_sha512sum_mismatch(self):
        """Test check_squashfs_resquash() - sha512sum mismatch (no enforce)"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        # fake sha512sum
        sha512sum = os.path.join(output_dir, "sha512sum")
        content = """#!/bin/sh
bn=`basename "$1"`
if [ "$bn" = "test_1.0_all.snap" ]; then
    echo beefeeee $1
else
    echo deadbeef $1
fi
exit 0
"""
        with open(sha512sum, "w") as f:
            f.write(content)
        os.chmod(sha512sum, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        os.environ["SNAP_ENFORCE_RESQUASHFS"] = "0"
        c.check_squashfs_resquash()
        os.environ.pop("SNAP_ENFORCE_RESQUASHFS")
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_squashfs_resquash_sha512sum_mismatch_enforce(self):
        """Test check_squashfs_resquash() - sha512sum mismatch - enforce"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        # fake sha512sum
        sha512sum = os.path.join(output_dir, "sha512sum")
        content = """#!/bin/sh
bn=`basename "$1"`
if [ "$bn" = "test_1.0_all.snap" ]; then
    echo beefeeee $1
else
    echo deadbeef $1
fi
exit 0
"""
        with open(sha512sum, "w") as f:
            f.write(content)
        os.chmod(sha512sum, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        os.environ["SNAP_ENFORCE_RESQUASHFS"] = "1"
        os.environ["SNAP_DEBUG_RESQUASHFS"] = "1"
        c.check_squashfs_resquash()
        os.environ.pop("SNAP_DEBUG_RESQUASHFS")
        os.environ.pop("SNAP_ENFORCE_RESQUASHFS")
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_repack_checksum"
        expected["error"][name] = {
            "text": "checksums do not match. Please ensure the snap is created with either 'snapcraft pack <DIR>' (using snapcraft >= 2.38) or 'mksquashfs <dir> <snap> -noappend -comp xz -all-root -no-xattrs -no-fragments'. If using electron-builder, please upgrade to latest stable (>= 20.14.7). See https://forum.snapcraft.io/t/automated-reviews-and-snapcraft-2-38/4982/17 for details."
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_resquash_sha512sum_mismatch_override(self):
        """Test check_squashfs_resquash() - sha512sum mismatch - overridden"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        # fake sha512sum
        sha512sum = os.path.join(output_dir, "sha512sum")
        content = """#!/bin/sh
bn=`basename "$1"`
if [ "$bn" = "test_1.0_all.snap" ]; then
    echo beefeeee $1
else
    echo deadbeef $1
fi
exit 0
"""
        with open(sha512sum, "w") as f:
            f.write(content)
        os.chmod(sha512sum, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        os.environ["SNAP_ENFORCE_RESQUASHFS"] = "1"
        os.environ["SNAP_DEBUG_RESQUASHFS"] = "1"

        # add this snap to the override
        from reviewtools.overrides import sec_resquashfs_overrides

        sec_resquashfs_overrides.append("test")
        c.check_squashfs_resquash()
        # then clean up
        sec_resquashfs_overrides.remove("test")

        os.environ.pop("SNAP_DEBUG_RESQUASHFS")
        os.environ.pop("SNAP_ENFORCE_RESQUASHFS")
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_repack_checksum"
        expected["info"][name] = {
            "text": "OK (check not enforced for this snap): checksums do not match. Please ensure the snap is created with either 'snapcraft pack <DIR>' (using snapcraft >= 2.38) or 'mksquashfs <dir> <snap> -noappend -comp xz -all-root -no-xattrs -no-fragments'. If using electron-builder, please upgrade to latest stable (>= 20.14.7). See https://forum.snapcraft.io/t/automated-reviews-and-snapcraft-2-38/4982/17 for details."
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_resquash_sha512sum_mismatch_enforce_os(self):
        """Test check_squashfs_resquash() - sha512sum mismatch - enforce os"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        sy_path = os.path.join(output_dir, "snap.yaml")
        content = """
name: test
version: 0.1
summary: some thing
description: some desc
architectures: [ amd64 ]
type: os
"""
        with open(sy_path, "w") as f:
            f.write(content)

        package = utils.make_snap2(
            output_dir=output_dir, extra_files=["%s:meta/snap.yaml" % sy_path]
        )

        c = SnapReviewSecurity(package)

        # fake sha512sum
        sha512sum = os.path.join(output_dir, "sha512sum")
        content = """#!/bin/sh
bn=`basename "$1"`
if [ "$bn" = "test_1.0_all.snap" ]; then
    echo beefeeee $1
else
    echo deadbeef $1
fi
exit 0
"""
        with open(sha512sum, "w") as f:
            f.write(content)
        os.chmod(sha512sum, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        os.environ["SNAP_ENFORCE_RESQUASHFS"] = "1"
        c.check_squashfs_resquash()
        os.environ.pop("SNAP_ENFORCE_RESQUASHFS")
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_repack_checksum"
        expected["info"][name] = {
            "text": "OK (check not enforced for base and os snaps)"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_resquash_sha512sum_mismatch_enforce_app_override(self):
        """Test check_squashfs_resquash() - sha512sum mismatch - enforce app
           with override.
        """
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        sy_path = os.path.join(output_dir, "snap.yaml")
        content = """
name: chromium
version: 0.1
summary: some thing
description: some desc
architectures: [ amd64 ]
"""
        with open(sy_path, "w") as f:
            f.write(content)

        package = utils.make_snap2(
            output_dir=output_dir, extra_files=["%s:meta/snap.yaml" % sy_path]
        )

        c = SnapReviewSecurity(package)

        # fake sha512sum
        sha512sum = os.path.join(output_dir, "sha512sum")
        content = """#!/bin/sh
bn=`basename "$1"`
if [ "$bn" = "test_1.0_all.snap" ]; then
    echo beefeeee $1
else
    echo deadbeef $1
fi
exit 0
"""
        with open(sha512sum, "w") as f:
            f.write(content)
        os.chmod(sha512sum, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        os.environ["SNAP_ENFORCE_RESQUASHFS"] = "1"
        c.check_squashfs_resquash()
        os.environ.pop("SNAP_ENFORCE_RESQUASHFS")
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_repack_checksum"
        expected["info"][name] = {
            "text": "OK (check not enforced for app snaps with setuid/setgid overrides)"
        }
        self.check_results(report, expected=expected)

    def test_check_squashfs_resquash_sha512sum_mismatch_enforce_app_override_list(self):
        """Test check_squashfs_resquash() - sha512sum mismatch - enforce app
           with override (list).
        """
        # update the overrides
        from reviewtools.overrides import sec_mode_overrides

        sec_mode_overrides["foo"] = {"./test": ["rwsr-xr-x"]}

        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        sy_path = os.path.join(output_dir, "snap.yaml")
        content = """
name: foo
version: 0.1
summary: some thing
description: some desc
architectures: [ amd64 ]
"""
        with open(sy_path, "w") as f:
            f.write(content)

        package = utils.make_snap2(
            output_dir=output_dir, extra_files=["%s:meta/snap.yaml" % sy_path]
        )

        c = SnapReviewSecurity(package)

        # fake sha512sum
        sha512sum = os.path.join(output_dir, "sha512sum")
        content = """#!/bin/sh
bn=`basename "$1"`
if [ "$bn" = "test_1.0_all.snap" ]; then
    echo beefeeee $1
else
    echo deadbeef $1
fi
exit 0
"""
        with open(sha512sum, "w") as f:
            f.write(content)
        os.chmod(sha512sum, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        os.environ["SNAP_ENFORCE_RESQUASHFS"] = "1"
        c.check_squashfs_resquash()
        # clean up
        del sec_mode_overrides["foo"]
        os.environ.pop("SNAP_ENFORCE_RESQUASHFS")
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "security-snap-v2:squashfs_repack_checksum"
        expected["info"][name] = {
            "text": "OK (check not enforced for app snaps with setuid/setgid overrides)"
        }
        self.check_results(report, expected=expected)

    def test_check_debug_resquashfs(self):
        """Test check_debug_resquashfs()"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        repackage = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        r = c._debug_resquashfs(output_dir, package, repackage)
        self.assertTrue("squash fstime for test_1.0_all.snap" in r)
        self.assertTrue("unsquashfs -lls test_1.0_all.snap:" in r)
        self.assertTrue("diff -au " in r)

    def test_check_debug_resquashfs_bad_fstime(self):
        """Test check_debug_resquashfs() - bad unsquashfs -fstime"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        repackage = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        # fake unsquashfs
        unsquashfs = os.path.join(output_dir, "unsquashfs")
        content = """#!/bin/sh
echo test error: unsquashfs failure
exit 1
"""
        with open(unsquashfs, "w") as f:
            f.write(content)
        os.chmod(unsquashfs, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        r = c._debug_resquashfs(output_dir, package, repackage)
        os.environ["PATH"] = old_path
        self.assertTrue(re.search(r"unsquashfs -fstime .*\.snap' failed", r))

    def test_check_debug_resquashfs_bad_lls(self):
        """Test check_debug_resquashfs() - bad unsquashfs -lls"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        repackage = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        # fake unsquashfs
        unsquashfs = os.path.join(output_dir, "unsquashfs")
        content = """#!/bin/sh
if [ "$1" = "-fstime" ]; then
    echo mocked
    exit 0
fi
echo test error: unsquashfs failure
exit 1
"""
        with open(unsquashfs, "w") as f:
            f.write(content)
        os.chmod(unsquashfs, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        r = c._debug_resquashfs(output_dir, package, repackage)
        os.environ["PATH"] = old_path
        self.assertTrue(re.search(r"unsquashfs -lls .*\.snap' failed", r))

    def test_check_squashfs_files(self):
        """Test check_squashfs_files()"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        c.check_squashfs_files()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_squashfs_files_unsquashfs_failed(self):
        """Test check_squashfs_files()"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewSecurity(package)

        # fake unsquashfs
        unsquashfs = os.path.join(output_dir, "unsquashfs")
        content = """#!/bin/sh
echo test error: unsquashfs failure
exit 1
"""
        with open(unsquashfs, "w") as f:
            f.write(content)
        os.chmod(unsquashfs, 0o775)

        old_path = os.environ["PATH"]
        if old_path:
            os.environ["PATH"] = "%s:%s" % (output_dir, os.environ["PATH"])
        else:
            os.environ["PATH"] = output_dir  # pragma: nocover

        c.check_squashfs_files()
        os.environ["PATH"] = old_path
        report = c.review_report
        expected_counts = {"info": None, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)
