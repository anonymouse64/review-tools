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
        self.secnot_fn = "./tests/test-usn-unittest-1.db"
        self.secnot_db = usn.read_usn_db(self.secnot_fn)

        self.secnot_build_and_stage_pkgs_fn = "./tests/test-usn-unittest-build-pkgs.db"
        self.secnot_build_and_stage_pkgs_db = usn.read_usn_db(
            self.secnot_build_and_stage_pkgs_fn
        )

        self.secnot_build_pkgs_only_fn = "./tests/test-usn-unittest-build-pkgs-only.db"
        self.secnot_build_pkgs_only_db = usn.read_usn_db(self.secnot_build_pkgs_only_fn)

        self.secnot_kernel_fn = "./tests/test-usn-kernel.db"
        self.secnot_kernel_db = usn.read_usn_db(self.secnot_kernel_fn)

        self.secnot_kernel_and_build_pkgs_fn = (
            "./tests/test-usn-kernel-and-build-pkgs.db"
        )
        self.secnot_kernel_and_build_pkgs_db = usn.read_usn_db(
            self.secnot_kernel_and_build_pkgs_fn
        )

        self.secnot_budgie_fn = "./tests/test-usn-budgie-2.db"
        self.secnot_budgie_db = usn.read_usn_db(self.secnot_budgie_fn)

        self.secnot_lp1841848_fn = "./tests/test-usn-unittest-lp1841848.db"
        self.secnot_lp1841848_db = usn.read_usn_db(self.secnot_lp1841848_fn)

        self.secnot_lp1841848_incorrect_epoch_fn = (
            "./tests/test-usn-unittest-lp1841848-incorrect-epoch.db"
        )

        self.secnot_core_with_dpkg_list_fn = "./tests/test-usn-core-with-dpkg-list.db"

        self.store_fn = "./tests/test-store-unittest-1.db"
        self.store_db = read_file_as_json_dict(self.store_fn)

        self.rock_store_fn = "./tests/test-rocks-store-unittest-1.db"
        self.rock_store_db = read_file_as_json_dict(self.rock_store_fn)

        self.kernel_store_fn = "./tests/test-store-kernel.db"
        self.kernel_store_db = read_file_as_json_dict(self.kernel_store_fn)

        self.budgie_store_fn = "./tests/test-store-budgie.db"
        self.budgie_store_db = read_file_as_json_dict(self.budgie_store_fn)

        self.lp1841848_needed_store_fn = (
            "./tests/test-store-unittest-lp1841848-needed.db"
        )
        self.lp1841848_store_fn = "./tests/test-store-unittest-lp1841848.db"

        self.rock_fn = "./tests/test-rock-redis_5.0-20.04.tar"
        self.rock_non_lts_based_fn = "./tests/test-rock-non-lts.tar"
        self.seen_db = "seen.db"
        errors = {}
        self.pkg_db = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 0)

        os.environ["RT_SEND_EMAIL"] = "0"

        self.tmpdir = None

    def tearDown(self):
        if self.tmpdir is not None:
            recursive_rm(self.tmpdir)

    def test_check__secnot_report_for_pkg_with_build_and_stage_pkgs(self):
        """Test _secnot_report_for_pkg() - build and stage packages"""
        errors = {}
        pkg_db = store.get_pkg_revisions(
            self.store_db[0], self.secnot_build_and_stage_pkgs_db, errors
        )
        self.assertEqual(len(errors), 0)

        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(pkg_db, {})
        needle = """A scan of this snap shows that it was built with packages from the Ubuntu
archive that have since received security updates. The following lists new
USNs for affected binary packages in each snap revision:

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

Revision r15 (amd64; channels: edge)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1

Revision r16 (i386; channels: edge)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1

Revision r17 (amd64; channels: edge)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1

In addition, the following lists new USNs for affected build packages in
each snap revision:

Revision r11 (amd64; channels: stable, candidate, beta)
 * snapcraft: 5501-1

Revision r12 (i386; channels: stable, candidate, beta)
 * snapcraft: 5501-1

Revision r13 (amd64; channels: edge)
 * snapcraft: 5501-1

Revision r14 (i386; channels: edge)
 * snapcraft: 5501-1

Revision r15 (amd64; channels: edge)
 * snapcraft: 5501-1

Revision r16 (i386; channels: edge)
 * snapcraft: 5501-1

"""
        self.assertIn(needle, body)
        for line in body.splitlines():
            # text width of emails should not exceed 75
            self.assertTrue(len(line) <= 75)
        self.assertTrue(contains_stage_pkgs)
        self.assertTrue(contains_build_pkgs)
        self.assertEqual(
            "0ad contains and was built with outdated Ubuntu packages", subj
        )

    def test_check__secnot_report_for_pkg_with_build_pkgs_only(self):
        """Test _secnot_report_for_pkg() - only build packages"""
        errors = {}
        pkg_db = store.get_pkg_revisions(
            self.store_db[0], self.secnot_build_pkgs_only_db, errors
        )
        self.assertEqual(len(errors), 0)
        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(pkg_db, {})
        needle = """A scan of this snap shows that it was built with packages from the Ubuntu
archive that have since received security updates. The following lists new
USNs for affected build packages in each snap revision:

Revision r11 (amd64; channels: stable, candidate, beta)
 * snapcraft: 5501-1

Revision r12 (i386; channels: stable, candidate, beta)
 * snapcraft: 5501-1

Revision r13 (amd64; channels: edge)
 * snapcraft: 5501-1

Revision r14 (i386; channels: edge)
 * snapcraft: 5501-1

Revision r15 (amd64; channels: edge)
 * snapcraft: 5501-1

Revision r16 (i386; channels: edge)
 * snapcraft: 5501-1
"""
        needle_for_template_in_addition = """
In addition, the following lists new USNs for affected build packages in
each snap revision:
"""
        self.assertIn(needle, body)
        for line in body.splitlines():
            # text width of emails should not exceed 75
            self.assertTrue(len(line) <= 75)
        self.assertNotIn(needle_for_template_in_addition, body)
        self.assertFalse(contains_stage_pkgs)
        self.assertTrue(contains_build_pkgs)
        self.assertEqual("0ad was built with outdated Ubuntu packages", subj)

    def test_check__secnot_report_for_pkg(self):
        """Test _secnot_report_for_pkg() - only stage packages"""
        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(self.pkg_db, {})
        needle_for_revisions = """A scan of this snap shows that it was built with packages from the Ubuntu
archive that have since received security updates. The following lists new
USNs for affected binary packages in each snap revision:

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
        needle_for_template_in_addition = """
