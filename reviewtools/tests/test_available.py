"""test_available.py: tests for the available module"""
#
# Copyright (C) 2018 Canonical Ltd.
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
import tempfile

import reviewtools.available as available
import reviewtools.store as store
import reviewtools.usn as usn

from reviewtools.common import read_file_as_json_dict, recursive_rm


class TestAvailable(TestCase):
    """Tests for the updates available functions."""

    def setUp(self):
        self.secnot_db = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.store_db = read_file_as_json_dict("./tests/test-store-unittest-1.db")
        errors = {}
        self.pkg_db = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 0)

        os.environ["RT_SEND_EMAIL"] = "0"

        self.tmpdir = None

    def tearDown(self):
        if self.tmpdir is not None:
            recursive_rm(self.tmpdir)

    def test_check__secnot_report_for_pkg(self):
        """Test _secnot_report_for_pkg()"""
        res = available._secnot_report_for_pkg(self.pkg_db, {})
        needle = """
Revision r11 (amd64; channels: stable, candidate, beta)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1

Revision r12 (i386; channels: stable, candidate, beta)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1

Revision r13 (amd64; channels: edge)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1

Revision r14 (i386; channels: edge)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1
"""
        self.assertTrue(needle in res)

    def test_check__secnot_report_for_pkg_rev_no_secnots(self):
        """Test _secnot_report_for_pkg() - rev no secnots"""
        self.pkg_db["revisions"]["11"]["secnot-report"] = {}
        res = available._secnot_report_for_pkg(self.pkg_db, {})
        self.assertFalse(" r11 " in res)

    def test_check__secnot_report_for_pkg_no_urls(self):
        """Test _secnot_report_for_pkg() - no urls"""
        for rev in self.pkg_db["revisions"]:
            self.pkg_db["revisions"][rev]["secnot-report"] = {}
        res = available._secnot_report_for_pkg(self.pkg_db, {})
        self.assertEqual(res, "")

    def test_check__secnot_report_for_pkg_only_new_secnot(self):
        """Test _secnot_report_for_pkg() - only new secnot"""
        seen_db = {
            "0ad": {
                "11": ["3501-1", "3602-1"],
                "12": ["3501-1", "3602-1"],
                "13": ["3501-1", "3602-1"],
                "14": ["3501-1", "3602-1"],
            }
        }
        res = available._secnot_report_for_pkg(self.pkg_db, seen_db)
        needle = """
Revision r11 (amd64; channels: stable, candidate, beta)
 * libtiff5: 3606-1

Revision r12 (i386; channels: stable, candidate, beta)
 * libtiff5: 3606-1

Revision r13 (amd64; channels: edge)
 * libtiff5: 3606-1

Revision r14 (i386; channels: edge)
 * libtiff5: 3606-1
"""
        self.assertTrue(needle in res)

    def test_check__secnot_report_for_pkg_only_new_secnot_budgie(self):
        """Test _secnot_report_for_pkg() - only new secnot budgie"""
        self.secnot_db = usn.read_usn_db("./tests/test-usn-budgie-2.db")
        self.store_db = read_file_as_json_dict("./tests/test-store-budgie.db")
        errors = {}
        self.pkg_db = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 0)

        seen_db = {
            "ubuntu-budgie-welcome": {
                "11": [
                    "3598-1",
                    "3602-1",
                    "3606-1",
                    "3610-1",
                    "3611-1",
                    "3622-1",
                    "3628-1",
                ],
                "12": [
                    "3598-1",
                    "3602-1",
                    "3606-1",
                    "3610-1",
                    "3611-1",
                    "3622-1",
                    "3628-1",
                ],
                "43": [
                    "3598-1",
                    "3602-1",
                    "3606-1",
                    "3610-1",
                    "3611-1",
                    "3622-1",
                    "3628-1",
                ],
                "44": [
                    "3598-1",
                    "3602-1",
                    "3606-1",
                    "3610-1",
                    "3611-1",
                    "3622-1",
                    "3628-1",
                ],
                "45": [
                    "3598-1",
                    "3602-1",
                    "3606-1",
                    "3610-1",
                    "3611-1",
                    "3622-1",
                    "3628-1",
                ],
                "46": [
                    "3598-1",
                    "3602-1",
                    "3606-1",
                    "3610-1",
                    "3611-1",
                    "3622-1",
                    "3628-1",
                ],
            }
        }
        res = available._secnot_report_for_pkg(self.pkg_db, seen_db)
        needle = """
Revision r11 (amd64; channels: candidate, beta)
 * gir1.2-javascriptcoregtk-4.0: 3635-1
 * gir1.2-webkit2-4.0: 3635-1
 * libjavascriptcoregtk-4.0-18: 3635-1
 * libwebkit2gtk-4.0-37: 3635-1

Revision r12 (i386; channels: candidate, beta)
 * gir1.2-javascriptcoregtk-4.0: 3635-1
 * gir1.2-webkit2-4.0: 3635-1
 * libjavascriptcoregtk-4.0-18: 3635-1
 * libwebkit2gtk-4.0-37: 3635-1
"""
        self.assertTrue(needle in res)

    def test_check__email_report_for_pkg(self):
        """Test _email_report_for_pkg()"""
        (to_addr, subj, body) = available._email_report_for_pkg(self.pkg_db, {})

        for eml in ["olivier.tilloy@canonical.com"]:
            self.assertTrue(eml in to_addr)

        self.assertTrue("0ad" in subj)

        for pkg in ["libtiff5", "libxcursor1"]:
            self.assertTrue(pkg in body)
        for sn in ["3501-1", "3602-1", "3606-1"]:
            self.assertTrue(sn in body)

    def test_check__email_report_for_pkg_no_urls(self):
        """Test _email_report_for_pkg() - no urls"""
        for rev in self.pkg_db["revisions"]:
            self.pkg_db["revisions"][rev]["secnot-report"] = {}
        (to_addr, subj, body) = available._email_report_for_pkg(self.pkg_db, {})
        self.assertEqual(to_addr, None)
        self.assertEqual(subj, None)
        self.assertEqual(body, None)

    def test_check__email_report_for_pkg_with_collaborators(self):
        """Test _email_report_for_pkg() - with collaborators"""
        self.pkg_db["collaborators"] = ["testme@example.com"]
        self.pkg_db["uploaders"] = ["testme2@example.com"]
        (to_addr, subj, body) = available._email_report_for_pkg(self.pkg_db, {})
        self.assertTrue("testme@example.com" in to_addr)
        # collaborators supercede uploaders
        self.assertFalse("testme2@example.com" in to_addr)

    def test_check__email_report_for_pkg_with_uploaders(self):
        """Test _email_report_for_pkg() - with uploaders"""
        self.pkg_db["uploaders"] = ["testme@example.com"]
        (to_addr, subj, body) = available._email_report_for_pkg(self.pkg_db, {})
        self.assertTrue("testme@example.com" in to_addr)

    def test_check__email_report_for_pkg_with_additional(self):
        """Test _email_report_for_pkg() - with additional"""
        self.pkg_db["additional"] = ["testme@example.com"]
        (to_addr, subj, body) = available._email_report_for_pkg(self.pkg_db, {})
        self.assertTrue("testme@example.com" in to_addr)

    def test_check_read_seen_db(self):
        """Test read_seen_db()"""
        self.tmpdir = tempfile.mkdtemp()
        tmp = os.path.join(self.tmpdir, "seen.db")
        res = available.read_seen_db(tmp)
        self.assertEqual(len(res), 0)

    def test_check__update_seen(self):
        """Test _update_seen()"""
        self.tmpdir = tempfile.mkdtemp()
        tmp = os.path.join(self.tmpdir, "seen.db")
        res = available.read_seen_db(tmp)
        self.assertEqual(len(res), 0)
        seen_db = res

        available._update_seen(tmp, seen_db, self.pkg_db)

        res = available.read_seen_db(tmp)
        self.assertEqual(len(res), 1)
        self.assertTrue("0ad" in res)

        expected_db = {
            "0ad": {
                "11": ["3501-1", "3602-1", "3606-1"],
                "12": ["3501-1", "3602-1", "3606-1"],
                "13": ["3501-1", "3602-1", "3606-1"],
                "14": ["3501-1", "3602-1", "3606-1"],
            }
        }
        self.assertEqual(len(expected_db), len(res))

        for pkg in expected_db:
            self.assertTrue(pkg in res)
            self.assertEqual(len(expected_db[pkg]), len(res[pkg]))
            for rev in expected_db[pkg]:
                self.assertTrue(rev in res[pkg])
                self.assertEqual(len(expected_db[pkg][rev]), len(res[pkg][rev]))
                for secnot in expected_db[pkg][rev]:
                    self.assertTrue(secnot in res[pkg][rev])

    def test_check__update_seen_no_secnots(self):
        """Test _update_seen() - no secnots"""
        self.tmpdir = tempfile.mkdtemp()
        tmp = os.path.join(self.tmpdir, "seen.db")
        res = available.read_seen_db(tmp)
        self.assertEqual(len(res), 0)
        seen_db = res

        for rev in self.pkg_db["revisions"]:
            self.pkg_db["revisions"][rev]["secnot-report"] = {}
        available._update_seen(tmp, seen_db, self.pkg_db)

        res = available.read_seen_db(tmp)
        self.assertEqual(len(res), 1)
        self.assertTrue("0ad" in res)
        self.assertEqual(len(res["0ad"]), 0)

    def test_check__update_seen_remove_old_revision(self):
        """Test _update_seen() - remove old revision"""
        self.tmpdir = tempfile.mkdtemp()
        tmp = os.path.join(self.tmpdir, "seen.db")
        res = available.read_seen_db(tmp)
        self.assertEqual(len(res), 0)

        seen_db = {
            "0ad": {"9": ["3401-1"], "10": ["3401-1"], "8": ["3401-1"], "7": ["3401-1"]}
        }
        available._update_seen(tmp, seen_db, self.pkg_db)

        res = available.read_seen_db(tmp)
        self.assertEqual(len(res), 1)
        self.assertTrue("0ad" in res)
        self.assertEqual(len(res["0ad"]), 4)

        for r in ["7", "8", "9", "10"]:
            self.assertFalse(r in seen_db["0ad"])

    def test_check_scan_shared_publishers(self):
        """Test scan_shared_publishers()"""
        fn = "./tests/test-store-missing-shared-override.db"
        res = available.scan_shared_publishers(fn)
        self.assertTrue(len(res) > 0)
        for p in [
            "missing-publisher-overrides-snap-1",
            "missing-publisher-overrides-snap-2",
        ]:
            self.assertTrue(p in res)

    def test_check_scan_snap(self):
        """Test scan_snap()"""
        secnot_fn = "./tests/test-usn-unittest-1.db"
        snap_fn = "./tests/test-snapcraft-manifest-unittest_0_amd64.snap"
        res = available.scan_snap(secnot_fn, snap_fn)
        self.assertTrue(len(res) > 0)
        self.assertTrue("3501-1" in res)

    def test_check_scan_snap_core(self):
        """Test scan_snap() - core"""
        secnot_fn = "./tests/test-usn-core-with-dpkg-list.db"
        snap_fn = "./tests/test-core_16-2.37.2_amd64.snap"
        res = available.scan_snap(secnot_fn, snap_fn)
        self.assertTrue(len(res) > 0)
        self.assertTrue("3323-1" in res)

    def test_check_scan_snap_dpkg_list_app(self):
        """Test scan_snap() - dpkg.list app"""
        secnot_fn = "./tests/test-usn-core-with-dpkg-list.db"
        snap_fn = "./tests/test-dpkg-list-app_1.0_amd64.snap"
        res = available.scan_snap(secnot_fn, snap_fn)
        self.assertTrue(len(res) > 0)
        self.assertTrue("3323-1" in res)

    def test_check_scan_snap_kernel(self):
        """Test scan_snap() - kernel"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["pc-kernel"] = {"linux-image-generic": "auto-kernel"}
        secnot_fn = "./tests/test-usn-kernel.db"
        snap_fn = "./tests/pc-kernel_4.4.0-141.167_amd64.snap"
        res = available.scan_snap(secnot_fn, snap_fn)
        self.assertTrue(len(res) > 0)
        self.assertTrue("3879-1" in res)

    def test_check_scan_snap_kernel_abi(self):
        """Test scan_snap() - kernel abi"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["linux-generic-bbb"] = {
            "linux-image-generic": "auto-kernelabi"
        }
        secnot_fn = "./tests/test-usn-kernel.db"
        snap_fn = "./tests/linux-generic-bbb_4.4.0-140-1_armhf.snap"
        res = available.scan_snap(secnot_fn, snap_fn)
        self.assertTrue(len(res) > 0)
        self.assertTrue("3848-1" in res)
        self.assertTrue("3879-1" in res)

    def test_check_scan_snap_canonical_snap(self):
        """Test scan_snap() - canonical snap - network-manager"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["network-manager"] = {"network-manager": "auto"}
        secnot_fn = "./tests/test-usn-network-manager.db"
        snap_fn = "./tests/network-manager_1.10.6-2ubuntu1.0+dbce8fd2_amd64.snap"
        res = available.scan_snap(secnot_fn, snap_fn)
        self.assertTrue(len(res) > 0)
        self.assertTrue("3807-1" in res)

    def test_check_scan_store(self):
        """Test scan_store()"""
        secnot_fn = "./tests/test-usn-unittest-1.db"
        store_fn = "./tests/test-store-unittest-1.db"
        (sent, errors) = available.scan_store(secnot_fn, store_fn, None, None)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        for eml in ["olivier.tilloy@canonical.com"]:
            self.assertTrue(eml in to_addr)

        self.assertTrue("0ad contains outdated Ubuntu packages" in subj)
        self.assertTrue("built with packages from the Ubuntu" in body)

        for pkg in ["libtiff5", "libxcursor1"]:
            self.assertTrue(pkg in body)
        for sn in ["3501-1", "3602-1", "3606-1"]:
            self.assertTrue(sn in body)

    def test_check_scan_store_with_seen(self):
        """Test scan_store() - with seen"""
        secnot_fn = "./tests/test-usn-unittest-1.db"
        store_fn = "./tests/test-store-unittest-1.db"
        self.tmpdir = tempfile.mkdtemp()
        seen_fn = os.path.join(self.tmpdir, "seen.db")
        (sent, errors) = available.scan_store(secnot_fn, store_fn, seen_fn, None)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        for eml in ["olivier.tilloy@canonical.com"]:
            self.assertTrue(eml in to_addr)

        self.assertTrue("0ad" in subj)

        for pkg in ["libtiff5", "libxcursor1"]:
            self.assertTrue(pkg in body)
        for sn in ["3501-1", "3602-1", "3606-1"]:
            self.assertTrue(sn in body)

    def test_check_scan_store_with_pkgname(self):
        """Test scan_store() - with pkgname"""
        secnot_fn = "./tests/test-usn-unittest-1.db"
        store_fn = "./tests/test-store-unittest-1.db"
        (sent, errors) = available.scan_store(secnot_fn, store_fn, None, "not-there")
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 0)

    def test_check_scan_store_with_pkgname_bad_publisher(self):
        """Test scan_store() - with pkgname and bad publisher"""
        secnot_fn = "./tests/test-usn-unittest-1.db"
        store_fn = "./tests/test-store-unittest-bad-1.db"
        (sent, errors) = available.scan_store(secnot_fn, store_fn, None, "1ad")
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(sent), 0)

    def test_check_scan_store_kernel(self):
        """Test scan_store() - kernel"""
        secnot_fn = "./tests/test-usn-kernel.db"
        store_fn = "./tests/test-store-kernel.db"
        (sent, errors) = available.scan_store(secnot_fn, store_fn, None, None)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        for eml in ["foo@example.com"]:
            self.assertTrue(eml in to_addr)
        self.assertTrue("using sources based on a kernel" in body)
        self.assertTrue("linux-image-generic" in body)

        self.assertTrue("linux-generic-bbb built from outdated Ubuntu kernel" in subj)

        for sn in ["3848-1", "3879-1"]:
            self.assertTrue(sn in body)

    def test_check_scan_store_lp1841848_allbinaries(self):
        """Test scan_store() - lp1841848 (allbinaries)"""
        secnot_fn = "./tests/test-usn-unittest-lp1841848.db"
        store_fn = "./tests/test-store-unittest-lp1841848.db"
        (sent, errors) = available.scan_store(secnot_fn, store_fn, None, None)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        self.assertEqual(to_addr, None)
        self.assertEqual(subj, None)
        self.assertEqual(body, None)

    def test_check_scan_store_lp1841848_allbinaries_needed(self):
        """Test scan_store() - lp1841848 (allbinaries needed)"""
        secnot_fn = "./tests/test-usn-unittest-lp1841848.db"
        store_fn = "./tests/test-store-unittest-lp1841848-needed.db"
        (sent, errors) = available.scan_store(secnot_fn, store_fn, None, None)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        eml = "test.me@example.com"
        self.assertTrue(eml in to_addr)
        self.assertTrue("libreoffice-style-tango: 4102-1" in body)
        self.assertTrue("uno-libs3: 4102-1" in body)

    def test_check_scan_store_lp1841848_allbinaries_bad_epoch(self):
        """Test scan_store() - lp1841848 (allbinaries with bad epoch)"""
        secnot_fn = "./tests/test-usn-unittest-lp1841848-incorrect-epoch.db"
        store_fn = "./tests/test-store-unittest-lp1841848.db"
        (sent, errors) = available.scan_store(secnot_fn, store_fn, None, None)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]

        self.assertEqual(to_addr, None)
        self.assertEqual(subj, None)
        self.assertEqual(body, None)

    def test_check_scan_store_lp1841848_allbinaries_bad_epoch_needed(self):
        """Test scan_store() - lp1841848 (allbinaries with bad epoch needed)"""
        secnot_fn = "./tests/test-usn-unittest-lp1841848-incorrect-epoch.db"
        store_fn = "./tests/test-store-unittest-lp1841848-needed.db"
        (sent, errors) = available.scan_store(secnot_fn, store_fn, None, None)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        eml = "test.me@example.com"
        self.assertTrue(eml in to_addr)
        self.assertTrue("libreoffice-style-tango: 4102-1" in body)
        self.assertTrue("uno-libs3: 4102-1" in body)

    def test_check_scan_store_lp1841848_allbinaries_bad_epoch2(self):
        """Test scan_store() - lp1841848 (allbinaries with bad epoch2)"""
        secnot_fn = "./tests/test-usn-unittest-lp1841848-incorrect-epoch2.db"
        store_fn = "./tests/test-store-unittest-lp1841848.db"
        (sent, errors) = available.scan_store(secnot_fn, store_fn, None, None)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]

        self.assertEqual(to_addr, None)
        self.assertEqual(subj, None)
        self.assertEqual(body, None)

    def test_check_scan_store_lp1841848_unmatched_binver(self):
        """Test scan_store() - lp1841848 (unmatched binary version)"""
        secnot_fn = "./tests/test-usn-unittest-lp1841848-unmatched-binver.db"
        store_fn = "./tests/test-store-unittest-lp1841848.db"
        (sent, errors) = available.scan_store(secnot_fn, store_fn, None, None)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]

        self.assertEqual(to_addr, None)
        self.assertEqual(subj, None)
        self.assertEqual(body, None)

    def test_check_scan_store_lp1841848_no_allbinaries(self):
        """Test scan_store() - lp1841848 (no allbinaries)"""
        secnot_fn = "./tests/test-usn-unittest-lp1841848-noallbin.db"
        store_fn = "./tests/test-store-unittest-lp1841848.db"
        (sent, errors) = available.scan_store(secnot_fn, store_fn, None, None)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        self.assertEqual(to_addr, None)
        self.assertEqual(subj, None)
        self.assertEqual(body, None)

    def test_check_scan_store_lp1841848_no_allbinaries_needed(self):
        """Test scan_store() - lp1841848 (no allbinaries needed)"""
        secnot_fn = "./tests/test-usn-unittest-lp1841848-noallbin.db"
        store_fn = "./tests/test-store-unittest-lp1841848-needed.db"
        (sent, errors) = available.scan_store(secnot_fn, store_fn, None, None)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        eml = "test.me@example.com"
        self.assertTrue(eml in to_addr)
        self.assertTrue("libreoffice-style-tango: 4102-1" in body)
        self.assertTrue("uno-libs3: 4102-1" in body)

    def test_check_scan_store_lp1841848_unmatched_binver2(self):
        """Test scan_store() - lp1841848 (unmatched binary version no all binaries)"""
        secnot_fn = "./tests/test-usn-unittest-lp1841848-unmatched-binver-noallbin.db"
        store_fn = "./tests/test-store-unittest-lp1841848.db"
        (sent, errors) = available.scan_store(secnot_fn, store_fn, None, None)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]

        self.assertEqual(to_addr, None)
        self.assertEqual(subj, None)
        self.assertEqual(body, None)

    def test_check_scan_store_empty_manifest(self):
        """Test scan_store() - empty manifest"""
        secnot_fn = "./tests/test-usn-unittest-1.db"
        store_fn = "./tests/test-store-unittest-bare.db"
        (sent, errors) = available.scan_store(secnot_fn, store_fn, None, None)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 0)
