"""test_store.py: tests for the store module"""
#
# Copyright (C) 2018-2020 Canonical Ltd.
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

import copy
import yaml

import reviewtools.store as store

from reviewtools.common import read_file_as_json_dict
import reviewtools.usn as usn


class TestStore(TestCase):
    """Tests for the store functions."""

    def setUp(self):
        """Read in a sample store and security notice db"""
        self.secnot_db = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.store_db = read_file_as_json_dict("./tests/test-store-unittest-1.db")
        self.first_revision = 0
        self.first_revision_with_primed_stage = 4
        # make sure primed-stage-packages section is present on
        # first_revision_with_primed_stage revision. Adding this assertion
        # here means we end up checking that in each test. Still, it is a
        # cheap test and means all the tests don't need to worry about using
        # primed-stage-packages with self.first_revision_with_primed_stage
        self.assertTrue(
            "primed-stage-packages"
            in self.store_db[0]["revisions"][self.first_revision_with_primed_stage][
                "manifest_yaml"
            ]
        )
        self.manifest_basic = {
            "apps": {"foo": {"command": "bin/foo"}},
            "architectures": ["amd64"],
            "build-packages": [],
            "build-snaps": [],
            "confinement": "strict",
            "description": "some description",
            "grade": "stable",
            "name": "foo",
            "parts": {
                "part1": {
                    "build-packages": [],
                    "installed-packages": ["bar=1.2", "baz=3.4"],
                    "installed-snaps": [],
                    "plugin": "dump",
                    "prime": [],
                    "source": "snap",
                    "stage": [],
                    "stage-packages": ["libbar=1.2", "libbaz=3.4"],
                    "uname": "Linux 5.4.0-29-generic #33-Ubuntu SMP Wed Apr 29 14:32:27 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux",
                },
                "part2": {
                    "build-packages": ["autoconf", "dpkg-dev"],
                    "install": "some_command",
                    "installed-packages": ["norf=5.6", "baz=3.4"],
                    "installed-snaps": [],
                    "plugin": "nil",
                    "prepare": "some_other_command",
                    "prime": [],
                    "source": "http://some/where/blah.tar.gz",
                    "stage": [],
                    "stage-packages": [],
                    "uname": "Linux 5.4.0-29-generic #33-Ubuntu SMP Wed Apr 29 14:32:27 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux",
                },
                "part3": {
                    "build-packages": [],
                    "installed-packages": ["norf=5.6", "corge=7.8"],
                    "installed-snaps": [],
                    "organize": {"blah": "bin/blah"},
                    "plugin": "dump",
                    "prime": [],
                    "source": "http://some/where/blah2.tar.gz",
                    "stage": [],
                    "stage-packages": [],
                    "uname": "Linux 5.4.0-29-generic #33-Ubuntu SMP Wed Apr 29 14:32:27 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux",
                },
            },
            "summary": "some summary",
            "version": "0.1",
        }

    def test_check_get_package_revisions_empty(self):
        """Test get_package_revisions() - empty item"""

        try:
            store.get_pkg_revisions({}, self.secnot_db, {})
        except ValueError:
            return

        raise Exception("Should have raised ValueError")  # pragma: nocover

    def test_check_get_package_revisions_valid(self):
        """Test get_package_revisions() - valid"""
        errors = {}
        res = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 0)

        # verify the structure is what we expect
        self.assertTrue("name" in res)
        self.assertEqual(res["name"], "0ad")

        self.assertTrue("publisher" in res)
        self.assertEqual(res["publisher"], "olivier.tilloy@canonical.com")

        self.assertTrue("uploaders" in res)
        self.assertTrue(isinstance(res["uploaders"], list))
        self.assertEqual(len(res["uploaders"]), 0)

        self.assertTrue("additional" in res)
        self.assertTrue(isinstance(res["additional"], list))
        self.assertEqual(len(res["additional"]), 0)

        self.assertTrue("revisions" in res)
        self.assertTrue("12" in res["revisions"])

        self.assertTrue("channels" in res["revisions"]["12"])
        self.assertTrue("stable" in res["revisions"]["12"]["channels"])

        self.assertTrue("architectures" in res["revisions"]["12"])
        self.assertTrue("i386" in res["revisions"]["12"]["architectures"])

        self.assertTrue("secnot-report" in res["revisions"]["12"])
        self.assertTrue("staged" in res["revisions"]["12"]["secnot-report"])
        self.assertTrue(
            "libxcursor1" in res["revisions"]["12"]["secnot-report"]["staged"]
        )
        self.assertTrue(
            "3501-1" in res["revisions"]["12"]["secnot-report"]["staged"]["libxcursor1"]
        )
        self.assertFalse("build" in res["revisions"]["12"]["secnot-report"])

    def test_check_get_package_revisions_valid_with_snap_type(self):
        """Test get_package_revisions() - valid (snap type)"""
        m = (
            self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"]
            + "\ntype: app"
        )
        self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"] = m
        errors = {}
        res = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 0)
        self.assertTrue("staged" in res["revisions"]["12"]["secnot-report"])
        self.assertTrue(
            "3501-1" in res["revisions"]["12"]["secnot-report"]["staged"]["libxcursor1"]
        )
        self.assertFalse("build" in res["revisions"]["12"]["secnot-report"])

    def test_check_get_package_revisions_missing_publisher(self):
        """Test get_package_revisions() - missing publisher"""
        self.store_db[0]["publisher_email"] = ""
        errors = {}
        store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors["0ad"][0], "publisher_email '' invalid")

    def test_check_get_package_revisions_missing_revision(self):
        """Test get_package_revisions() - missing revision"""
        del self.store_db[0]["revisions"][self.first_revision]["revision"]
        errors = {}
        store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors["0ad"][0], "no revisions found")

    def test_check_get_package_revisions_missing_manifest(self):
        """Test get_package_revisions() - missing manifest"""
        del self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"]
        errors = {}
        store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors["0ad"][0], "manifest_yaml missing for revision '12'")

    def test_check_get_package_revisions_bad_manifest(self):
        """Test get_package_revisions() - bad manifest"""
        self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"] = "{"
        errors = {}
        store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 1)
        self.assertTrue(
            errors["0ad"][0].startswith("error loading manifest for revision '12':")
        )

    def test_check_get_package_revisions_bad_secnot(self):
        """Test get_package_revisions() - bad secnot db"""
        self.secnot_db = "bad"
        errors = {}
        pkg_db = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(pkg_db["revisions"]), 0)

    def test_check_get_package_revisions_empty_uploader(self):
        """Test get_package_revisions() - empty uploader"""
        self.store_db[0]["revisions"][self.first_revision]["uploader_email"] = ""
        errors = {}
        store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors["0ad"][0], "uploader_email '' invalid")

    def test_check_get_package_revisions_has_uploader(self):
        """Test get_package_revisions() - has uploader"""
        self.store_db[0]["revisions"][self.first_revision][
            "uploader_email"
        ] = "test@example.com"
        errors = {}
        res = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 0)
        self.assertTrue("uploaders" in res)
        self.assertTrue(isinstance(res["uploaders"], list))
        self.assertEqual(len(res["uploaders"]), 1)
        self.assertEqual(res["uploaders"][0], "test@example.com")

    def test_check_get_package_revisions_empty_collaborator(self):
        """Test get_package_revisions() - empty collaborator"""
        self.store_db[0]["collaborators"] = [{"email": ""}]
        errors = {}
        store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors["0ad"][0], "collaborator email '' invalid")

    def test_check_get_package_revisions_malformed_collaborator(self):
        """Test get_package_revisions() - malformed collaborator"""
        self.store_db[0]["collaborators"] = ["test@example.com"]
        errors = {}
        res = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 0)
        self.assertTrue(isinstance(res["collaborators"], list))
        self.assertEqual(len(res["collaborators"]), 0)

    def test_check_get_package_revisions_has_collaborator(self):
        """Test get_package_revisions() - has has collaborator"""
        self.store_db[0]["collaborators"] = [
            {"email": "test@example.com", "name": "Test Me"}
        ]
        errors = {}
        res = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 0)
        self.assertTrue(isinstance(res["collaborators"], list))
        self.assertEqual(len(res["collaborators"]), 1)
        self.assertEqual(res["collaborators"][0], "test@example.com")

    def test_check_get_package_revisions_parts_is_none(self):
        """Test get_package_revisions() - parts is None has no security
           notices """
        for i in range(len(self.store_db[0]["revisions"])):
            m = yaml.load(
                self.store_db[0]["revisions"][i]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )
            m["parts"] = None
            self.store_db[0]["revisions"][i]["manifest_yaml"] = yaml.dump(m)
        errors = {}
        pkg_db = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        # empty parts has no security notices
        self.assertEqual(len(errors), 0)
        for rev in pkg_db["revisions"]:
            self.assertEqual(len(pkg_db["revisions"][rev]["secnot-report"]), 0)

    def test_check_get_package_revisions_parts_is_none_and_usn_for_build_pkgs(self):
        """Test get_package_revisions() - parts is None has no security
           notices even with usn for build-packages"""
        for i in range(len(self.store_db[0]["revisions"])):
            m = yaml.load(
                self.store_db[0]["revisions"][i]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )
            m["parts"] = None
            m["snapcraft-version"] = "1.1.1"
            self.store_db[0]["revisions"][i]["manifest_yaml"] = yaml.dump(m)
        secnot_db = usn.read_usn_db("./tests/test-usn-unittest-build-pgks.db")
        errors = {}
        pkg_db = store.get_pkg_revisions(self.store_db[0], secnot_db, errors)
        # empty parts has no security notices
        self.assertEqual(len(errors), 0)
        for rev in pkg_db["revisions"]:
            self.assertEqual(len(pkg_db["revisions"][rev]["secnot-report"]), 0)

    def test_check_get_package_revisions_parts_is_empty(self):
        """Test get_package_revisions() - parts is empty has no security
           notices"""

        for i in range(len(self.store_db[0]["revisions"])):
            m = yaml.load(
                self.store_db[0]["revisions"][i]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )
            m["parts"] = {}
            self.store_db[0]["revisions"][i]["manifest_yaml"] = yaml.dump(m)
        errors = {}
        pkg_db = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        # empty parts has no security notices
        self.assertEqual(len(errors), 0)
        for rev in pkg_db["revisions"]:
            self.assertEqual(len(pkg_db["revisions"][rev]["secnot-report"]), 0)

    def test_check_get_package_revisions_parts_is_empty_and_usn_for_build_pkgs(self):
        """Test get_package_revisions() - parts is empty has no security
           notices even if USN for build-packages"""

        for i in range(len(self.store_db[0]["revisions"])):
            m = yaml.load(
                self.store_db[0]["revisions"][i]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )
            m["parts"] = {}
            m["snapcraft-version"] = "1.1.1"
            self.store_db[0]["revisions"][i]["manifest_yaml"] = yaml.dump(m)
        errors = {}
        pkg_db = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        # empty parts has no security notices
        self.assertEqual(len(errors), 0)
        for rev in pkg_db["revisions"]:
            self.assertEqual(len(pkg_db["revisions"][rev]["secnot-report"]), 0)

    def test_check_get_package_revisions_image_info_is_none(self):
        """Test get_package_revisions() - image-info is None"""
        for i in range(len(self.store_db[0]["revisions"])):
            m = yaml.load(
                self.store_db[0]["revisions"][i]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )
            m["image-info"] = None
            self.store_db[0]["revisions"][i]["manifest_yaml"] = yaml.dump(m)
        errors = {}
        pkg_db = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        # empty image-info has no effect
        self.assertEqual(len(errors), 0)
        for rev in pkg_db["revisions"]:
            self.assertFalse(len(pkg_db["revisions"][rev]["secnot-report"]) == 0)

    def test_check_get_package_revisions_parts_stage_packages_and_primed_stage_packages_are_none(
        self,
    ):
        """Test get_package_revisions() - parts/stage-packages and
           primed-stage-packages are None has no security notices if no usn for build-pkgs"""
        for i in range(len(self.store_db[0]["revisions"])):
            m = yaml.load(
                self.store_db[0]["revisions"][i]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )
            for p in m["parts"]:
                if "stage-packages" in m["parts"][p]:
                    m["parts"][p]["stage-packages"] = None
            m["primed-stage-packages"] = None
            self.store_db[0]["revisions"][i]["manifest_yaml"] = yaml.dump(m)
        errors = {}
        pkg_db = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        # empty parts/stage-packages has no security notices
        self.assertEqual(len(errors), 0)
        for rev in pkg_db["revisions"]:
            self.assertEqual(len(pkg_db["revisions"][rev]["secnot-report"]), 0)

    def test_check_get_package_revisions_parts_stage_packages_and_primed_stage_packages_are_none_but_usn_for_build_pkgs(
        self,
    ):
        """Test get_package_revisions() - parts/stage-packages and
           primed-stage-packages are None but USN for build-packages has
           security notices"""
        for i in range(len(self.store_db[0]["revisions"])):
            m = yaml.load(
                self.store_db[0]["revisions"][i]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )
            for p in m["parts"]:
                if "stage-packages" in m["parts"][p]:
                    m["parts"][p]["stage-packages"] = None
            m["primed-stage-packages"] = None
            m["snapcraft-version"] = "1.1.1"
            self.store_db[0]["revisions"][i]["manifest_yaml"] = yaml.dump(m)
        secnot_db = usn.read_usn_db("./tests/test-usn-unittest-build-pgks.db")
        errors = {}
        pkg_db = store.get_pkg_revisions(self.store_db[0], secnot_db, errors)
        for rev in pkg_db["revisions"]:
            self.assertFalse("stage-packages" in rev)
            self.assertEqual(len(pkg_db["revisions"][rev]["secnot-report"]["build"]), 1)
            self.assertTrue(
                "snapcraft" in pkg_db["revisions"][rev]["secnot-report"]["build"]
            )
            self.assertTrue(
                "5501-1"
                in pkg_db["revisions"][rev]["secnot-report"]["build"]["snapcraft"]
            )

    def test_check_get_package_revisions_primed_and_staged_none_and_usn_for_build_but_no_affected_snapcraft_version_in_manifest(
        self,
    ):
        """Test get_package_revisions() - parts/stage-packages and
           primed-stage-packages are None and no snapcraft version or
           higher has no security notices"""
        snapcraft_version_value = [
            "not_present",
            None,
            "",
            "6",
        ]  # snacraft version in USN is 5.0.0 so version 6 should not get secnot
        for snapcraft_version in snapcraft_version_value:
            for i in range(len(self.store_db[0]["revisions"])):
                m = yaml.load(
                    self.store_db[0]["revisions"][i]["manifest_yaml"],
                    Loader=yaml.SafeLoader,
                )
                for p in m["parts"]:
                    if "stage-packages" in m["parts"][p]:
                        m["parts"][p]["stage-packages"] = None
                m["primed-stage-packages"] = None
                if snapcraft_version == "not_present":
                    del m["snapcraft-version"]
                else:
                    m["snapcraft-version"] = snapcraft_version
                self.store_db[0]["revisions"][i]["manifest_yaml"] = yaml.dump(m)
            secnot_db = usn.read_usn_db("./tests/test-usn-unittest-build-pgks.db")
            errors = {}
            pkg_db = store.get_pkg_revisions(self.store_db[0], secnot_db, errors)
            # empty parts/stage-packages has no security notices
            # usn for build-packages does not apply
            for rev in pkg_db["revisions"]:
                self.assertEqual(len(pkg_db["revisions"][rev]["secnot-report"]), 0)

    def test_check_get_package_revisions_pkg_override(self):
        """Test get_package_revisions() - pkg override"""
        # update the overrides for this snap
        from reviewtools.overrides import update_publisher_overrides

        update_publisher_overrides["rt-tests@example.com"] = {}
        update_publisher_overrides["rt-tests@example.com"]["0ad"] = ["over@example.com"]
        self.store_db[0]["publisher_email"] = "rt-tests@example.com"
        errors = {}
        res = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 0)
        self.assertTrue("additional" in res)
        self.assertTrue(isinstance(res["additional"], list))
        self.assertEqual(len(res["additional"]), 1)
        self.assertEqual(res["additional"][0], "over@example.com")

    def test_check_get_package_revisions_bad_release(self):
        """Test get_package_revisions() - pkg override"""
        for i in range(len(self.store_db[0]["revisions"])):
            m = yaml.load(
                self.store_db[0]["revisions"][i]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )
            del m["parts"]
            self.store_db[0]["revisions"][i]["manifest_yaml"] = yaml.dump(m)
        errors = {}
        store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors["0ad"][0],
            "(revision '12') Could not determine Ubuntu release ('parts' not in manifest)",
        )

    def test_check_get_shared_snap_without_override_missing(self):
        """Test get_shared_snap_without_override() - missing"""
        # update the overrides for this snap
        from reviewtools.overrides import update_publisher_overrides

        update_publisher_overrides["rt-tests@example.com"] = {}
        self.store_db[0]["publisher_email"] = "rt-tests@example.com"
        res = store.get_shared_snap_without_override(self.store_db)
        self.assertTrue(isinstance(res, dict))
        self.assertEqual(len(res), 1)
        self.assertTrue("rt-tests@example.com" in res)
        self.assertEqual(len(res["rt-tests@example.com"]), 1)
        self.assertEqual(res["rt-tests@example.com"][0], "0ad")

    def test_check_get_shared_snap_without_override_missing_publisher(self):
        """Test get_shared_snap_without_override() - missing publisher"""
        del self.store_db[0]["publisher_email"]
        res = store.get_shared_snap_without_override(self.store_db)
        self.assertTrue(isinstance(res, dict))
        self.assertEqual(len(res), 0)

    def test_check_get_shared_snap_without_override_not_present(self):
        """Test get_shared_snap_without_override() - not present"""
        res = store.get_shared_snap_without_override(self.store_db)
        self.assertTrue(isinstance(res, dict))
        self.assertEqual(len(res), 0)

    def test_check_normalize_and_verify_snap_manifest(self):
        """Test normalize_and_verify_snap_manifest()"""
        for r in self.store_db[0]["revisions"]:
            m = yaml.load(r["manifest_yaml"], Loader=yaml.SafeLoader)
            store.normalize_and_verify_snap_manifest(m)

    def test_check_normalize_and_verify_snap_manifest_bad(self):
        """Test normalize_and_verify_snap_manifest()"""
        try:
            store.normalize_and_verify_snap_manifest([])
        except ValueError:
            return

        raise Exception("Should have raised ValueError")  # pragma: nocover

    def test_check_get_staged_and_build_packages_from_manifest(self):
        """Test get_staged_packages_from_manifest()"""
        snapcraft_version_value = [
            "not_present",
            None,
            "",
            "6",
        ]
        for snapcraft_version in snapcraft_version_value:
            m = yaml.load(
                self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )
            if snapcraft_version != "not_present":
                m["snapcraft-version"] = snapcraft_version
            res = store.get_staged_and_build_packages_from_manifest(m)
            self.assertTrue(isinstance(res, dict))
            self.assertTrue(len(res) > 0)
            self.assertTrue("staged" in res)
            self.assertTrue("libxcursor1" in res["staged"])
            self.assertTrue("1:1.1.14-1" in res["staged"]["libxcursor1"])
            self.assertFalse("build" in res)

    def test_check_get_staged_packages_from_manifest_with_primed_stage_packages(self):
        """Test get_staged_packages_from_manifest(), primed-stage exists"""
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision_with_primed_stage][
                "manifest_yaml"
            ],
            Loader=yaml.SafeLoader,
        )
        res = store.get_staged_and_build_packages_from_manifest(m)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue(len(res) > 0)
        self.assertTrue("staged" in res)
        self.assertTrue("libxcursor1" in res["staged"])
        self.assertTrue("1:1.1.14-1" in res["staged"]["libxcursor1"])
        self.assertFalse("build" in res)

    def test_check_get_staged_packages_from_manifest_missing_parts(self):
        """Test get_staged_packages_from_manifest() - missing parts"""
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        del m["parts"]

        res = store.get_staged_and_build_packages_from_manifest(m)
        self.assertEqual(res, None)

    def test_check_get_staged_packages_from_manifest_bad_staged_and_no_primed_stage(
        self,
    ):
        """Test get_staged_packages_from_manifest() - bad staged"""
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        m["parts"]["0ad-launcher"]["stage-packages"].append("foo")

        res = store.get_staged_and_build_packages_from_manifest(m)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue(len(res) > 0)
        self.assertTrue("staged" in res)
        self.assertFalse("foo" in res["staged"])
        self.assertTrue("libxcursor1" in res["staged"])
        self.assertTrue("1:1.1.14-1" in res["staged"]["libxcursor1"])
        self.assertFalse("build" in res)

    def test_check_get_staged_packages_from_manifest_bad_primed_staged(self,):
        """Test get_staged_packages_from_manifest() - only one
           bad package in primed-stage returns None"""
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        m["primed-stage-packages"] = ["foo"]

        res = store.get_staged_and_build_packages_from_manifest(m)
        self.assertEqual(res, None)

    def test_check_get_staged_packages_from_manifest_partially_bad_primed_staged(self,):
        """Test get_staged_packages_from_manifest() - one bad primed-stage is
           ignored but others are still added """

        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision_with_primed_stage][
                "manifest_yaml"
            ],
            Loader=yaml.SafeLoader,
        )
        m["primed-stage-packages"].append("foo")

        res = store.get_staged_and_build_packages_from_manifest(m)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue(len(res) > 0)
        self.assertFalse("foo" in res)
        self.assertTrue("staged" in res)
        self.assertTrue("libxcursor1" in res["staged"])
        self.assertTrue("1:1.1.14-1" in res["staged"]["libxcursor1"])
        self.assertFalse("build" in res)

    def test_check_get_staged_packages_from_manifest_primed_staged_and_staged_packages_are_none(
        self,
    ):
        """Test get_staged_packages_from_manifest() - bad primed-stage"""
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        m["primed-stage-packages"] = None
        for p in m["parts"]:
            if "stage-packages" in m["parts"][p]:
                m["parts"][p]["stage-packages"] = None

        res = store.get_staged_and_build_packages_from_manifest(m)
        self.assertEqual(res, None)

    def test_check_get_staged_packages_from_manifest_primed_staged_is_none_and_staged_packages_are_empty(
        self,
    ):
        """Test get_staged_packages_from_manifest() - bad primed-stage"""
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        m["primed-stage-packages"] = None
        for p in m["parts"]:
            if "stage-packages" in m["parts"][p]:
                m["parts"][p]["stage-packages"] = []

        res = store.get_staged_and_build_packages_from_manifest(m)
        self.assertEqual(res, None)

    def test_check_get_staged_packages_from_manifest_bad_primed_stage_and_no_staged_packages(
        self,
    ):
        """Test get_staged_packages_from_manifest() - bad primed-stage and no
           staged"""
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        for part in m["parts"]:
            m["parts"][part]["stage-packages"] = []
        m["primed-stage-packages"] = ["foo"]

        res = store.get_staged_and_build_packages_from_manifest(m)
        self.assertEqual(res, None)

    def test_check_get_staged_packages_from_manifest_empty_staged_and_no_primed_stage(
        self,
    ):
        """Test get_staged_packages_from_manifest() - empty staged"""
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        m["parts"]["0ad-launcher"]["stage-packages"] = []

        res = store.get_staged_and_build_packages_from_manifest(m)
        self.assertEqual(res, None)

    def test_check_get_staged_packages_from_manifest_binary_ignored_and_no_primed_stage(
        self,
    ):
        """Test get_staged_packages_from_manifest() - binary ignored, no
           primed-stage"""
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        m["parts"]["0ad-launcher"]["stage-packages"].append(
            "linux-libc-dev=4.4.0-104.127"
        )

        res = store.get_staged_and_build_packages_from_manifest(m)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue(len(res) > 0)
        self.assertTrue("staged" in res)
        self.assertTrue("libxcursor1" in res["staged"])
        self.assertTrue("1:1.1.14-1" in res["staged"]["libxcursor1"])
        # make sure the ignored package is not present
        self.assertFalse("linux-libc-dev" in res["staged"])
        self.assertFalse("build" in res)

    def test_check_get_staged_packages_from_manifest_with_primed_stage_binary_ignored(
        self,
    ):
        """Test get_staged_packages_from_manifest() - binary ignored,
           primed-stage exists"""
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision_with_primed_stage][
                "manifest_yaml"
            ],
            Loader=yaml.SafeLoader,
        )
        m["primed-stage-packages"].append("linux-libc-dev=4.4.0-104.127")

        res = store.get_staged_and_build_packages_from_manifest(m)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue(len(res) > 0)
        self.assertTrue("staged" in res)
        self.assertTrue("libxcursor1" in res["staged"])
        self.assertTrue("1:1.1.14-1" in res["staged"]["libxcursor1"])
        # make sure the ignored package is not present
        self.assertFalse("linux-libc-dev" in res)
        self.assertFalse("build" in res)

    def test_check_get_secnots_for_manifest_with_no_primed_stage_packages(self):
        """Test get_secnots_for_manifest()"""
        has_build_packages = [True, False]
        has_secnot_for_build_packages = [True, False]

        for build_packages in has_build_packages:
            m = yaml.load(
                self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )
            if build_packages:
                # Adding faked-by-review-tools part
                m["parts"]["faked-by-review-tools"] = {}
                m["parts"]["faked-by-review-tools"]["build-packages"] = [
                    "snapcraft=1.1"
                ]

            for sec_not_for_build_packages in has_secnot_for_build_packages:
                if sec_not_for_build_packages:
                    secnot_db = usn.read_usn_db(
                        "./tests/test-usn-unittest-build-pgks.db"
                    )
                    res = store.get_secnots_for_manifest(m, secnot_db)
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)

                self.assertTrue(isinstance(res, dict))
                if build_packages and sec_not_for_build_packages:
                    self.assertTrue("build" in res)
                    self.assertEqual(len(res["build"]), 1)
                    self.assertTrue("snapcraft" in res["build"])
                    self.assertEqual(len(res["build"]["snapcraft"]), 1)
                    self.assertTrue("5501-1" in res["build"]["snapcraft"])
                    self.assertEqual(len(res), 2)
                else:
                    self.assertFalse("build" in res)
                    self.assertEqual(len(res), 1)

                self.assertTrue("staged" in res)
                self.assertEqual(len(res["staged"]), 2)
                self.assertTrue("libxcursor1" in res["staged"])
                self.assertEqual(len(res["staged"]["libxcursor1"]), 1)
                self.assertEqual(res["staged"]["libxcursor1"][0], "3501-1")
                self.assertTrue("libtiff5" in res["staged"])
                self.assertEqual(len(res["staged"]["libtiff5"]), 2)
                self.assertTrue("3602-1" in res["staged"]["libtiff5"])
                self.assertTrue("3606-1" in res["staged"]["libtiff5"])

    def test_check_get_secnots_for_manifest_with_empty_primed_stage_list(self):
        """Test get_secnots_for_manifest() - primed-stage-packages empty"""
        has_build_packages = [True, False]
        has_secnot_for_build_packages = [True, False]

        for build_packages in has_build_packages:
            m = yaml.load(
                self.store_db[0]["revisions"][self.first_revision_with_primed_stage][
                    "manifest_yaml"
                ],
                Loader=yaml.SafeLoader,
            )

            m["primed-stage-packages"] = []
            if build_packages:
                # Adding faked-by-review-tools part
                m["parts"]["faked-by-review-tools"] = {}
                m["parts"]["faked-by-review-tools"]["build-packages"] = [
                    "snapcraft=1.1"
                ]

            for sec_not_for_build_packages in has_secnot_for_build_packages:
                if sec_not_for_build_packages:
                    secnot_db = usn.read_usn_db(
                        "./tests/test-usn-unittest-build-pgks.db"
                    )
                    res = store.get_secnots_for_manifest(m, secnot_db)
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)

                self.assertTrue(isinstance(res, dict))
                if build_packages and sec_not_for_build_packages:
                    self.assertTrue("build" in res)
                    self.assertEqual(len(res["build"]), 1)
                    self.assertTrue("snapcraft" in res["build"])
                    self.assertEqual(len(res["build"]["snapcraft"]), 1)
                    self.assertTrue("5501-1" in res["build"]["snapcraft"])
                    self.assertEqual(len(res), 1)
                else:
                    self.assertFalse("build" in res)
                    self.assertEqual(len(res), 0)

                self.assertFalse("stage-packages" in res)

    def test_check_get_secnots_for_manifest_with_primed_stage_equals_none(self):
        """Test get_secnots_for_manifest() primed-stage-packages None"""
        has_build_packages = [True, False]
        has_secnot_for_build_packages = [True, False]

        for build_packages in has_build_packages:
            m = yaml.load(
                self.store_db[0]["revisions"][self.first_revision_with_primed_stage][
                    "manifest_yaml"
                ],
                Loader=yaml.SafeLoader,
            )

            m["primed-stage-packages"] = None
            if build_packages:
                # Adding faked-by-review-tools part
                m["parts"]["faked-by-review-tools"] = {}
                m["parts"]["faked-by-review-tools"]["build-packages"] = [
                    "snapcraft=1.1"
                ]

            for sec_not_for_build_packages in has_secnot_for_build_packages:
                if sec_not_for_build_packages:
                    secnot_db = usn.read_usn_db(
                        "./tests/test-usn-unittest-build-pgks.db"
                    )
                    res = store.get_secnots_for_manifest(m, secnot_db)
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)
                self.assertTrue(isinstance(res, dict))
                if build_packages and sec_not_for_build_packages:
                    self.assertTrue("build" in res)
                    self.assertEqual(len(res["build"]), 1)
                    self.assertTrue("snapcraft" in res["build"])
                    self.assertEqual(len(res["build"]["snapcraft"]), 1)
                    self.assertTrue("5501-1" in res["build"]["snapcraft"])
                    self.assertEqual(len(res), 2)
                else:
                    self.assertFalse("build" in res)
                    self.assertEqual(len(res), 1)

                self.assertTrue("staged" in res)
                self.assertEqual(len(res["staged"]), 2)
                self.assertTrue("libxcursor1" in res["staged"])
                self.assertEqual(len(res["staged"]["libxcursor1"]), 1)
                self.assertEqual(res["staged"]["libxcursor1"][0], "3501-1")
                self.assertTrue("libtiff5" in res["staged"])
                self.assertEqual(len(res["staged"]["libtiff5"]), 2)
                self.assertTrue("3602-1" in res["staged"]["libtiff5"])
                self.assertTrue("3606-1" in res["staged"]["libtiff5"])

    def test_check_get_secnots_for_manifest_with_primed_stage_list_equal_to_staged_packages_list(
        self,
    ):
        """Test get_secnots_for_manifest() primed-stage-packages same as
           staged-packages"""
        has_build_packages = [True, False]
        has_secnot_for_build_packages = [True, False]

        for build_packages in has_build_packages:
            m = yaml.load(
                self.store_db[0]["revisions"][self.first_revision_with_primed_stage][
                    "manifest_yaml"
                ],
                Loader=yaml.SafeLoader,
            )
            if build_packages:
                # Adding faked-by-review-tools part
                m["parts"]["faked-by-review-tools"] = {}
                m["parts"]["faked-by-review-tools"]["build-packages"] = [
                    "snapcraft=1.1"
                ]

            for sec_not_for_build_packages in has_secnot_for_build_packages:
                if sec_not_for_build_packages:
                    secnot_db = usn.read_usn_db(
                        "./tests/test-usn-unittest-build-pgks.db"
                    )
                    res = store.get_secnots_for_manifest(m, secnot_db)
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)
                self.assertTrue(isinstance(res, dict))
                if build_packages and sec_not_for_build_packages:
                    self.assertTrue("build" in res)
                    self.assertEqual(len(res["build"]), 1)
                    self.assertTrue("snapcraft" in res["build"])
                    self.assertEqual(len(res["build"]["snapcraft"]), 1)
                    self.assertTrue("5501-1" in res["build"]["snapcraft"])
                    self.assertEqual(len(res), 2)
                else:
                    self.assertFalse("build" in res)
                    self.assertEqual(len(res), 1)

                self.assertTrue(isinstance(res, dict))
                self.assertTrue("staged" in res)
                self.assertEqual(len(res["staged"]), 2)
                self.assertTrue("libxcursor1" in res["staged"])
                self.assertEqual(len(res["staged"]["libxcursor1"]), 1)
                self.assertEqual(res["staged"]["libxcursor1"][0], "3501-1")
                self.assertTrue("libtiff5" in res["staged"])
                self.assertEqual(len(res["staged"]["libtiff5"]), 2)
                self.assertTrue("3602-1" in res["staged"]["libtiff5"])
                self.assertTrue("3606-1" in res["staged"]["libtiff5"])

    def test_check_get_secnots_for_manifest_with_primed_stage_list_smaller_than_staged_packages_list(
        self,
    ):
        """Test get_secnots_for_manifest() primed-stage-packages smaller than
           staged-packages """
        has_build_packages = [True, False]
        has_secnot_for_build_packages = [True, False]

        for build_packages in has_build_packages:
            m = yaml.load(
                self.store_db[0]["revisions"][self.first_revision_with_primed_stage][
                    "manifest_yaml"
                ],
                Loader=yaml.SafeLoader,
            )

            m["primed-stage-packages"].remove("libxcursor1=1:1.1.14-1")
            if build_packages:
                # Adding faked-by-review-tools part
                m["parts"]["faked-by-review-tools"] = {}
                m["parts"]["faked-by-review-tools"]["build-packages"] = [
                    "snapcraft=1.1"
                ]

            for sec_not_for_build_packages in has_secnot_for_build_packages:
                if sec_not_for_build_packages:
                    secnot_db = usn.read_usn_db(
                        "./tests/test-usn-unittest-build-pgks.db"
                    )
                    res = store.get_secnots_for_manifest(m, secnot_db)
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)
                self.assertTrue(isinstance(res, dict))
                if build_packages and sec_not_for_build_packages:
                    self.assertTrue("build" in res)
                    self.assertEqual(len(res["build"]), 1)
                    self.assertTrue("snapcraft" in res["build"])
                    self.assertEqual(len(res["build"]["snapcraft"]), 1)
                    self.assertTrue("5501-1" in res["build"]["snapcraft"])
                    self.assertEqual(len(res), 2)
                else:
                    self.assertFalse("build" in res)
                    self.assertEqual(len(res), 1)

                self.assertTrue("staged" in res)
                self.assertTrue("libtiff5" in res["staged"])
                self.assertEqual(len(res["staged"]["libtiff5"]), 2)
                self.assertTrue("3602-1" in res["staged"]["libtiff5"])
                self.assertTrue("3606-1" in res["staged"]["libtiff5"])
                # since it was removed from primed-stage-packages, we
                # shouldn't have a notice
                self.assertFalse("libxcursor1" in res)

    def test_check_get_secnots_for_manifest_empty_staged(self):
        """Test get_secnots_for_manifest() - empty staged"""
        has_build_packages = [True, False]
        has_secnot_for_build_packages = [True, False]

        for build_packages in has_build_packages:
            m = yaml.load(
                self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )
            m["parts"]["0ad-launcher"]["stage-packages"] = []
            if build_packages:
                # Adding faked-by-review-tools part
                m["parts"]["faked-by-review-tools"] = {}
                m["parts"]["faked-by-review-tools"]["build-packages"] = [
                    "snapcraft=1.1"
                ]

            for sec_not_for_build_packages in has_secnot_for_build_packages:
                if sec_not_for_build_packages:
                    secnot_db = usn.read_usn_db(
                        "./tests/test-usn-unittest-build-pgks.db"
                    )
                    res = store.get_secnots_for_manifest(m, secnot_db)
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)
                self.assertTrue(isinstance(res, dict))
                self.assertFalse("staged" in res)
                if build_packages and sec_not_for_build_packages:
                    self.assertTrue("build" in res)
                    self.assertEqual(len(res["build"]), 1)
                    self.assertTrue("snapcraft" in res["build"])
                    self.assertEqual(len(res["build"]["snapcraft"]), 1)
                    self.assertTrue("5501-1" in res["build"]["snapcraft"])
                    self.assertEqual(len(res), 1)
                else:
                    self.assertFalse("build" in res)
                    self.assertEqual(len(res), 0)

    def test_check_get_secnots_for_manifest_empty_primed_stage_and_staged(self):
        """Test get_secnots_for_manifest() - empty primed-stage and staged"""
        has_build_packages = [True, False]
        has_secnot_for_build_packages = [True, False]

        for build_packages in has_build_packages:
            m = yaml.load(
                self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )
            m["parts"]["0ad-launcher"]["stage-packages"] = []
            m["primed-stage-packages"] = []

            if build_packages:
                # Adding faked-by-review-tools part
                m["parts"]["faked-by-review-tools"] = {}
                m["parts"]["faked-by-review-tools"]["build-packages"] = [
                    "snapcraft=1.1"
                ]

            for sec_not_for_build_packages in has_secnot_for_build_packages:
                if sec_not_for_build_packages:
                    secnot_db = usn.read_usn_db(
                        "./tests/test-usn-unittest-build-pgks.db"
                    )
                    res = store.get_secnots_for_manifest(m, secnot_db)
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)
                self.assertTrue(isinstance(res, dict))
                self.assertFalse("staged" in res)
                if build_packages and sec_not_for_build_packages:
                    self.assertTrue("build" in res)
                    self.assertEqual(len(res["build"]), 1)
                    self.assertTrue("snapcraft" in res["build"])
                    self.assertEqual(len(res["build"]["snapcraft"]), 1)
                    self.assertTrue("5501-1" in res["build"]["snapcraft"])
                    self.assertEqual(len(res), 1)
                else:
                    self.assertFalse("build" in res)
                    self.assertEqual(len(res), 0)

    def test_check_get_secnots_for_manifest_empty_staged_with_cves(self,):
        """Test get_secnots_for_manifest() - cves"""
        has_build_packages = [True, False]
        has_secnot_for_build_packages = [True, False]

        for build_packages in has_build_packages:
            m = yaml.load(
                self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )
            m["parts"]["0ad-launcher"]["stage-packages"] = []
            if build_packages:
                # Adding faked-by-review-tools part
                m["parts"]["faked-by-review-tools"] = {}
                m["parts"]["faked-by-review-tools"]["build-packages"] = [
                    "snapcraft=1.1"
                ]

            for sec_not_for_build_packages in has_secnot_for_build_packages:
                if sec_not_for_build_packages:
                    secnot_db = usn.read_usn_db(
                        "./tests/test-usn-unittest-build-pgks.db"
                    )
                    res = store.get_secnots_for_manifest(m, secnot_db, with_cves=True)
                else:
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_db, with_cves=True
                    )
                self.assertTrue(isinstance(res, dict))
                self.assertFalse("staged" in res)
                if build_packages and sec_not_for_build_packages:
                    self.assertTrue("build" in res)
                    self.assertEqual(len(res["build"]), 1)
                    self.assertTrue("snapcraft" in res["build"])
                    self.assertEqual(len(res["build"]["snapcraft"]), 1)
                    self.assertTrue("5501-1" in res["build"]["snapcraft"])
                    self.assertTrue(
                        "CVE-2020-9999" in res["build"]["snapcraft"]["5501-1"]
                    )
                    self.assertEqual(len(res), 1)
                else:
                    self.assertFalse("build" in res)
                    self.assertEqual(len(res), 0)

    def test_check_get_secnots_for_manifest_empty_primed_stage_and_staged_with_cves(
        self,
    ):
        """Test get_secnots_for_manifest() - cves, no primed-stage"""
        has_build_packages = [True, False]
        has_secnot_for_build_packages = [True, False]

        for build_packages in has_build_packages:
            m = yaml.load(
                self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )
            m["primed-stage-packages"] = []
            if build_packages:
                # Adding faked-by-review-tools part
                m["parts"]["faked-by-review-tools"] = {}
                m["parts"]["faked-by-review-tools"]["build-packages"] = [
                    "snapcraft=1.1"
                ]

            for sec_not_for_build_packages in has_secnot_for_build_packages:
                if sec_not_for_build_packages:
                    secnot_db = usn.read_usn_db(
                        "./tests/test-usn-unittest-build-pgks.db"
                    )
                    res = store.get_secnots_for_manifest(m, secnot_db, with_cves=True)
                else:
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_db, with_cves=True
                    )
                self.assertTrue(isinstance(res, dict))
                self.assertFalse("staged" in res)
                if build_packages and sec_not_for_build_packages:
                    self.assertTrue("build" in res)
                    self.assertEqual(len(res["build"]), 1)
                    self.assertTrue("snapcraft" in res["build"])
                    self.assertEqual(len(res["build"]["snapcraft"]), 1)
                    self.assertTrue("5501-1" in res["build"]["snapcraft"])
                    self.assertTrue(
                        "CVE-2020-9999" in res["build"]["snapcraft"]["5501-1"]
                    )
                    self.assertEqual(len(res), 1)
                else:
                    self.assertFalse("build" in res)
                    self.assertEqual(len(res), 0)

    def test_check_get_secnots_for_manifest_with_primed_stage_list_equal_to_staged_packages_list_with_cves(
        self,
    ):
        """Test get_secnots_for_manifest() - cves, primed-stage same as staged"""
        has_build_packages = [True, False]
        has_secnot_for_build_packages = [True, False]

        for build_packages in has_build_packages:
            m = yaml.load(
                self.store_db[0]["revisions"][self.first_revision_with_primed_stage][
                    "manifest_yaml"
                ],
                Loader=yaml.SafeLoader,
            )

            if build_packages:
                # Adding faked-by-review-tools part
                m["parts"]["faked-by-review-tools"] = {}
                m["parts"]["faked-by-review-tools"]["build-packages"] = [
                    "snapcraft=1.1"
                ]

            for sec_not_for_build_packages in has_secnot_for_build_packages:
                if sec_not_for_build_packages:
                    secnot_db = usn.read_usn_db(
                        "./tests/test-usn-unittest-build-pgks.db"
                    )
                    res = store.get_secnots_for_manifest(m, secnot_db, with_cves=True)
                else:
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_db, with_cves=True
                    )
                self.assertTrue(isinstance(res, dict))
                if build_packages and sec_not_for_build_packages:
                    self.assertTrue("build" in res)
                    self.assertEqual(len(res["build"]), 1)
                    self.assertTrue("snapcraft" in res["build"])
                    self.assertEqual(len(res["build"]["snapcraft"]), 1)
                    self.assertTrue("5501-1" in res["build"]["snapcraft"])
                    self.assertTrue(
                        "CVE-2020-9999" in res["build"]["snapcraft"]["5501-1"]
                    )
                    self.assertEqual(len(res), 2)
                else:
                    self.assertFalse("build" in res)
                    self.assertEqual(len(res), 1)

                self.assertTrue("staged" in res)
                self.assertEqual(len(res["staged"]), 2)
                self.assertTrue("libxcursor1" in res["staged"])
                self.assertEqual(len(res["staged"]["libxcursor1"]), 1)
                self.assertTrue("3501-1" in res["staged"]["libxcursor1"])
                self.assertTrue(
                    isinstance(res["staged"]["libxcursor1"]["3501-1"], list)
                )
                self.assertEqual(len(res["staged"]["libxcursor1"]["3501-1"]), 1)
                self.assertTrue(
                    "CVE-2017-16612" in res["staged"]["libxcursor1"]["3501-1"]
                )
                self.assertTrue("libtiff5" in res["staged"])
                self.assertEqual(len(res["staged"]["libtiff5"]), 2)
                self.assertTrue(isinstance(res["staged"]["libtiff5"]["3602-1"], list))
                self.assertEqual(len(res["staged"]["libtiff5"]["3602-1"]), 27)
                self.assertTrue(isinstance(res["staged"]["libtiff5"]["3606-1"], list))
                self.assertEqual(len(res["staged"]["libtiff5"]["3606-1"]), 12)

    def test_check_get_secnots_for_manifest_with_primed_stage_list_smaller_than_staged_packages_list_with_cves(
        self,
    ):
        """Test get_secnots_for_manifest() - cves, primed-stage smaller
         than staged"""
        has_build_packages = [True, False]
        has_secnot_for_build_packages = [True, False]

        for build_packages in has_build_packages:
            m = yaml.load(
                self.store_db[0]["revisions"][self.first_revision_with_primed_stage][
                    "manifest_yaml"
                ],
                Loader=yaml.SafeLoader,
            )

            m["primed-stage-packages"].remove("libxcursor1=1:1.1.14-1")

            if build_packages:
                # Adding faked-by-review-tools part
                m["parts"]["faked-by-review-tools"] = {}
                m["parts"]["faked-by-review-tools"]["build-packages"] = [
                    "snapcraft=1.1"
                ]

            for sec_not_for_build_packages in has_secnot_for_build_packages:
                if sec_not_for_build_packages:
                    secnot_db = usn.read_usn_db(
                        "./tests/test-usn-unittest-build-pgks.db"
                    )
                    res = store.get_secnots_for_manifest(m, secnot_db, with_cves=True)
                else:
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_db, with_cves=True
                    )
                self.assertTrue(isinstance(res, dict))
                if build_packages and sec_not_for_build_packages:
                    self.assertTrue("build" in res)
                    self.assertEqual(len(res["build"]), 1)
                    self.assertTrue("snapcraft" in res["build"])
                    self.assertEqual(len(res["build"]["snapcraft"]), 1)
                    self.assertTrue("5501-1" in res["build"]["snapcraft"])
                    self.assertTrue(
                        "CVE-2020-9999" in res["build"]["snapcraft"]["5501-1"]
                    )
                    self.assertEqual(len(res), 2)
                else:
                    self.assertFalse("build" in res)
                    self.assertEqual(len(res), 1)

                self.assertTrue("libtiff5" in res["staged"])
                self.assertTrue("staged" in res)
                self.assertEqual(len(res["staged"]["libtiff5"]), 2)
                self.assertTrue(isinstance(res["staged"]["libtiff5"]["3602-1"], list))
                self.assertEqual(len(res["staged"]["libtiff5"]["3602-1"]), 27)
                self.assertTrue(isinstance(res["staged"]["libtiff5"]["3606-1"], list))
                self.assertEqual(len(res["staged"]["libtiff5"]["3606-1"]), 12)

                # since it was removed from primed-stage-packages, we
                # shouldn't have a notice
                self.assertFalse("libxcursor1" in res)

    def test_check_get_secnots_for_manifest_missing_primed_stage_packages_has_newer(
        self,
    ):
        """Test get_secnots_for_manifest() - has newer"""
        has_build_packages = [True, False]
        has_secnot_for_build_packages = [True, False]

        for build_packages in has_build_packages:
            m = yaml.load(
                self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )

            # clear out all the stage-packages and then add one that has a
            # newer package than what is in the security notices
            for part in m["parts"]:
                m["parts"][part]["stage-packages"] = []
                if part == "0ad-launcher":
                    m["parts"][part]["stage-packages"].append(
                        "libxcursor1=999:1.1.14-1"
                    )

            if build_packages:
                # Adding faked-by-review-tools part
                m["parts"]["faked-by-review-tools"] = {}
                m["parts"]["faked-by-review-tools"]["build-packages"] = [
                    "snapcraft=1.1"
                ]

            for sec_not_for_build_packages in has_secnot_for_build_packages:
                if sec_not_for_build_packages:
                    secnot_db = usn.read_usn_db(
                        "./tests/test-usn-unittest-build-pgks.db"
                    )
                    res = store.get_secnots_for_manifest(m, secnot_db)
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)
                self.assertTrue(isinstance(res, dict))
                if build_packages and sec_not_for_build_packages:
                    self.assertTrue("build" in res)
                    self.assertEqual(len(res["build"]), 1)
                    self.assertTrue("snapcraft" in res["build"])
                    self.assertEqual(len(res["build"]["snapcraft"]), 1)
                    self.assertTrue("5501-1" in res["build"]["snapcraft"])
                    self.assertEqual(len(res), 1)
                else:
                    self.assertFalse("build" in res)
                    self.assertEqual(len(res), 0)

    def test_check_get_secnots_for_manifest_primed_staged_list_equal_to_staged_list_has_newer(
        self,
    ):
        """Test get_secnots_for_manifest() - primed-stage equal to stage,
        has newer"""
        has_build_packages = [True, False]
        has_secnot_for_build_packages = [True, False]
        for build_packages in has_build_packages:
            m = yaml.load(
                self.store_db[0]["revisions"][self.first_revision_with_primed_stage][
                    "manifest_yaml"
                ],
                Loader=yaml.SafeLoader,
            )

            # clear out all the stage-packages and then add one that has a
            # newer package than what is in the security notices
            for part in m["parts"]:
                m["parts"][part]["stage-packages"] = []
                if part == "0ad-launcher":
                    m["parts"][part]["stage-packages"].append(
                        "libxcursor1=999:1.1.14-1"
                    )

            m["primed-stage-packages"] = []
            m["primed-stage-packages"].append("libxcursor1=999:1.1.14-1")

            if build_packages:
                # Adding faked-by-review-tools part
                m["parts"]["faked-by-review-tools"] = {}
                m["parts"]["faked-by-review-tools"]["build-packages"] = [
                    "snapcraft=1.1"
                ]

            for sec_not_for_build_packages in has_secnot_for_build_packages:
                if sec_not_for_build_packages:
                    secnot_db = usn.read_usn_db(
                        "./tests/test-usn-unittest-build-pgks.db"
                    )
                    res = store.get_secnots_for_manifest(m, secnot_db)
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)
                self.assertTrue(isinstance(res, dict))
                if build_packages and sec_not_for_build_packages:
                    self.assertTrue("build" in res)
                    self.assertEqual(len(res["build"]), 1)
                    self.assertTrue("snapcraft" in res["build"])
                    self.assertEqual(len(res["build"]["snapcraft"]), 1)
                    self.assertTrue("5501-1" in res["build"]["snapcraft"])
                    self.assertEqual(len(res), 1)
                else:
                    self.assertFalse("build" in res)
                    self.assertEqual(len(res), 0)

    def test_check_get_secnots_for_manifest_primed_staged_list_smaller_than_staged_list_has_newer(
        self,
    ):
        """Test get_secnots_for_manifest() - primed-stage smaller than stage
        has newer"""
        has_build_packages = [True, False]
        has_secnot_for_build_packages = [True, False]
        for build_packages in has_build_packages:
            m = yaml.load(
                self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )

            # clear out all the stage-packages and then add one that has a
            # newer package than what is in the security notices and one that
            # is older than what is in the security notices
            for part in m["parts"]:
                m["parts"][part]["stage-packages"] = []
                if part == "0ad-launcher":
                    m["parts"][part]["stage-packages"].append(
                        "libxcursor1=999:1.1.14-1"
                    )
                    m["parts"][part]["stage-packages"].append(
                        "libtiff5=4.0.6-1ubuntu0.3"
                    )  # 3606-1 is newer

            m["primed-stage-packages"] = ["libxcursor1=999:1.1.14-1"]

            if build_packages:
                # Adding faked-by-review-tools part
                m["parts"]["faked-by-review-tools"] = {}
                m["parts"]["faked-by-review-tools"]["build-packages"] = [
                    "snapcraft=1.1"
                ]

            for sec_not_for_build_packages in has_secnot_for_build_packages:
                if sec_not_for_build_packages:
                    secnot_db = usn.read_usn_db(
                        "./tests/test-usn-unittest-build-pgks.db"
                    )
                    res = store.get_secnots_for_manifest(m, secnot_db)
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)
                self.assertTrue(isinstance(res, dict))
                if build_packages and sec_not_for_build_packages:
                    self.assertTrue("build" in res)
                    self.assertEqual(len(res["build"]), 1)
                    self.assertTrue("snapcraft" in res["build"])
                    self.assertEqual(len(res["build"]["snapcraft"]), 1)
                    self.assertTrue("5501-1" in res["build"]["snapcraft"])
                    self.assertEqual(len(res), 1)
                else:
                    self.assertFalse("build" in res)
                    self.assertEqual(len(res), 0)

    def test_check_get_ubuntu_release_from_manifest_store_db(self):
        """Test get_ubuntu_release_from_manifest() - test-store-unittest-1.db"""
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEqual(res, "xenial")

    def test_check_get_ubuntu_release_from_manifest(self):
        """Test get_ubuntu_release_from_manifest() - no base, use default"""
        m = self.manifest_basic
        res = store.get_ubuntu_release_from_manifest(m)
        # no base
        self.assertEqual(res, "xenial")

    def test_check_get_ubuntu_release_from_manifest_known_bases(self):
        """Test get_ubuntu_release_from_manifest() - base: <known>"""
        for base in store.snap_to_release:
            m = copy.deepcopy(self.manifest_basic)
            m["base"] = base
            res = store.get_ubuntu_release_from_manifest(m)
            self.assertEqual(res, store.snap_to_release[base])

    def test_check_get_ubuntu_release_from_manifest_unknown_base_snap1(self):
        """Test get_ubuntu_release_from_manifest() - unknown base, known installed snap"""
        for base in store.snap_to_release:
            m = copy.deepcopy(self.manifest_basic)
            m["base"] = "some-other-base"
            m["parts"]["part2"]["installed-snaps"].append("%s=123" % base)

            res = store.get_ubuntu_release_from_manifest(m)
            self.assertEqual(res, store.snap_to_release[base])

    def test_check_get_ubuntu_release_from_manifest_unknown_base_bad_snap(self):
        """Test get_ubuntu_release_from_manifest() - unknown base, bad snap"""
        m = copy.deepcopy(self.manifest_basic)
        m["base"] = "some-other-base"
        m["parts"]["part1"]["installed-snaps"] = ["core18"]
        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEqual(res, "xenial")

    def test_check_get_ubuntu_release_from_manifest_unknown_base_other_snap(self):
        """Test get_ubuntu_release_from_manifest() - unknown base, other installed snap"""
        m = copy.deepcopy(self.manifest_basic)
        m["base"] = "some-other-base"
        m["parts"]["part1"]["installed-snaps"] = ["other=234"]
        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEqual(res, "xenial")

    def test_check_get_ubuntu_release_from_manifest_missing_parts(self):
        """Test get_ubuntu_release_from_manifest() - missing parts"""
        m = copy.deepcopy(self.manifest_basic)
        del m["parts"]

        try:
            store.get_ubuntu_release_from_manifest(m)
        except ValueError:
            return

        raise Exception("Should have raised ValueError")  # pragma: nocover

    def test_check_get_ubuntu_release_from_manifest_base18_with_others(self):
        """Test get_ubuntu_release_from_manifest() - unknown base, known installed with other"""
        m = copy.deepcopy(self.manifest_basic)
        m["base"] = "some-other-base"
        m["parts"]["part1"]["installed-snaps"].append("abc=123")
        m["parts"]["part2"]["installed-snaps"].append("base-18=123")

        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEqual(res, "bionic")

    def test_check_get_ubuntu_release_from_manifest_base18_with_core(self):
        """Test get_ubuntu_release_from_manifest() - unknown base, two known installed"""
        m = copy.deepcopy(self.manifest_basic)
        m["base"] = "some-other-base"
        m["parts"]["part1"]["installed-snaps"].append("core=123")
        m["parts"]["part2"]["installed-snaps"].append("base-18=123")

        try:
            store.get_ubuntu_release_from_manifest(m)
        except ValueError:
            return

        raise Exception("Should have raised ValueError")  # pragma: nocover

    def test_check_get_ubuntu_release_from_manifest_os_release_xenial(self):
        """Test get_ubuntu_release_from_manifest() - ubuntu/xenial"""
        m = copy.deepcopy(self.manifest_basic)
        m["snapcraft-os-release-id"] = "ubuntu"
        m["snapcraft-os-release-version-id"] = "16.04"
        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEqual(res, "xenial")

    def test_check_get_ubuntu_release_from_manifest_os_release_artful(self):
        """Test get_ubuntu_release_from_manifest() - ubuntu/artful"""
        m = copy.deepcopy(self.manifest_basic)
        m["snapcraft-os-release-id"] = "ubuntu"
        m["snapcraft-os-release-version-id"] = "17.10"
        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEqual(res, "artful")

    def test_check_get_ubuntu_release_from_manifest_os_release_bionic(self):
        """Test get_ubuntu_release_from_manifest() - ubuntu/bionic"""
        m = copy.deepcopy(self.manifest_basic)
        m["snapcraft-os-release-id"] = "ubuntu"
        m["snapcraft-os-release-version-id"] = "18.04"
        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEqual(res, "bionic")

    def test_check_get_ubuntu_release_from_manifest_os_release_neon_bionic_alt_base(
        self,
    ):
        """Test get_ubuntu_release_from_manifest() - neon/18.04 with base: other"""
        m = copy.deepcopy(self.manifest_basic)
        m["base"] = "some-other-base"
        m["snapcraft-os-release-id"] = "neon"
        m["snapcraft-os-release-version-id"] = "18.04"
        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEqual(res, "bionic")

    def test_check_get_ubuntu_release_from_manifest_os_release_neon_nonexist_ver(self):
        """Test get_ubuntu_release_from_manifest() - neon/nonexistent with base: other"""
        m = copy.deepcopy(self.manifest_basic)
        m["base"] = "some-other-base"
        m["snapcraft-os-release-id"] = "neon"
        m["snapcraft-os-release-version-id"] = "1"
        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEqual(res, "xenial")

    def test_check_get_ubuntu_release_from_manifest_os_release_neon_bionic_core20(self):
        """Test get_ubuntu_release_from_manifest() - neon/18.04 with base: core20"""
        m = copy.deepcopy(self.manifest_basic)
        m["base"] = "core20"
        m["snapcraft-os-release-id"] = "neon"
        m["snapcraft-os-release-version-id"] = "18.04"
        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEqual(res, "focal")

    def test_check_get_ubuntu_release_from_manifest_os_release_nonexist_os_and_ver(
        self,
    ):
        """Test get_ubuntu_release_from_manifest() - nonexistent os/ver"""
        m = copy.deepcopy(self.manifest_basic)
        m["snapcraft-os-release-id"] = "nonexistent"
        m["snapcraft-os-release-version-id"] = "1"
        res = store.get_ubuntu_release_from_manifest(m)
        # fallback to old behavior
        self.assertEqual(res, "xenial")

    def test_check_get_ubuntu_release_from_manifest_os_release_nonexist_ver(self):
        """Test get_ubuntu_release_from_manifest() - ubuntu/nonexistent"""
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        m["snapcraft-os-release-id"] = "ubuntu"
        m["snapcraft-os-release-version-id"] = "1.02"
        res = store.get_ubuntu_release_from_manifest(m)
        # fallback to old behavior
        self.assertEqual(res, "xenial")

    def test_convert_canonical_kernel_version(self):
        """Test convert_canonical_kernel_version()"""
        # (version, expected)
        tests = [
            ("1.2", "1.2"),
            ("1.3", "1.3"),
            ("1.2~", "1.2~"),
            ("1.3~", "1.3~"),
            ("1.2.3-4.5~16.04.1", "1.2.3.4.999999"),
            ("1.2.3-4.6", "1.2.3.4.999999"),
            ("1.2.3-4-6~16.04.1", "1.2.3.4.999999"),
            ("4.4.0-161", "4.4.0.161.999999"),
            ("4.4.0-140-1", "4.4.0.140.999999"),
        ]
        for (v, expected) in tests:
            res = store.convert_canonical_kernel_version(v)
            self.assertEqual(res, expected)

    def test_convert_canonical_app_version(self):
        """Test convert_canonical_app_version()"""
        # (version, expected)
        tests = [
            ("1.2", "1.2"),
            ("1.2~", "1.2~"),
            ("1.2-3", "1.2-3"),
            ("1.2-3ubuntu4.5", "1.2-3ubuntu4.5"),
            ("1.2-3ubuntu4.5~16.04.1", "1.2-3ubuntu4.5~16.04.1"),
            ("1.2-3+git1234ubuntu0.1", "1.2-3+git1234ubuntu0.1"),
            ("1.2-3+git1234ubuntu0.1+deadbeef", "1.2-3+git1234ubuntu0.1"),
        ]
        for (v, expected) in tests:
            res = store.convert_canonical_app_version(v)
            self.assertEqual(res, expected)

    def test_get_faked_stage_packages_with_no_primed_stage_version(self,):
        """Test get_faked_stage_packages - no primed-stage - version"""
        has_snapcraft_version = [True, False]
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["foo"] = {"bar": "1.2~"}
        m = {}
        m["name"] = "foo"
        m["version"] = "1.2~"
        m["parts"] = {"foo-part": {}}
        for snapcraft_version in has_snapcraft_version:
            if snapcraft_version:
                m["snapcraft-version"] = "1.1.1"
                res = store.get_faked_build_and_stage_packages(m)
                self.assertTrue("faked-by-review-tools" in res["parts"])
                self.assertTrue(
                    "stage-packages" in res["parts"]["faked-by-review-tools"]
                )
                self.assertTrue(
                    "bar=1.2~"
                    in res["parts"]["faked-by-review-tools"]["stage-packages"]
                )
                self.assertTrue(
                    "build-packages" in res["parts"]["faked-by-review-tools"]
                )
                self.assertTrue(
                    "snapcraft=1.1.1"
                    in res["parts"]["faked-by-review-tools"]["build-packages"]
                )
            else:
                snapcraft_version_value = ["not_present", None, ""]
                for invalid_snapcraft_version in snapcraft_version_value:
                    if invalid_snapcraft_version != "not_present":
                        m["snapcraft-version"] = invalid_snapcraft_version
                    else:
                        del m["snapcraft-version"]
                    res = store.get_faked_build_and_stage_packages(m)
                    self.assertTrue("faked-by-review-tools" in res["parts"])
                    self.assertTrue(
                        "stage-packages" in res["parts"]["faked-by-review-tools"]
                    )
                    self.assertTrue(
                        "bar=1.2~"
                        in res["parts"]["faked-by-review-tools"]["stage-packages"]
                    )
                    self.assertTrue(
                        "build-packages" in res["parts"]["faked-by-review-tools"]
                    )
                    self.assertEqual(
                        len(res["parts"]["faked-by-review-tools"]["build-packages"]), 0
                    )

    def test_get_faked_stage_packages_has_no_side_effect_on_original_manifest(self):
        """Test get_faked_stage_packages - no side effect on m"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["foo"] = {"bar": "1.2~"}
        m = {}
        m["name"] = "foo"
        m["version"] = "1.2~"
        m["parts"] = {"foo-part": {}}
        has_snapcraft_version = [True, False]
        for snapcraft_version in has_snapcraft_version:
            if snapcraft_version:
                m["snapcraft-version"] = "1.1.1"

            res = store.get_faked_build_and_stage_packages(m)
            self.assertTrue("faked-by-review-tools" in res["parts"])
            self.assertTrue("stage-packages" in res["parts"]["faked-by-review-tools"])
            self.assertTrue(
                "bar=1.2~" in res["parts"]["faked-by-review-tools"]["stage-packages"]
            )
            self.assertTrue("build-packages" in res["parts"]["faked-by-review-tools"])
            self.assertTrue(
                "snapcraft=1.1.1"
                in res["parts"]["faked-by-review-tools"]["build-packages"]
            )
            self.assertFalse("faked-by-review-tools" in m["parts"])

    def test_get_faked_stage_packages_with_none_primed_stage_version(self,):
        """Test get_faked_stage_packages - None primed-stage - non affected snapcraft version"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["foo"] = {"bar": "1.2~"}
        m = {}
        m["name"] = "foo"
        m["version"] = "1.2~"
        m["parts"] = {"foo-part": {}}
        m["primed-stage-packages"] = None

        has_snapcraft_version = [True, False]
        for snapcraft_version in has_snapcraft_version:
            if snapcraft_version:
                m["snapcraft-version"] = "1.1.1"
                res = store.get_faked_build_and_stage_packages(m)
                self.assertTrue("faked-by-review-tools" in res["parts"])
                self.assertTrue(
                    "stage-packages" in res["parts"]["faked-by-review-tools"]
                )
                self.assertTrue(
                    "bar=1.2~"
                    in res["parts"]["faked-by-review-tools"]["stage-packages"]
                )
                self.assertTrue(
                    "build-packages" in res["parts"]["faked-by-review-tools"]
                )
                self.assertTrue(
                    "snapcraft=1.1.1"
                    in res["parts"]["faked-by-review-tools"]["build-packages"]
                )
            else:
                snapcraft_version_value = ["not_present", None, ""]
                for invalid_snapcraft_version in snapcraft_version_value:
                    if invalid_snapcraft_version != "not_present":
                        m["snapcraft-version"] = invalid_snapcraft_version
                    else:
                        del m["snapcraft-version"]
                    res = store.get_faked_build_and_stage_packages(m)
                    self.assertTrue("faked-by-review-tools" in res["parts"])
                    self.assertTrue(
                        "stage-packages" in res["parts"]["faked-by-review-tools"]
                    )
                    self.assertTrue(
                        "bar=1.2~"
                        in res["parts"]["faked-by-review-tools"]["stage-packages"]
                    )
                    self.assertTrue(
                        "build-packages" in res["parts"]["faked-by-review-tools"]
                    )
                    self.assertEqual(
                        len(res["parts"]["faked-by-review-tools"]["build-packages"]), 0
                    )

    def test_get_faked_stage_packages_with_empty_primed_stage_version_and_no_snapcraft_version(
        self,
    ):
        """Test get_faked_stage_packages - empty primed-stage - version"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["foo"] = {"bar": "1.2~"}
        m = {}
        m["name"] = "foo"
        m["version"] = "1.2~"
        m["parts"] = {"foo-part": {}}

        m["primed-stage-packages"] = []
        has_snapcraft_version = [True, False]
        for snapcraft_version in has_snapcraft_version:
            if snapcraft_version:
                m["snapcraft-version"] = "1.1.1"
                res = store.get_faked_build_and_stage_packages(m)
                self.assertTrue("faked-by-review-tools" in res["parts"])
                self.assertTrue("bar=1.2~" in res["primed-stage-packages"])
                self.assertTrue(
                    "build-packages" in res["parts"]["faked-by-review-tools"]
                )
                self.assertEqual(
                    len(res["parts"]["faked-by-review-tools"]["build-packages"]), 1
                )
                self.assertTrue(
                    "snapcraft=1.1.1"
                    in res["parts"]["faked-by-review-tools"]["build-packages"]
                )
            else:
                snapcraft_version_value = ["not_present", None, ""]
                for invalid_snapcraft_version in snapcraft_version_value:
                    if invalid_snapcraft_version != "not_present":
                        m["snapcraft-version"] = invalid_snapcraft_version
                    else:
                        del m["snapcraft-version"]

                res = store.get_faked_build_and_stage_packages(m)
                self.assertTrue("faked-by-review-tools" in res["parts"])
                self.assertTrue("bar=1.2~" in res["primed-stage-packages"])
                self.assertTrue(
                    "build-packages" in res["parts"]["faked-by-review-tools"]
                )
                self.assertEqual(
                    len(res["parts"]["faked-by-review-tools"]["build-packages"]), 0
                )

    def test_get_faked_stage_packages_with_primed_stage_version_and_no_snapcraft_version(
        self,
    ):
        """Test get_faked_stage_packages - primed-stage exists - version"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["foo"] = {"bar": "1.2~"}
        m = {}
        m["name"] = "foo"
        m["version"] = "1.2~"
        m["parts"] = {"foo-part": {}}
        m["primed-stage-packages"] = ["libxcursor1=1:1.1.14-1"]
        has_snapcraft_version = [True, False]
        for snapcraft_version in has_snapcraft_version:
            if snapcraft_version:
                m["snapcraft-version"] = "1.1.1"

                res = store.get_faked_build_and_stage_packages(m)
                self.assertTrue("faked-by-review-tools" in res["parts"])
                self.assertFalse("faked-by-review-tools" in m["parts"])
                self.assertTrue("bar=1.2~" in res["primed-stage-packages"])
                self.assertTrue(
                    "libxcursor1=1:1.1.14-1" in res["primed-stage-packages"]
                )
                self.assertTrue(
                    "build-packages" in res["parts"]["faked-by-review-tools"]
                )
                self.assertEqual(
                    len(res["parts"]["faked-by-review-tools"]["build-packages"]), 1
                )
                self.assertTrue(
                    "snapcraft=1.1.1"
                    in res["parts"]["faked-by-review-tools"]["build-packages"]
                )
            else:
                snapcraft_version_value = ["not_present", None, ""]
                for invalid_snapcraft_version in snapcraft_version_value:
                    if invalid_snapcraft_version != "not_present":
                        m["snapcraft-version"] = invalid_snapcraft_version
                    else:
                        del m["snapcraft-version"]

                    res = store.get_faked_build_and_stage_packages(m)
                    self.assertTrue("faked-by-review-tools" in res["parts"])
                    self.assertFalse("faked-by-review-tools" in m["parts"])
                    self.assertTrue("bar=1.2~" in res["primed-stage-packages"])
                    self.assertTrue(
                        "libxcursor1=1:1.1.14-1" in res["primed-stage-packages"]
                    )
                    self.assertTrue(
                        "build-packages" in res["parts"]["faked-by-review-tools"]
                    )
                    self.assertEqual(
                        len(res["parts"]["faked-by-review-tools"]["build-packages"]), 0
                    )

    def test_get_faked_stage_packages_auto(self):
        """Test get_faked_stage_packages"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["foo"] = {"bar": "auto"}
        m = {}
        m["name"] = "foo"
        m["version"] = "1.2-3ubuntu0.4+gitdeadbeef"
        m["parts"] = {"foo-part": {}}

        res = store.get_faked_build_and_stage_packages(m)
        self.assertTrue("faked-by-review-tools" in res["parts"])
        self.assertTrue("stage-packages" in res["parts"]["faked-by-review-tools"])
        self.assertTrue(
            "bar=1.2-3ubuntu0.4"
            in res["parts"]["faked-by-review-tools"]["stage-packages"]
        )

    def test_get_faked_stage_packages_with_primed_stage_auto_(self):
        """Test get_faked_stage_packages, primed-stage exists"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["foo"] = {"bar": "auto"}
        m = {}
        m["name"] = "foo"
        m["version"] = "1.2-3ubuntu0.4+gitdeadbeef"
        m["parts"] = {"foo-part": {}}
        m["primed-stage-packages"] = ["libxcursor1=1:1.1.14-1"]

        res = store.get_faked_build_and_stage_packages(m)
        self.assertTrue("faked-by-review-tools" in res["parts"])
        self.assertTrue("bar=1.2-3ubuntu0.4" in res["primed-stage-packages"])
        self.assertTrue("libxcursor1=1:1.1.14-1" in res["primed-stage-packages"])

    def test_get_faked_stage_packages_auto_kernel(self):
        """Test get_faked_stage_packages"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["foo"] = {"linux-image-generic": "auto-kernel"}
        m = {}
        m["name"] = "foo"
        m["version"] = "4.4.0-140.141"
        m["parts"] = {"foo-part": {}}

        res = store.get_faked_build_and_stage_packages(m)
        self.assertTrue("faked-by-review-tools" in res["parts"])
        self.assertTrue("stage-packages" in res["parts"]["faked-by-review-tools"])
        self.assertTrue(
            "linux-image-generic=4.4.0.140.999999"
            in res["parts"]["faked-by-review-tools"]["stage-packages"]
        )

    def test_get_faked_stage_packages_with_primed_stage_auto_kernel(self):
        """Test get_faked_stage_packages primed-stage exists"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["foo"] = {"linux-image-generic": "auto-kernel"}
        m = {}
        m["name"] = "foo"
        m["version"] = "4.4.0-140.141"
        m["parts"] = {"foo-part": {}}

        m["primed-stage-packages"] = ["libxcursor1=1:1.1.14-1"]

        res = store.get_faked_build_and_stage_packages(m)
        self.assertTrue("faked-by-review-tools" in res["parts"])
        self.assertTrue(
            "linux-image-generic=4.4.0.140.999999" in res["primed-stage-packages"]
        )
        self.assertTrue("libxcursor1=1:1.1.14-1" in res["primed-stage-packages"])

    def test_get_faked_stage_packages_base_override(self):
        """Test get_faked_stage_packages - base override"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["foo"] = {"bar": "1.2~"}
        update_stage_packages["foo/core18"] = {"bar": "2.0"}
        m = {}
        m["name"] = "foo"
        m["base"] = "core18"
        m["version"] = "1.2~"
        m["parts"] = {"foo-part": {}}

        res = store.get_faked_build_and_stage_packages(m)
        self.assertTrue("faked-by-review-tools" in res["parts"])
        self.assertTrue("stage-packages" in res["parts"]["faked-by-review-tools"])
        self.assertTrue(
            "bar=2.0" in res["parts"]["faked-by-review-tools"]["stage-packages"]
        )

    def test_get_faked_stage_packages_with_primed_stage_base_override(self):
        """Test get_faked_stage_packages - base override, primed-stage exists"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["foo"] = {"bar": "1.2~"}
        update_stage_packages["foo/core18"] = {"bar": "2.0"}
        m = {}
        m["name"] = "foo"
        m["base"] = "core18"
        m["version"] = "1.2~"
        m["parts"] = {"foo-part": {}}
        m["primed-stage-packages"] = ["libxcursor1=1:1.1.14-1"]

        res = store.get_faked_build_and_stage_packages(m)
        self.assertTrue("faked-by-review-tools" in res["parts"])
        self.assertTrue("bar=2.0" in res["primed-stage-packages"])
        self.assertTrue("libxcursor1=1:1.1.14-1" in res["primed-stage-packages"])

    def test_get_faked_stage_packages_base_fallback(self):
        """Test get_faked_stage_packages - base fallback"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["foo"] = {"bar": "1.2~"}
        m = {}
        m["name"] = "foo"
        m["base"] = "core18"
        m["version"] = "1.2~"
        m["parts"] = {"foo-part": {}}

        res = store.get_faked_build_and_stage_packages(m)
        self.assertTrue("faked-by-review-tools" in res["parts"])
        self.assertTrue("stage-packages" in res["parts"]["faked-by-review-tools"])
        self.assertTrue(
            "bar=1.2~" in res["parts"]["faked-by-review-tools"]["stage-packages"]
        )

    def test_get_faked_stage_packages_base_fallback_with_primed_stage(self):
        """Test get_faked_stage_packages - base fallback"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["foo"] = {"bar": "1.2~"}
        m = {}
        m["name"] = "foo"
        m["base"] = "core18"
        m["version"] = "1.2~"
        m["parts"] = {"foo-part": {}}
        m["primed-stage-packages"] = ["libxcursor1=1:1.1.14-1"]

        res = store.get_faked_build_and_stage_packages(m)
        self.assertTrue("faked-by-review-tools" in res["parts"])
        self.assertTrue("bar=1.2~" in res["primed-stage-packages"])
        self.assertTrue("libxcursor1=1:1.1.14-1" in res["primed-stage-packages"])

    def test_get_faked_build_packages_has_no_side_effect_on_original_manifest(self,):
        """Test get_faked_stage_packages - no side effect on m"""
        from reviewtools.overrides import update_build_packages

        update_build_packages["foo"] = {"bar": "1.2~"}
        m = {}
        m["name"] = "foo"
        m["version"] = "1.2~"
        m["parts"] = {"foo-part": {}}
        m["snapcraft-version"] = "1.1.1"

        res = store.get_faked_build_and_stage_packages(m)
        self.assertTrue("faked-by-review-tools" in res["parts"])
        self.assertTrue("stage-packages" in res["parts"]["faked-by-review-tools"])
        self.assertEqual(
            len(res["parts"]["faked-by-review-tools"]["stage-packages"]), 0
        )
        self.assertEqual(
            len(res["parts"]["faked-by-review-tools"]["build-packages"]), 1
        )
        self.assertTrue(
            "snapcraft=1.1.1" in res["parts"]["faked-by-review-tools"]["build-packages"]
        )
        self.assertFalse(
            "bar=1.2~" in res["parts"]["faked-by-review-tools"]["build-packages"]
        )
        self.assertFalse("faked-by-review-tools" in m["parts"])

    def test_check_get_package_revisions_empty_manifest(self):
        """Test get_package_revisions() - empty manifest"""
        self.store_db = read_file_as_json_dict("./tests/test-store-unittest-bare.db")
        errors = {}
        res = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEqual(len(errors), 0)

        self.assertTrue("revisions" in res)
        self.assertEqual(len(res["revisions"]), 0)

    def test_get_snapcraft_version_from_manifest(self,):
        """Test get_snapcraft_version_from_manifest()"""
        m = {}
        snapcraft_version_values = {
            "invalid": ["not_present", None, ""],
            "valid": ["1", "1.1"],
        }
        for snapcraft_versions in snapcraft_version_values:
            if snapcraft_versions == "invalid":
                for invalid_version in snapcraft_version_values[snapcraft_versions]:
                    if invalid_version != "not_present":
                        m["snapcraft-version"] = invalid_version
                    else:
                        if "snapcraft-version" in m:
                            del m["snapcraft-version"]
                    self.assertEqual(store.get_snapcraft_version_from_manifest(m), None)
            else:
                for valid_version in snapcraft_version_values[snapcraft_versions]:
                    m["snapcraft-version"] = valid_version
                    self.assertEqual(
                        store.get_snapcraft_version_from_manifest(m), valid_version
                    )