In addition, the following lists new USNs for affected build packages in
each snap revision:
            """
        self.assertIn(needle_for_revisions, body)
        for line in body.splitlines():
            # text width of emails should not exceed 75
            self.assertTrue(len(line) <= 75)
        self.assertNotIn(needle_for_template_in_addition, body)
        self.assertTrue(contains_stage_pkgs)
        self.assertFalse(contains_build_pkgs)
        self.assertEqual("0ad contains outdated Ubuntu packages", subj)

    def test_check__secnot_report_for_pkg_rev_no_secnots(self):
        """Test _secnot_report_for_pkg() - rev no secnots"""
        self.pkg_db["revisions"]["11"]["secnot-report"] = {}
        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(self.pkg_db, {})
        self.assertNotIn("Revision r11", body)
        self.assertTrue(contains_stage_pkgs)
        self.assertFalse(contains_build_pkgs)
        self.assertEqual("0ad contains outdated Ubuntu packages", subj)

    def test_check__secnot_report_for_pkg_no_urls(self):
        """Test _secnot_report_for_pkg() - no urls"""
        for rev in self.pkg_db["revisions"]:
            self.pkg_db["revisions"][rev]["secnot-report"] = {}
        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(self.pkg_db, {})
        self.assertEqual(body, "")
        self.assertFalse(contains_stage_pkgs)
        self.assertFalse(contains_build_pkgs)
        self.assertEqual("", subj)

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
        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(self.pkg_db, seen_db)
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
        self.assertIn(needle, body)
        self.assertTrue(contains_stage_pkgs)
        self.assertFalse(contains_build_pkgs)
        self.assertEqual("0ad contains outdated Ubuntu packages", subj)

    def test_check__secnot_report_for_pkg_only_build_pkg_new_secnot(self):
        """Test _secnot_report_for_pkg() - only new secnot for build pkg"""
        errors = {}
        self.pkg_db = store.get_pkg_revisions(
            self.store_db[0], self.secnot_build_pkgs_only_db, errors
        )

        seen_db = {
            "0ad": {
                "11": ["3501-1", "3602-1"],
                "12": ["3501-1", "3602-1"],
                "13": ["3501-1", "3602-1"],
                "14": ["3501-1", "3602-1"],
            }
        }
        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(self.pkg_db, seen_db)
        needle = """
Revision r11 (amd64; channels: stable, candidate, beta)
 * snapcraft: 5501-1

Revision r12 (i386; channels: stable, candidate, beta)
 * snapcraft: 5501-1

Revision r13 (amd64; channels: edge)
 * snapcraft: 5501-1

Revision r14 (i386; channels: edge)
 * snapcraft: 5501-1

Revision r15 (amd64; channels: edge)
 * snapcraft: 5501-1

Revision r16 (i386; channels: edge)
 * snapcraft: 5501-1
"""
        needle_for_template_in_addition = """In addition, the following lists new USNs for affected build packages in
each snap revision
"""
        self.assertIn(needle, body)
        self.assertNotIn(needle_for_template_in_addition, body)
        self.assertFalse(contains_stage_pkgs)
        self.assertTrue(contains_build_pkgs)
        self.assertEqual("0ad was built with outdated Ubuntu packages", subj)

    def test_check__secnot_report_for_pkg_stage_and_build_pkg_new_secnot(self):
        """Test _secnot_report_for_pkg() - new secnot for build and
        staged pkg"""
        errors = {}
        self.pkg_db = store.get_pkg_revisions(
            self.store_db[0], self.secnot_build_and_stage_pkgs_db, errors
        )

        seen_db = {
            "0ad": {
                "11": ["3501-1", "3602-1"],
                "12": ["3501-1", "3602-1"],
                "13": ["3501-1", "3602-1"],
                "14": ["3501-1", "3602-1"],
            }
        }
        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(self.pkg_db, seen_db)
        needle = """A scan of this snap shows that it was built with packages from the Ubuntu
archive that have since received security updates. The following lists new
USNs for affected binary packages in each snap revision:

Revision r11 (amd64; channels: stable, candidate, beta)
 * libtiff5: 3606-1

Revision r12 (i386; channels: stable, candidate, beta)
 * libtiff5: 3606-1

Revision r13 (amd64; channels: edge)
 * libtiff5: 3606-1

Revision r14 (i386; channels: edge)
 * libtiff5: 3606-1

Revision r15 (amd64; channels: edge)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1

Revision r16 (i386; channels: edge)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1

Revision r17 (amd64; channels: edge)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1

In addition, the following lists new USNs for affected build packages in
each snap revision:

Revision r11 (amd64; channels: stable, candidate, beta)
 * snapcraft: 5501-1

Revision r12 (i386; channels: stable, candidate, beta)
 * snapcraft: 5501-1

Revision r13 (amd64; channels: edge)
 * snapcraft: 5501-1

Revision r14 (i386; channels: edge)
 * snapcraft: 5501-1

Revision r15 (amd64; channels: edge)
 * snapcraft: 5501-1

Revision r16 (i386; channels: edge)
 * snapcraft: 5501-1
"""
        self.assertIn(needle, body)
        self.assertTrue(contains_stage_pkgs)
        self.assertTrue(contains_build_pkgs)
        self.assertEqual(
            "0ad contains and was built with outdated Ubuntu packages", subj
        )

    def test_check__secnot_report_for_pkg_build_pkg_in_seen_db(self):
        """Test _secnot_report_for_pkg() - new secnot for staged pkg, build in
        seen-db"""
        errors = {}
        self.pkg_db = store.get_pkg_revisions(
            self.store_db[0], self.secnot_build_and_stage_pkgs_db, errors
        )

        seen_db = {
            "0ad": {
                "11": ["3501-1", "3602-1", "5501-1"],
                "12": ["3501-1", "3602-1", "5501-1"],
                "13": ["3501-1", "3602-1", "5501-1"],
                "14": ["3501-1", "3602-1", "5501-1"],
                "15": ["5501-1"],
                "16": ["5501-1"],
            }
        }
        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(self.pkg_db, seen_db)
        needle = """A scan of this snap shows that it was built with packages from the Ubuntu
archive that have since received security updates. The following lists new
USNs for affected binary packages in each snap revision:

Revision r11 (amd64; channels: stable, candidate, beta)
 * libtiff5: 3606-1

Revision r12 (i386; channels: stable, candidate, beta)
 * libtiff5: 3606-1

Revision r13 (amd64; channels: edge)
 * libtiff5: 3606-1

Revision r14 (i386; channels: edge)
 * libtiff5: 3606-1

Revision r15 (amd64; channels: edge)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1

Revision r16 (i386; channels: edge)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1

Revision r17 (amd64; channels: edge)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1
"""
        needle_for_template_in_addition = """
In addition, the following lists new USNs for affected build packages in
each snap revision:
"""
        self.assertIn(needle, body)
        self.assertNotIn(needle_for_template_in_addition, body)
        self.assertTrue(contains_stage_pkgs)
        self.assertFalse(contains_build_pkgs)
        self.assertEqual("0ad contains outdated Ubuntu packages", subj)

    def test_check__secnot_report_for_kernel_only_new_secnot(self):
        """Test _secnot_report_for_pkg() - new secnot for kernel"""
        errors = {}
        self.pkg_db = store.get_pkg_revisions(
            self.kernel_store_db[0], self.secnot_kernel_db, errors
        )
        seen_db = {"linux-generic-bbb": {"12": ["3848-1"]}}
        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(self.pkg_db, seen_db)
        needle = """
Revision r12 (armhf; channels: stable, beta)
 * linux-image-generic: 3879-1
"""
        self.assertIn(needle, body)
        self.assertTrue(contains_stage_pkgs)
        self.assertFalse(contains_build_pkgs)
        self.assertEqual("linux-generic-bbb built from outdated Ubuntu kernel", subj)

    def test_check__secnot_report_for_kernel_only_build_pkg_new_secnot(self):
        """Test _secnot_report_for_pkg() - only new secnot for build pkg"""
        errors = {}
        self.pkg_db = store.get_pkg_revisions(
            self.kernel_store_db[0], self.secnot_build_pkgs_only_db, errors
        )

        seen_db = {"linux-generic-bbb": {"12": ["3848-1"]}}
        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(self.pkg_db, seen_db)
        needle = """
Revision r12 (armhf; channels: stable, beta)
 * snapcraft: 5501-1
"""
        needle_for_template_in_addition = """In addition, the following lists new
        USNs for affected build packages in
each snap revision
"""
        self.assertIn(needle, body)
        self.assertNotIn(needle_for_template_in_addition, body)
        self.assertNotIn("3848-1", body)
        self.assertFalse(contains_stage_pkgs)
        self.assertTrue(contains_build_pkgs)
        self.assertEqual(
            "linux-generic-bbb was built with outdated Ubuntu packages", subj
        )

    def test_check__secnot_report_for_kernel_stage_and_build_pkg_new_secnot(self):
        """Test _secnot_report_for_pkg() - new secnot for build and
        staged pkg"""
        errors = {}
        self.pkg_db = store.get_pkg_revisions(
            self.kernel_store_db[0], self.secnot_kernel_and_build_pkgs_db, errors
        )

        seen_db = {"linux-generic-bbb": {"12": ["3848-1", "3602-1"]}}
        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(self.pkg_db, seen_db)
        needle = """A scan of this snap shows that it was built using sources based on a kernel
from the Ubuntu archive that has since received security updates. The
following lists new USNs for the Ubuntu kernel that the snap is based on in
each snap revision:

Revision r12 (armhf; channels: stable, beta)
 * linux-image-generic: 3879-1

In addition, the following lists new USNs for affected build packages in
each snap revision:

Revision r12 (armhf; channels: stable, beta)
 * snapcraft: 5501-1
"""
        self.assertIn(needle, body)
        self.assertTrue(contains_stage_pkgs)
        self.assertTrue(contains_build_pkgs)
        self.assertEqual(
            "linux-generic-bbb built from outdated Ubuntu kernel and with outdated Ubuntu packages",
            subj,
        )

    def test_check__secnot_report_for_kernel_build_pkg_in_seen_db(self):
        """Test _secnot_report_for_pkg() - new secnot for staged pkg, build in
        seen-db"""
        errors = {}
        self.pkg_db = store.get_pkg_revisions(
            self.kernel_store_db[0], self.secnot_kernel_and_build_pkgs_db, errors
        )

        seen_db = {"linux-generic-bbb": {"12": ["3848-1", "3602-1", "5501-1"]}}
        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(self.pkg_db, seen_db)
        needle = """A scan of this snap shows that it was built using sources based on a kernel
from the Ubuntu archive that has since received security updates. The
following lists new USNs for the Ubuntu kernel that the snap is based on in
each snap revision:

Revision r12 (armhf; channels: stable, beta)
 * linux-image-generic: 3879-1
"""
        needle_for_template_in_addition = """
In addition, the following lists new USNs for affected build packages in
each snap revision:
"""
        self.assertIn(needle, body)
        self.assertNotIn(needle_for_template_in_addition, body)
        self.assertIn(needle, body)
        self.assertTrue(contains_stage_pkgs)
        self.assertFalse(contains_build_pkgs)
        self.assertEqual(
            "linux-generic-bbb built from outdated Ubuntu kernel", subj,
        )

    def test_check__secnot_report_for_pkg_only_new_secnot_budgie(self):
        """Test _secnot_report_for_pkg() - only new secnot budgie"""
        errors = {}
        self.pkg_db = store.get_pkg_revisions(
            self.budgie_store_db[0], self.secnot_budgie_db, errors
        )
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
        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(self.pkg_db, seen_db)
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
        self.assertIn(needle, body)
        self.assertTrue(contains_stage_pkgs)
        self.assertFalse(contains_build_pkgs)
        self.assertEqual(
            "ubuntu-budgie-welcome contains outdated Ubuntu packages", subj
        )

    def test_check__email_report_for_pkg(self):
        """Test _email_report_for_pkg()"""
        (to_addr, subj, body) = available._email_report_for_pkg(self.pkg_db, {})

        for eml in ["olivier.tilloy@canonical.com"]:
            self.assertIn(eml, to_addr)

        self.assertEqual("0ad contains outdated Ubuntu packages", subj)

        for pkg in ["libtiff5", "libxcursor1"]:
            self.assertIn(pkg, body)
        for sn in ["3501-1", "3602-1", "3606-1"]:
            self.assertIn(sn, body)

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
        self.assertIn("testme@example.com", to_addr)
        self.assertEqual("0ad contains outdated Ubuntu packages", subj)
        # collaborators supercede uploaders
        self.assertNotIn("testme2@example.com", to_addr)

    def test_check__email_report_for_pkg_with_uploaders(self):
        """Test _email_report_for_pkg() - with uploaders"""
        self.pkg_db["uploaders"] = ["testme@example.com"]
        (to_addr, subj, body) = available._email_report_for_pkg(self.pkg_db, {})
        self.assertEqual("0ad contains outdated Ubuntu packages", subj)
        self.assertIn("testme@example.com", to_addr)

    def test_check__email_report_for_pkg_with_additional(self):
        """Test _email_report_for_pkg() - with additional"""
        self.pkg_db["additional"] = ["testme@example.com"]
        (to_addr, subj, body) = available._email_report_for_pkg(self.pkg_db, {})
        self.assertEqual("0ad contains outdated Ubuntu packages", subj)
        self.assertIn("testme@example.com", to_addr)

    def test_check__email_report_for_pkg_with_staged_and_build_pkgs(self):
        """Test _email_report_for_pkg() - with staged and build_pks"""
        errors = {}
        pkg_db = store.get_pkg_revisions(
            self.store_db[0], self.secnot_build_and_stage_pkgs_db, errors
        )
        (to_addr, subj, body) = available._email_report_for_pkg(pkg_db, {})
        self.assertEqual(
            "0ad contains and was built with outdated Ubuntu packages", subj
        )

    def test_check__email_report_for_pkg_with_and_build_pkgs_only(self):
        """Test _email_report_for_pkg() - with staged and build_pks"""
        errors = {}
        pkg_db = store.get_pkg_revisions(
            self.store_db[0], self.secnot_build_pkgs_only_db, errors
        )
        (to_addr, subj, body) = available._email_report_for_pkg(pkg_db, {})
        self.assertEqual("0ad was built with outdated Ubuntu packages", subj)

    def test_check_read_seen_db(self):
        """Test read_seen_db()"""
        self.tmpdir = tempfile.mkdtemp()
        tmp = os.path.join(self.tmpdir, self.seen_db)
        res = available.read_seen_db(tmp)
        self.assertEqual(len(res), 0)

    def test_check__update_seen(self):
        """Test _update_seen()"""
        self.tmpdir = tempfile.mkdtemp()
        tmp = os.path.join(self.tmpdir, self.seen_db)
        res = available.read_seen_db(tmp)
        self.assertEqual(len(res), 0)
        seen_db = res

        available._update_seen(tmp, seen_db, self.pkg_db)

        res = available.read_seen_db(tmp)
        self.assertEqual(len(res), 1)
        self.assertIn("0ad", res)

        expected_db = {
            "0ad": {
                "11": ["3501-1", "3602-1", "3606-1"],
                "12": ["3501-1", "3602-1", "3606-1"],
                "13": ["3501-1", "3602-1", "3606-1"],
                "14": ["3501-1", "3602-1", "3606-1"],
                "15": ["3501-1", "3602-1", "3606-1"],
                "16": ["3501-1", "3602-1", "3606-1"],
                "17": ["3501-1", "3602-1", "3606-1"],
            }
        }
        self.assertEqual(len(expected_db), len(res))

        for pkg in expected_db:
            self.assertIn(pkg, res)
            self.assertEqual(len(expected_db[pkg]), len(res[pkg]))
            for rev in expected_db[pkg]:
                self.assertIn(rev, res[pkg])
                self.assertEqual(len(expected_db[pkg][rev]), len(res[pkg][rev]))
                for secnot in expected_db[pkg][rev]:
                    self.assertIn(secnot, res[pkg][rev])

    def test_check__update_seen_no_secnots(self):
        """Test _update_seen() - no secnots"""
        self.tmpdir = tempfile.mkdtemp()
        tmp = os.path.join(self.tmpdir, self.seen_db)
        res = available.read_seen_db(tmp)
        self.assertEqual(len(res), 0)
        seen_db = res

        for rev in self.pkg_db["revisions"]:
            self.pkg_db["revisions"][rev]["secnot-report"] = {}
        available._update_seen(tmp, seen_db, self.pkg_db)

        res = available.read_seen_db(tmp)
        self.assertEqual(len(res), 1)
        self.assertIn("0ad", res)
        self.assertEqual(len(res["0ad"]), 0)

    def test_check__update_seen_remove_old_revision(self):
        """Test _update_seen() - remove old revision"""
        self.tmpdir = tempfile.mkdtemp()
        tmp = os.path.join(self.tmpdir, self.seen_db)
        res = available.read_seen_db(tmp)
        self.assertEqual(len(res), 0)

        seen_db = {
            "0ad": {"9": ["3401-1"], "10": ["3401-1"], "8": ["3401-1"], "7": ["3401-1"]}
        }
        available._update_seen(tmp, seen_db, self.pkg_db)

        res = available.read_seen_db(tmp)
        self.assertEqual(len(res), 1)
        self.assertIn("0ad", res)
        self.assertEqual(len(res["0ad"]), 7)

        for r in ["7", "8", "9", "10"]:
            self.assertNotIn(r, seen_db["0ad"])

    def test_check_scan_shared_publishers(self):
        """Test scan_shared_publishers()"""
        fn = "./tests/test-store-missing-shared-override.db"
        res = available.scan_shared_publishers(fn)
        self.assertTrue(len(res) > 0)
        for p in [
            "missing-publisher-overrides-snap-1",
            "missing-publisher-overrides-snap-2",
        ]:
            self.assertIn(p, res)

    def test_check_scan_snap(self):
        """Test scan_snap()"""
        snap_fn = "./tests/test-snapcraft-manifest-unittest_0_amd64.snap"
        res = available.scan_snap(self.secnot_fn, snap_fn)
        self.assertTrue(len(res) > 0)
        self.assertIn("3501-1", res)

    def test_check_scan_snap_with_cves(self):
        """Test scan_snap() with cves"""
        snap_fn = (
            "./tests/test-snapcraft-manifest-snapcraft-version-needed_0_amd64.snap"
        )
        res = available.scan_snap(self.secnot_build_and_stage_pkgs_fn, snap_fn, True)
        self.assertTrue(len(res), 1)
        self.assertIn("snapcraft", res)
        self.assertIn("5501-1", res)
        self.assertIn("CVE-2020-9999", res)

    def test_check_scan_snap_core(self):
        """Test scan_snap() - core"""
        snap_fn = "./tests/test-core_16-2.37.2_amd64.snap"
        res = available.scan_snap(self.secnot_core_with_dpkg_list_fn, snap_fn)
        self.assertTrue(len(res) > 0)
        # This asserts a binary was obtained from the URLs since its not listed in the USN binaries keys
        self.assertIn("libc-bin", res)
        # This asserts the dpkg-query file was properly parsed and arch qualifiers were ignored LP: #1930105
        self.assertIn("libc6", res)
        self.assertIn("3323-1", res)

    def test_check_scan_snap_dpkg_list_app(self):
        """Test scan_snap() - dpkg.list app"""
        snap_fn = "./tests/test-dpkg-list-app_1.0_amd64.snap"
        res = available.scan_snap(self.secnot_core_with_dpkg_list_fn, snap_fn)
        self.assertTrue(len(res) > 0)
        self.assertIn("3323-1", res)

    def test_check_scan_snap_kernel(self):
        """Test scan_snap() - kernel"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["pc-kernel"] = {"linux-image-generic": "auto-kernel"}
        snap_fn = "./tests/pc-kernel_4.4.0-141.167_amd64.snap"
        res = available.scan_snap(self.secnot_kernel_fn, snap_fn)
        self.assertTrue(len(res) > 0)
        self.assertIn("3879-1", res)

    def test_check_scan_snap_kernel_packaging_fix_ignored(self):
        """Test scan_snap() - kernel - ignoring NNN, considering ABI only always"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["gke-kernel"] = {"linux-image-gke": "auto-kernel"}
        snap_fn = "./tests/gke-kernel_4.15.0-1069.72_amd64.snap"
        res = available.scan_snap(self.secnot_kernel_fn, snap_fn)
        self.assertTrue(len(res) == 0)

    def test_check_scan_snap_kernel_keeping_potentially_outdated_linux_image_generic_version_format(
        self,
    ):
        """Test scan_snap() - kernel abi, keeping MAJ.MIN.MIC-ABI-NNN support in case needed"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["linux-generic-bbb"] = {
            "linux-image-generic": "auto-kernel"
        }
        snap_fn = "./tests/linux-generic-bbb_4.4.0-140-1_armhf.snap"
        res = available.scan_snap(self.secnot_kernel_fn, snap_fn)
        self.assertTrue(len(res) > 0)
        self.assertIn("3848-1", res)
        self.assertIn("3879-1", res)

    def test_check_scan_snap_canonical_snap(self):
        """Test scan_snap() - canonical snap - network-manager"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["network-manager"] = {"network-manager": "auto"}
        secnot_fn = "./tests/test-usn-network-manager.db"
        snap_fn = "./tests/network-manager_1.10.6-2ubuntu1.0+dbce8fd2_amd64.snap"
        res = available.scan_snap(secnot_fn, snap_fn)
        self.assertTrue(len(res) > 0)
        self.assertIn("3807-1", res)

    def test_check_scan_store(self):
        """Test scan_store()"""
        (sent, errors) = available.scan_store(self.secnot_fn, self.store_fn, None, None)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        for eml in ["olivier.tilloy@canonical.com"]:
            self.assertIn(eml, to_addr)

        self.assertEqual("0ad contains outdated Ubuntu packages", subj)
        self.assertIn("built with packages from the Ubuntu", body)

        for pkg in ["libtiff5", "libxcursor1"]:
            self.assertIn(pkg, body)
        for sn in ["3501-1", "3602-1", "3606-1"]:
            self.assertIn(sn, body)

    def test_check_scan_store_invalid_snapcraft_version(self):
        """Test scan_store()"""
        store_fn = "./tests/test-store-unittest-invalid-snapcraft-version.db"
        (sent, errors) = available.scan_store(self.secnot_fn, store_fn, None, None)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        self.assertEqual(to_addr, None)
        self.assertEqual(subj, None)
        self.assertEqual(body, None)

    def test_check_scan_store_with_seen(self):
        """Test scan_store() - with seen - snaps and rocks"""
        store_dbs = {
            "snap": [
                self.store_fn,
                ["olivier.tilloy@canonical.com"],
                "0ad",
                ["libtiff5", "libxcursor1"],
                ["3501-1", "3602-1", "3606-1"],
            ],
            "rock": [
                self.rock_store_fn,
                ["rocks@canonical.com"],
                "redis",
                ["libxcursor1"],
                ["3501-1"],
            ],
        }
        self.tmpdir = tempfile.mkdtemp()

        for store_type, store_metadata in store_dbs.items():
            (
                store_fn,
                publishers,
                pkg_name,
                binaries_with_updates,
                secnots,
            ) = store_metadata
            with self.subTest(
                store_type=store_type,
                store_fn=store_fn,
                publishers=publishers,
                pkg_name=pkg_name,
                binaries_with_updates=binaries_with_updates,
                secnots=secnots,
            ):
                seen_fn = os.path.join(self.tmpdir, self.seen_db)
                sent, errors = available.scan_store(
                    self.secnot_fn, store_fn, seen_fn, None, store_type
                )
                self.assertEqual(len(errors), 0)
                self.assertEqual(len(sent), 1)
                to_addr, subj, body = sent[0]
                for email_addr in publishers:
                    self.assertIn(email_addr, to_addr)
                self.assertEqual(
                    "%s contains outdated Ubuntu packages" % pkg_name, subj
                )
                for pkg in binaries_with_updates:
                    self.assertIn(pkg, body)
                for sn in secnots:
                    self.assertIn(sn, body)

    def test_check_scan_store_with_pkgname(self):
        """Test scan_store() - with pkgname - snaps and rocks"""
        store_dbs = {
            "snap": self.store_fn,
            "rock": self.rock_store_fn,
        }
        for store_type, store_fn in store_dbs.items():
            with self.subTest(store_type=store_type, store_fn=store_fn):
                (sent, errors) = available.scan_store(
                    self.secnot_fn, store_fn, None, "not-there", store_type
                )
                self.assertEqual(len(errors), 0)
                self.assertEqual(len(sent), 0)

    def test_check_scan_store_with_pkgname_bad_publisher(self):
        """Test scan_store() - with pkgname and bad publisher - snaps and
        rocks
        """
        store_dbs = {
            "snap": ["./tests/test-store-unittest-bad-1.db", "1ad"],
            "rock": ["./tests/test-rocks-store-unittest-bad-1.db", "redis"],
        }
        for store_type, store_metadata in store_dbs.items():
            store_fn, pkg_name = store_metadata
            with self.subTest(
                store_type=store_type, store_fn=store_fn, pkg_name=pkg_name
            ):
                (sent, errors) = available.scan_store(
                    self.secnot_fn, store_fn, None, pkg_name, store_type
                )
                self.assertEqual(len(errors), 1)
                self.assertEqual(len(sent), 0)

    def test_check_scan_store_kernel(self):
        """Test scan_store() - kernel"""
        (sent, errors) = available.scan_store(
            self.secnot_kernel_fn, self.kernel_store_fn, None, None
        )
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        for eml in ["foo@example.com"]:
            self.assertIn(eml, to_addr)
        self.assertIn("using sources based on a kernel", body)
        self.assertIn("Updating the snap's git tree", body)
        self.assertNotIn("Simply rebuilding the snap", body)
        self.assertIn("linux-image-generic", body)
        for line in body.splitlines():
            # text width of emails should not exceed 75
            self.assertTrue(len(line) <= 75)
        self.assertEqual("linux-generic-bbb built from outdated Ubuntu kernel", subj)

        for sn in ["3848-1", "3879-1"]:
            self.assertIn(sn, body)

    def test_check_scan_store_kernel_and_build_pkg_update_only(self):
        """Test scan_store() - kernel snap and build pkg update"""
        (sent, errors) = available.scan_store(
            self.secnot_build_pkgs_only_fn, self.kernel_store_fn, None, None
        )
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        for eml in ["foo@example.com"]:
            self.assertIn(eml, to_addr)
        self.assertNotIn("using sources based on a kernel", body)
        self.assertIn("Updating the snap's git tree", body)
        self.assertNotIn("Simply rebuilding the snap", body)
        self.assertIn("snapcraft", body)
        for line in body.splitlines():
            # text width of emails should not exceed 75
            self.assertTrue(len(line) <= 75)
        self.assertEqual(
            "linux-generic-bbb was built with outdated Ubuntu packages", subj
        )
        self.assertIn("USN-5501-1", body)

    def test_check_scan_store_kernel_and_build_pkg_update_invalid_snapcraft_version(
        self,
    ):
        """Test scan_store() - kernel snap and build pkg update but invalid
        snapcraft version"""
        store_fn = "./tests/test-store-kernel-invalid-snapcraft-version.db"
        (sent, errors) = available.scan_store(
            self.secnot_build_pkgs_only_fn, store_fn, None, None
        )
        (to_addr, subj, body) = sent[0]
        self.assertEqual(to_addr, None)
        self.assertEqual(subj, None)
        self.assertEqual(body, None)

    def test_check_scan_store_kernel_and_build_pkg_updates(self):
        """Test scan_store() - kernel snap and build pkg update"""
        (sent, errors) = available.scan_store(
            self.secnot_kernel_and_build_pkgs_fn, self.kernel_store_fn, None, None
        )
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        for eml in ["foo@example.com"]:
            self.assertIn(eml, to_addr)
        self.assertIn("using sources based on a kernel", body)
        self.assertIn("Updating the snap's git tree", body)
        self.assertNotIn("Simply rebuilding the snap", body)
        self.assertIn("snapcraft", body)
        self.assertIn("linux-image-generic", body)
        for line in body.splitlines():
            # text width of emails should not exceed 75
            self.assertTrue(len(line) <= 75)
        self.assertEqual(
            "linux-generic-bbb built from outdated Ubuntu kernel and with outdated Ubuntu packages",
            subj,
        )
        for sn in ["3848-1", "3879-1", "USN-5501-1"]:
            self.assertIn(sn, body)

    def test_check_scan_store_lp1841848_allbinaries(self):
        """Test scan_store() - lp1841848 (allbinaries)"""
        (sent, errors) = available.scan_store(
            self.secnot_lp1841848_fn, self.lp1841848_store_fn, None, None
        )
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        self.assertEqual(to_addr, None)
        self.assertEqual(subj, None)
        self.assertEqual(body, None)

    def test_check_scan_store_lp1841848_allbinaries_needed(self):
        """Test scan_store() - lp1841848 (allbinaries needed)"""
        (sent, errors) = available.scan_store(
            self.secnot_lp1841848_fn, self.lp1841848_needed_store_fn, None, None
        )
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        eml = "test.me@example.com"
        self.assertIn(eml, to_addr)
        self.assertIn("libreoffice-style-tango: 4102-1", body)
        self.assertIn("uno-libs3: 4102-1", body)
        self.assertEqual("test-snap contains outdated Ubuntu packages", subj)

    def test_check_scan_store_lp1841848_allbinaries_bad_epoch(self):
        """Test scan_store() - lp1841848 (allbinaries with bad epoch)"""
        (sent, errors) = available.scan_store(
            self.secnot_lp1841848_incorrect_epoch_fn,
            self.lp1841848_store_fn,
            None,
            None,
        )
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]

        self.assertEqual(to_addr, None)
        self.assertEqual(subj, None)
        self.assertEqual(body, None)

    def test_check_scan_store_lp1841848_allbinaries_bad_epoch_needed(self):
        """Test scan_store() - lp1841848 (allbinaries with bad epoch needed)"""
        (sent, errors) = available.scan_store(
            self.secnot_lp1841848_incorrect_epoch_fn,
            self.lp1841848_needed_store_fn,
            None,
            None,
        )
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        eml = "test.me@example.com"
        self.assertIn(eml, to_addr)
        self.assertIn("libreoffice-style-tango: 4102-1", body)
        self.assertIn("uno-libs3: 4102-1", body)
        self.assertEqual("test-snap contains outdated Ubuntu packages", subj)

    def test_check_scan_store_lp1841848_allbinaries_bad_epoch2(self):
        """Test scan_store() - lp1841848 (allbinaries with bad epoch2)"""
        secnot_fn = "./tests/test-usn-unittest-lp1841848-incorrect-epoch2.db"
        (sent, errors) = available.scan_store(
            secnot_fn, self.lp1841848_store_fn, None, None
        )
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]

        self.assertEqual(to_addr, None)
        self.assertEqual(subj, None)
        self.assertEqual(body, None)

    def test_check_scan_store_lp1841848_unmatched_binver(self):
        """Test scan_store() - lp1841848 (unmatched binary version)"""
        secnot_fn = "./tests/test-usn-unittest-lp1841848-unmatched-binver.db"
        (sent, errors) = available.scan_store(
            secnot_fn, self.lp1841848_store_fn, None, None
        )
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]

        self.assertEqual(to_addr, None)
        self.assertEqual(subj, None)
        self.assertEqual(body, None)

    def test_check_scan_store_lp1841848_no_allbinaries(self):
        """Test scan_store() - lp1841848 (no allbinaries)"""
        secnot_fn = "./tests/test-usn-unittest-lp1841848-noallbin.db"
        (sent, errors) = available.scan_store(
            secnot_fn, self.lp1841848_store_fn, None, None
        )
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        self.assertEqual(to_addr, None)
        self.assertEqual(subj, None)
        self.assertEqual(body, None)

    def test_check_scan_store_lp1841848_no_allbinaries_needed(self):
        """Test scan_store() - lp1841848 (no allbinaries needed)"""
        secnot_fn = "./tests/test-usn-unittest-lp1841848-noallbin.db"
        (sent, errors) = available.scan_store(
            secnot_fn, self.lp1841848_needed_store_fn, None, None
        )
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        eml = "test.me@example.com"
        self.assertIn(eml, to_addr)
        self.assertIn("libreoffice-style-tango: 4102-1", body)
        self.assertIn("uno-libs3: 4102-1", body)
        self.assertEqual("test-snap contains outdated Ubuntu packages", subj)

    def test_check_scan_store_lp1841848_unmatched_binver2(self):
        """Test scan_store() - lp1841848 (unmatched binary version no all binaries)"""
        secnot_fn = "./tests/test-usn-unittest-lp1841848-unmatched-binver-noallbin.db"
        (sent, errors) = available.scan_store(
            secnot_fn, self.lp1841848_store_fn, None, None
        )
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]

        self.assertEqual(to_addr, None)
        self.assertEqual(subj, None)
        self.assertEqual(body, None)

    def test_check_scan_store_empty_manifest(self):
        """Test scan_store() - empty manifest - snaps and rocks"""
        store_dbs = {
            "snap": "./tests/test-store-unittest-bare.db",
            "rock": "./tests/test-rocks-store-unittest-bare.db",
        }
        for store_type, store_fn in store_dbs.items():
            with self.subTest(store_type=store_type, store_fn=store_fn):
                (sent, errors) = available.scan_store(
                    self.secnot_fn, store_fn, None, None, store_type
                )
                self.assertEqual(len(errors), 0)
                self.assertEqual(len(sent), 0)

    def test_check_scan_rock(self):
        """Test scan_rock()"""
        test_rocks = [self.rock_fn, self.rock_non_lts_based_fn]
        for rock in test_rocks:
            with self.subTest(rock=rock):
                res = available.scan_rock(self.secnot_fn, rock)
                self.assertTrue(len(res) > 0)
                self.assertIn("3501-1", res)

    def test_check_scan_rock_release_not_in_secnot(self):
        """Test scan_rock() no release"""
        with self.assertRaises(ValueError):
            available.scan_rock(self.secnot_build_and_stage_pkgs_fn, self.rock_fn)

    def test_check_scan_rock_no_updates(self):
        """Test scan_rock() no release"""
        res = available.scan_rock(self.secnot_build_pkgs_only_fn, self.rock_fn)
        self.assertTrue(len(res) == 0)

    def test_check_scan_rock_with_cves(self):
        """Test scan_rock() with cves"""
        test_rocks = [self.rock_fn, self.rock_non_lts_based_fn]
        for rock in test_rocks:
            with self.subTest(rock=rock):
                res = available.scan_rock(self.secnot_fn, rock, True)
                self.assertTrue(len(res), 1)
                self.assertIn("libxcursor1", res)
                self.assertIn("3501-1", res)
                self.assertIn("CVE-2017-16612", res)

    def test_check_scan_rock_store(self):
        """Test scan_store() - rock"""
        store_fn = self.rock_store_fn
        (sent, errors) = available.scan_store(
            self.secnot_fn, store_fn, None, None, "rock"
        )
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(sent), 1)
        (to_addr, subj, body) = sent[0]
        for eml in ["rocks@canonical.com"]:
            self.assertIn(eml, to_addr)

        self.assertEqual("redis contains outdated Ubuntu packages", subj)
        self.assertIn("built with packages from the Ubuntu", body)
        self.assertIn("libxcursor1", body)
        self.assertEqual(body.count("libxcursor1"), 2)
        self.assertIn("3501-1", body)
        # rock_store_fn contains USNs for 2 revisions but count is 3 due
        # to the references link
        self.assertEqual(body.count("3501-1"), 3)

    def test_check_secnot_report_for_rock(self):
        """Test _secnot_report_for_pkg() - rock"""
        errors = {}
        self.store_db = {}
        secnot_db = usn.read_usn_db(self.secnot_fn, support_non_lts=True)
        pkg_db = store.get_pkg_revisions(
            self.rock_store_db[0], secnot_db, errors, "rock"
        )
        self.assertEqual(len(errors), 0)
        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(pkg_db, {})
        needle = """A scan of this rock shows that it was built with packages from the Ubuntu
archive that have since received security updates. The following lists new
USNs for affected binary packages in each rock revision:

Revision r852f7702e973 (amd64; channels: edge, beta)
 * libxcursor1: 3501-1

Revision r852f7702e974 (amd64; channels: edge, beta)
 * libxcursor1: 3501-1

Simply rebuilding the rock will pull in the new security updates and
resolve this. If your rock also contains vendored code, now might be a
good time to review it for any needed updates.

Thank you for your rock and for attending to this matter.

References:
 * https://ubuntu.com/security/notices/USN-3501-1/
"""
        self.assertIn(needle, body)
        for line in body.splitlines():
            # text width of emails should not exceed 75
            self.assertTrue(len(line) <= 75)
        self.assertTrue(contains_stage_pkgs)
        self.assertFalse(contains_build_pkgs)
        self.assertEqual("redis contains outdated Ubuntu packages", subj)

    def test_check_secnot_report_for_rock_no_updates(self):
        """Test _secnot_report_for_pkg() - rock - no updates"""
        errors = {}
        self.store_db = {}
        pkg_db = store.get_pkg_revisions(
            self.rock_store_db[0], self.secnot_build_pkgs_only_db, errors, "rock"
        )
        self.assertEqual(len(errors), 0)
        (
            subj,
            body,
            contains_stage_pkgs,
            contains_build_pkgs,
        ) = available._secnot_report_for_pkg(pkg_db, {})
        self.assertEqual(body, "")
        self.assertFalse(contains_stage_pkgs)
        self.assertFalse(contains_build_pkgs)
        self.assertEqual("", subj)
