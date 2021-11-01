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
        self.secnot_stage_and_build_pkgs_db = usn.read_usn_db(
            "./tests/test-usn-unittest-build-pkgs.db"
        )

        self.store_db = read_file_as_json_dict("./tests/test-store-unittest-1.db")
        self.rock_store_db = read_file_as_json_dict(
            "./tests/test-rocks-store-unittest-1.db"
        )

        self.first_revision = 0
        self.first_revision_with_primed_stage = 4
        self.first_revision_with_installed_snap = 6
        # make sure primed-stage-packages section is present on
        # first_revision_with_primed_stage revision. Adding this assertion
        # here means we end up checking that in each test. Still, it is a
        # cheap test and means all the tests don't need to worry about using
        # primed-stage-packages with self.first_revision_with_primed_stage
        self.assertIn(
            "primed-stage-packages",
            self.store_db[0]["revisions"][self.first_revision_with_primed_stage][
                "manifest_yaml"
            ],
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
        self.rock_manifest_basic = {
            "manifest-version": "1",
            "name": "foo",
            "os-release-id": "ubuntu",
            "os-release-version-id": "20.04",
            "architectures": ["amd64"],
            "stage-packages": ["libbar=1.2,libbar=1.2", "libbaz=3.4,libbar=1.2"],
        }

    def test_check_get_package_revisions_empty(self):
        """Test get_package_revisions() - empty item - snaps and rocks"""

        pkg_types = ["snap", "rock"]
        for pkg_type in pkg_types:
            with self.subTest(pkg_type):
                with self.assertRaises(ValueError) as e:
                    store.get_pkg_revisions({}, self.secnot_db, {}, pkg_type)
                self.assertEqual(str(e.exception), "required field 'name' not found")

    def test_check_get_package_revisions_valid(self):
        """Test get_package_revisions() - valid snap and valid rock"""
        errors = {}
        store_dbs = {
            "snap": [
                self.store_db,
                "0ad",
                "olivier.tilloy@canonical.com",
                "12",
                "stable",
                "i386",
                "libxcursor1",
                "3501-1",
            ],
            "rock": [
                self.rock_store_db,
                "redis",
                "rocks@canonical.com",
                "852f7702e973",
                "beta",
                "amd64",
                "libxcursor1",
                "3501-1",
            ],
        }
        for store_type, store_metadata in store_dbs.items():
            (
                store_db,
                name,
                publisher,
                revision,
                channel,
                architecture,
                pkg_name,
                usn,
            ) = store_metadata
            with self.subTest(
                store_db=store_db,
                name=name,
                publisher=publisher,
                revision=revision,
                channel=channel,
                architecture=architecture,
                pkg_name=pkg_name,
                usn=usn,
            ):
                item = store_db[0]
                res = store.get_pkg_revisions(item, self.secnot_db, errors, store_type)
                self.assertEqual(len(errors), 0)

                # verify the structure is what we expect
                for key in (
                    "name",
                    "publisher",
                    "uploaders",
                    "additional",
                    "revisions",
                ):
                    self.assertIn(key, res)

                self.assertIn(revision, res["revisions"])

                self.assertEqual(res["name"], name)
                self.assertEqual(res["publisher"], publisher)

                self.assertIsInstance(res["uploaders"], list)
                self.assertIsInstance(res["additional"], list)
                self.assertEqual(len(res["uploaders"]), 0)
                self.assertEqual(len(res["additional"]), 0)

                target_rev = res["revisions"][revision]
                for key in ("channels", "architectures", "secnot-report"):
                    self.assertIn(key, target_rev)

                self.assertIn(channel, target_rev["channels"])
                self.assertIn(architecture, target_rev["architectures"])

                secnot_report = target_rev["secnot-report"]
                self.assertNotIn("build", secnot_report)
                self.assertIn("staged", secnot_report)

                staged = secnot_report["staged"]
                self.assertIn(pkg_name, staged)
                self.assertIn(usn, staged[pkg_name])

    def test_check_get_package_revisions_valid_with_type(self):
        """Test get_package_revisions() - valid (snap and rock type)"""
        store_dbs = {
            "snap": [self.store_db, "12", "app", self.first_revision],
            "rock": [self.rock_store_db, "852f7702e973", "oci", 0],
        }
        errors = {}
        for store_type, store_metadata in store_dbs.items():
            (store_db, revision, type, revision_index) = store_metadata
            with self.subTest(
                store_db=store_db,
                revision=revision,
                type=type,
                revision_index=revision_index,
            ):
                item = store_db[0]
                m = (
                    item["revisions"][self.first_revision]["manifest_yaml"]
                    + "\ntype: "
                    + type
                )
                item["revisions"][revision_index]["manifest_yaml"] = m
                res = store.get_pkg_revisions(item, self.secnot_db, errors, store_type)
                self.assertEqual(len(errors), 0)
                sec_not_report = res["revisions"][revision]["secnot-report"]
                self.assertIn("staged", sec_not_report)
                self.assertNotIn("build", sec_not_report)
                self.assertIn("3501-1", sec_not_report["staged"]["libxcursor1"])

    def test_check_get_package_revisions_missing_publisher(self):
        """Test get_package_revisions() - missing publisher"""
        store_dbs = {
            "snap": [self.store_db, "0ad"],
            "rock": [self.rock_store_db, "redis"],
        }
        for store_type, store_metadata in store_dbs.items():
            (store_db, pkg_name,) = store_metadata
            with self.subTest(store_db=store_db, pkg_name=pkg_name):
                item = store_db[0]
                item["publisher_email"] = ""
                errors = {}
                store.get_pkg_revisions(item, self.secnot_db, errors, store_type)
                self.assertEqual(len(errors), 1)
                self.assertEqual(errors[pkg_name][0], "publisher_email '' invalid")

    def test_check_get_package_revisions_missing_revision(self):
        """Test get_package_revisions() - missing revision"""
        store_dbs = {
            "snap": [self.store_db, "0ad", self.first_revision],
            "rock": [self.rock_store_db, "redis", 0],
        }
        for store_type, store_metadata in store_dbs.items():
            (store_db, pkg_name, revision_index,) = store_metadata
            with self.subTest(
                store_db=store_db, pkg_name=pkg_name, revision_index=revision_index,
            ):
                item = store_db[0]
                del item["revisions"][revision_index]["revision"]
                errors = {}
                store.get_pkg_revisions(item, self.secnot_db, errors, store_type)
                self.assertEqual(len(errors), 1)
                self.assertEqual(errors[pkg_name][0], "no revisions found")

    def test_check_get_package_revisions_missing_manifest(self):
        """Test get_package_revisions() - missing manifest"""
        store_dbs = {
            "snap": [self.store_db, "0ad", self.first_revision, "'12'"],
            "rock": [self.rock_store_db, "redis", 0, "'852f7702e973'"],
        }
        for store_type, store_metadata in store_dbs.items():
            (store_db, pkg_name, revision_index, revision) = store_metadata
            with self.subTest(
                store_db=store_db,
                pkg_name=pkg_name,
                revision_index=revision_index,
                revision=revision,
            ):
                item = store_db[0]
                del item["revisions"][revision_index]["manifest_yaml"]
                errors = {}
                store.get_pkg_revisions(item, self.secnot_db, errors, store_type)
                self.assertEqual(len(errors), 1)
                self.assertEqual(
                    errors[pkg_name][0],
                    "manifest_yaml missing for revision " + revision,
                )

    def test_check_get_package_revisions_bad_manifest(self):
        """Test get_package_revisions() - bad manifest"""
        store_dbs = {
            "snap": [self.store_db, "0ad", self.first_revision, "'12'"],
            "rock": [self.rock_store_db, "redis", 0, "'852f7702e973'"],
        }
        for store_type, store_metadata in store_dbs.items():
            (store_db, pkg_name, revision_index, revision) = store_metadata
            with self.subTest(
                store_db=store_db,
                pkg_name=pkg_name,
                revision_index=revision_index,
                revision=revision,
            ):
                item = store_db[0]
                item["revisions"][revision_index]["manifest_yaml"] = "{"
                errors = {}
                store.get_pkg_revisions(item, self.secnot_db, errors, store_type)
                self.assertEqual(len(errors), 1)
                self.assertTrue(
                    errors[pkg_name][0].startswith(
                        "error loading manifest for revision " + revision + ":"
                    )
                )

    def test_check_get_package_revisions_bad_secnot(self):
        """Test get_package_revisions() - bad secnot db"""
        store_dbs = {
            "snap": self.store_db,
            "rock": self.rock_store_db,
        }
        for store_type, store_db in store_dbs.items():
            with self.subTest():
                item = store_db[0]
                self.secnot_db = "bad"
                errors = {}
                pkg_db = store.get_pkg_revisions(
                    item, self.secnot_db, errors, store_type
                )
                self.assertEqual(len(errors), 0)
                self.assertEqual(len(pkg_db["revisions"]), 0)

    def test_check_get_package_revisions_empty_uploader(self):
        """Test get_package_revisions() - empty uploader"""
        store_dbs = {
            "snap": [self.store_db, "0ad", self.first_revision],
            "rock": [self.rock_store_db, "redis", 0],
        }
        for store_type, store_metadata in store_dbs.items():
            (store_db, pkg_name, revision_index,) = store_metadata
            with self.subTest(
                store_db=store_db, pkg_name=pkg_name, revision_index=revision_index,
            ):
                item = store_db[0]
                item["revisions"][revision_index]["uploader_email"] = ""
                errors = {}
                store.get_pkg_revisions(item, self.secnot_db, errors, store_type)
                self.assertEqual(len(errors), 1)
                self.assertEqual(errors[pkg_name][0], "uploader_email '' invalid")

    def test_check_get_package_revisions_has_uploader(self):
        """Test get_package_revisions() - has uploader"""
        store_dbs = {
            "snap": [self.store_db, self.first_revision],
            "rock": [self.rock_store_db, 0],
        }
        for store_type, store_metadata in store_dbs.items():
            (store_db, revision_index,) = store_metadata
            with self.subTest(
                store_db=store_db, revision_index=revision_index,
            ):
                item = store_db[0]
                item["revisions"][revision_index]["uploader_email"] = "test@example.com"
                errors = {}
                res = store.get_pkg_revisions(item, self.secnot_db, errors, store_type)
                self.assertEqual(len(errors), 0)
                self.assertIn("uploaders", res)
                self.assertIsInstance(res["uploaders"], list)
                self.assertEqual(len(res["uploaders"]), 1)
                self.assertEqual(res["uploaders"][0], "test@example.com")

    def test_check_get_package_revisions_empty_collaborator(self):
        """Test get_package_revisions() - empty collaborator"""
        store_dbs = {
            "snap": [self.store_db, "0ad"],
            "rock": [self.rock_store_db, "redis"],
        }
        for store_type, store_metadata in store_dbs.items():
            (store_db, pkg_name,) = store_metadata
            with self.subTest(
                store_db=store_db, pkg_name=pkg_name,
            ):
                item = store_db[0]
                item["collaborators"] = [{"email": ""}]
                errors = {}
                store.get_pkg_revisions(item, self.secnot_db, errors, store_type)
                self.assertEqual(len(errors), 1)
                self.assertEqual(errors[pkg_name][0], "collaborator email '' invalid")

    def test_check_get_package_revisions_malformed_collaborator(self):
        """Test get_package_revisions() - malformed collaborator"""
        store_dbs = {
            "snap": self.store_db,
            "rock": self.rock_store_db,
        }
        for store_type, store_db in store_dbs.items():
            with self.subTest():
                item = store_db[0]
                item["collaborators"] = ["test@example.com"]
                errors = {}
                res = store.get_pkg_revisions(item, self.secnot_db, errors, store_type)
                self.assertEqual(len(errors), 0)
                self.assertIsInstance(res["collaborators"], list)
                self.assertEqual(len(res["collaborators"]), 0)

    def test_check_get_package_revisions_has_collaborator(self):
        """Test get_package_revisions() - has has collaborator"""
        store_dbs = {
            "snap": self.store_db,
            "rock": self.rock_store_db,
        }
        for store_type, store_db in store_dbs.items():
            with self.subTest():
                item = store_db[0]
                item["collaborators"] = [
                    {"email": "test@example.com", "name": "Test Me"}
                ]
                errors = {}
                res = store.get_pkg_revisions(item, self.secnot_db, errors, store_type)
                self.assertEqual(len(errors), 0)
                self.assertIsInstance(res["collaborators"], list)
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
        errors = {}
        pkg_db = store.get_pkg_revisions(
            self.store_db[0], self.secnot_stage_and_build_pkgs_db, errors
        )
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

    def test_check_get_package_revisions_rock_stage_packages_is_none(self,):
        """Test get_package_revisions() - rock stage-packages is None has no
           security notices
        """
        for i in range(len(self.rock_store_db[0]["revisions"])):
            m = yaml.load(
                self.rock_store_db[0]["revisions"][i]["manifest_yaml"],
                Loader=yaml.SafeLoader,
            )
            m["stage-packages"] = None
            self.rock_store_db[0]["revisions"][i]["manifest_yaml"] = yaml.dump(m)
        errors = {}
        pkg_db = store.get_pkg_revisions(
            self.rock_store_db[0], self.secnot_db, errors, "rock"
        )
        # empty stage-packages has no security notices
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
        errors = {}
        pkg_db = store.get_pkg_revisions(
            self.store_db[0], self.secnot_stage_and_build_pkgs_db, errors
        )
        for rev in pkg_db["revisions"]:
            self.assertNotIn("stage-packages", rev)
            self.assertEqual(len(pkg_db["revisions"][rev]["secnot-report"]["build"]), 1)
            self.assertIn(
                "snapcraft", pkg_db["revisions"][rev]["secnot-report"]["build"]
            )
            self.assertIn(
                "5501-1",
                pkg_db["revisions"][rev]["secnot-report"]["build"]["snapcraft"],
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
            errors = {}
            pkg_db = store.get_pkg_revisions(
                self.store_db[0], self.secnot_stage_and_build_pkgs_db, errors
            )
            # empty parts/stage-packages has no security notices
            # usn for build-packages does not apply
            for rev in pkg_db["revisions"]:
                self.assertEqual(len(pkg_db["revisions"][rev]["secnot-report"]), 0)

    def test_check_get_package_revisions_pkg_override(self):
        """Test get_package_revisions() - pkg override"""
        # update the overrides for this snap and this rock
        from reviewtools.overrides import update_publisher_overrides

        store_dbs = {
            "snap": [self.store_db, "0ad"],
            "rock": [self.rock_store_db, "redis"],
        }
        for store_type, store_metadata in store_dbs.items():
            (store_db, pkg_name,) = store_metadata
            with self.subTest(
                store_db=store_db, pkg_name=pkg_name,
            ):
                item = store_db[0]
                update_publisher_overrides["rt-tests@example.com"] = {}
                update_publisher_overrides["rt-tests@example.com"][pkg_name] = [
                    "over@example.com"
                ]
                item["publisher_email"] = "rt-tests@example.com"
                errors = {}
                res = store.get_pkg_revisions(item, self.secnot_db, errors, store_type)
                self.assertEqual(len(errors), 0)
                self.assertIn("additional", res)
                self.assertIsInstance(res["additional"], list)
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
        self.assertIsInstance(res, dict)
        self.assertEqual(len(res), 1)
        self.assertIn("rt-tests@example.com", res)
        self.assertEqual(len(res["rt-tests@example.com"]), 1)
        self.assertEqual(res["rt-tests@example.com"][0], "0ad")

    def test_check_get_shared_snap_without_override_missing_publisher(self):
        """Test get_shared_snap_without_override() - missing publisher"""
        del self.store_db[0]["publisher_email"]
        res = store.get_shared_snap_without_override(self.store_db)
        self.assertIsInstance(res, dict)
        self.assertEqual(len(res), 0)

    def test_check_get_shared_snap_without_override_not_present(self):
        """Test get_shared_snap_without_override() - not present"""
        res = store.get_shared_snap_without_override(self.store_db)
        self.assertIsInstance(res, dict)
        self.assertEqual(len(res), 0)

    def test_check_normalize_and_verify_snap_manifest(self):
        """Test normalize_and_verify_snap_manifest()"""
        for r in self.store_db[0]["revisions"]:
            m = yaml.load(r["manifest_yaml"], Loader=yaml.SafeLoader)
            store.normalize_and_verify_snap_manifest(m)

    def test_check_normalize_and_verify_rock_manifest(self):
        """Test normalize_and_verify_rock_manifest()"""
        for r in self.rock_store_db[0]["revisions"]:
            m = yaml.load(r["manifest_yaml"], Loader=yaml.SafeLoader)
            store.normalize_and_verify_rock_manifest(m)

    def test_check_normalize_and_verify_snap_manifest_bad(self):
        """Test normalize_and_verify_snap_manifest()"""
        try:
            store.normalize_and_verify_snap_manifest([])
        except ValueError:
            return

        raise Exception("Should have raised ValueError")  # pragma: nocover

    def test_check_normalize_and_verify_rock_manifest_bad(self):
        """Test normalize_and_verify_rock_manifest()"""
        with self.assertRaises(ValueError):
            store.normalize_and_verify_rock_manifest([])

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
            self.assertIsInstance(res, dict)
            self.assertTrue(len(res) > 0)
            self.assertIn("staged", res)
            staged_packages = res["staged"]
            self.assertIn("libxcursor1", staged_packages)
            self.assertIn("1:1.1.14-1", staged_packages["libxcursor1"])
            self.assertNotIn("build", res)

    def test_check_get_staged_packages_from_rock_manifest(self):
        """Test get_staged_packages_from_rock_manifest()"""
        m = yaml.load(
            self.rock_store_db[0]["revisions"][0]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )

        res = store.get_staged_packages_from_rock_manifest(m)
        self.assertIsInstance(res, dict)
        self.assertTrue(len(res) > 0)
        self.assertIn("staged", res)
        expected_stage_packages = {
            "adduser": "3.118ubuntu2",
            "apt": "2.0.2ubuntu0.2",
            "bsdutils": "1:2.34-0.1ubuntu9.1",
            "libxcursor1": "1.0.0-2ubuntu1",
            "libcurl4": "7.74.0-1ubuntu2.1",
        }
        for pkg_name in expected_stage_packages:
            self.assertIn(pkg_name, res["staged"])
            self.assertIn(expected_stage_packages[pkg_name], res["staged"][pkg_name])
        self.assertNotIn("build", res)

    def test_check_get_staged_packages_from_manifest_with_primed_stage_packages(self):
        """Test get_staged_packages_from_manifest(), primed-stage exists"""
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision_with_primed_stage][
                "manifest_yaml"
            ],
            Loader=yaml.SafeLoader,
        )
        res = store.get_staged_and_build_packages_from_manifest(m)
        self.assertIsInstance(res, dict)
        self.assertTrue(len(res) > 0)
        self.assertIn("staged", res)
        staged_packages = res["staged"]
        self.assertIn("libxcursor1", staged_packages)
        self.assertIn("1:1.1.14-1", staged_packages["libxcursor1"])
        self.assertNotIn("build", res)

    def test_check_get_staged_packages_from_manifest_missing_parts(self):
        """Test get_staged_packages_from_manifest() - missing parts"""
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        del m["parts"]

        res = store.get_staged_and_build_packages_from_manifest(m)
        self.assertIs(res, None)

    def test_check_get_staged_packages_from_rock_manifest_missing_stage_packages(self):
        """Test get_staged_packages_from_rock_manifest() - missing stage-packages"""
        m = yaml.load(
            self.rock_store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        del m["stage-packages"]

        res = store.get_staged_packages_from_rock_manifest(m)
        self.assertIs(res, None)

    def test_check_get_staged_packages_from_rock_manifest_empty_stage_packages(self):
        """Test get_staged_packages_from_rock_manifest() - empty
           stage-packages
        """
        m = yaml.load(
            self.rock_store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        m["stage-packages"] = []

        res = store.get_staged_packages_from_rock_manifest(m)
        self.assertIs(res, None)

    def test_check_get_staged_packages_from_rock_manifest_bad_stage_packages(self):
        """Test get_staged_packages_from_rock_manifest() - bad stage-packages"""
        m = yaml.load(
            self.rock_store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        m["stage-packages"].append("foo")

        res = store.get_staged_packages_from_rock_manifest(m)
        self.assertIsInstance(res, dict)
        self.assertTrue(len(res) > 0)
        self.assertIn("staged", res)
        staged_packages = res["staged"]
        self.assertNotIn("foo", staged_packages)
        self.assertIn("libxcursor1", staged_packages)
        self.assertIn("1.0.0-2ubuntu1", staged_packages["libxcursor1"])
        self.assertNotIn("build", res)

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
        self.assertIsInstance(res, dict)
        self.assertTrue(len(res) > 0)
        self.assertIn("staged", res)
        staged_packages = res["staged"]
        self.assertNotIn("foo", staged_packages)
        self.assertIn("libxcursor1", staged_packages)
        self.assertIn("1:1.1.14-1", staged_packages["libxcursor1"])
        self.assertNotIn("build", res)

    def test_check_get_staged_packages_from_manifest_bad_primed_staged(self,):
        """Test get_staged_packages_from_manifest() - only one
           bad package in primed-stage returns None"""
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        m["primed-stage-packages"] = ["foo"]

        res = store.get_staged_and_build_packages_from_manifest(m)
        self.assertIs(res, None)

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
        self.assertIsInstance(res, dict)
        self.assertTrue(len(res) > 0)
        self.assertNotIn("foo", res)
        self.assertIn("staged", res)
        staged_packages = res["staged"]
        self.assertIn("libxcursor1", staged_packages)
        self.assertIn("1:1.1.14-1", staged_packages["libxcursor1"])
        self.assertNotIn("build", res)

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
        self.assertIs(res, None)

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
        self.assertIs(res, None)

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
        self.assertIs(res, None)

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
        self.assertIs(res, None)

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
        self.assertIsInstance(res, dict)
        self.assertTrue(len(res) > 0)
        self.assertIn("staged", res)
        staged_packages = res["staged"]
        self.assertIn("libxcursor1", staged_packages)
        self.assertIn("1:1.1.14-1", staged_packages["libxcursor1"])
        # make sure the ignored package is not present
        self.assertNotIn("linux-libc-dev", staged_packages)
        self.assertNotIn("build", res)

    def test_check_get_staged_packages_from_rock_manifest_binary_ignored(self,):
        """Test get_staged_packages_from_rock_manifest() - binary ignored"""
        m = yaml.load(
            self.rock_store_db[0]["revisions"][self.first_revision]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        m["stage-packages"].append("linux-libc-dev=4.4.0-104.127,linux=4.4.0-104.127")

        res = store.get_staged_packages_from_rock_manifest(m)
        self.assertIsInstance(res, dict)
        self.assertTrue(len(res) > 0)
        self.assertIn("staged", res)
        staged_packages = res["staged"]
        self.assertIn("libxcursor1", staged_packages)
        self.assertIn("1.0.0-2ubuntu1", staged_packages["libxcursor1"])
        # make sure the ignored package is not present
        self.assertNotIn("linux-libc-dev", staged_packages)
        self.assertNotIn("build", res)

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
        self.assertIsInstance(res, dict)
        self.assertTrue(len(res) > 0)
        self.assertIn("staged", res)
        staged_packages = res["staged"]
        self.assertIn("libxcursor1", staged_packages)
        self.assertIn("1:1.1.14-1", staged_packages["libxcursor1"])
        # make sure the ignored package is not present
        self.assertNotIn("linux-libc-dev", res)
        self.assertNotIn("build", res)

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
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_stage_and_build_pkgs_db
                    )
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)

                self.assertIsInstance(res, dict)
                if build_packages and sec_not_for_build_packages:
                    self.assertIn("build", res)
                    res_build_packages = res["build"]
                    self.assertEqual(len(res_build_packages), 1)
                    self.assertIn("snapcraft", res_build_packages)
                    self.assertEqual(len(res_build_packages["snapcraft"]), 1)
                    self.assertIn("5501-1", res_build_packages["snapcraft"])
                    self.assertEqual(len(res), 2)
                else:
                    self.assertNotIn("build", res)
                    self.assertEqual(len(res), 1)

                self.assertIn("staged", res)
                staged_packages = res["staged"]
                self.assertEqual(len(staged_packages), 2)
                self.assertIn("libxcursor1", staged_packages)
                self.assertEqual(len(staged_packages["libxcursor1"]), 1)
                self.assertEqual(staged_packages["libxcursor1"][0], "3501-1")
                self.assertIn("libtiff5", staged_packages)
                self.assertEqual(len(staged_packages["libtiff5"]), 2)
                self.assertIn("3602-1", staged_packages["libtiff5"])
                self.assertIn("3606-1", staged_packages["libtiff5"])

    def test_check_get_secnots_for_rock_manifest(self):
        """Test get_secnots_for_manifest()"""
        with_cves = [True, False]

        for run_with_cves in with_cves:
            with self.subTest():
                m = yaml.load(
                    self.rock_store_db[0]["revisions"][0]["manifest_yaml"],
                    Loader=yaml.SafeLoader,
                )
                res = store.get_secnots_for_manifest(
                    m, self.secnot_db, run_with_cves, "rock"
                )
                self.assertIsInstance(res, dict)
                self.assertNotIn("build", res)
                self.assertEqual(len(res), 1)
                self.assertIn("staged", res)
                staged_packages = res["staged"]
                self.assertEqual(len(staged_packages), 1)
                self.assertIn("libxcursor1", staged_packages)
                self.assertEqual(len(staged_packages["libxcursor1"]), 1)
                if run_with_cves:
                    self.assertIsInstance(
                        staged_packages["libxcursor1"]["3501-1"], list
                    )
                    self.assertEqual(len(staged_packages["libxcursor1"]["3501-1"]), 1)
                    self.assertIn(
                        "CVE-2017-16612", staged_packages["libxcursor1"]["3501-1"]
                    )
                else:
                    self.assertEqual(staged_packages["libxcursor1"][0], "3501-1")

    def test_check_get_secnots_for_rock_manifest_empty_staged(self):
        """Test get_secnots_for_manifest()"""
        with_cves = [True, False]

        for run_with_cves in with_cves:
            with self.subTest():
                m = yaml.load(
                    self.rock_store_db[0]["revisions"][0]["manifest_yaml"],
                    Loader=yaml.SafeLoader,
                )
                m["stage-packages"] = []
                res = store.get_secnots_for_manifest(
                    m, self.secnot_db, run_with_cves, "rock"
                )
                self.assertIsInstance(res, dict)
                self.assertNotIn("build", res)
                self.assertEqual(len(res), 0)
                self.assertNotIn("staged", res)

    def test_check_get_secnots_for_manifest_with_empty_primed_stage_list(self):
        """Test get_secnots_for_manifest() - primed-stage-packages empty"""
        has_build_packages = [True, False]
        secnots_dbs = [
            (self.secnot_stage_and_build_pkgs_db, True),
            (self.secnot_db, False),
        ]
        primed_stage_packages_values = [
            ([], False, 0, 1),
            (None, True, 1, 2),
            ("keep_original", True, 1, 2),
        ]

        for build_packages in has_build_packages:
            for secnot_db, has_secnot_for_build_packages, in secnots_dbs:
                for (
                    primed_stage_packages_value,
                    should_show_staged_packages,
                    res_length_with_staged,
                    res_length_with_staged_and_build,
                ) in primed_stage_packages_values:
                    m = yaml.load(
                        self.store_db[0]["revisions"][
                            self.first_revision_with_primed_stage
                        ]["manifest_yaml"],
                        Loader=yaml.SafeLoader,
                    )
                    if primed_stage_packages_value != "keep_original":
                        m["primed-stage-packages"] = primed_stage_packages_value
                    if build_packages:
                        # Adding faked-by-review-tools part
                        m["parts"]["faked-by-review-tools"] = {}
                        m["parts"]["faked-by-review-tools"]["build-packages"] = [
                            "snapcraft=1.1"
                        ]
                    res = store.get_secnots_for_manifest(m, secnot_db)
                    self.assertIsInstance(res, dict)
                    if build_packages and has_secnot_for_build_packages:
                        self.assertIn("build", res)
                        res_build_packages = res["build"]
                        self.assertEqual(len(res_build_packages), 1)
                        self.assertIn("snapcraft", res_build_packages)
                        self.assertEqual(len(res_build_packages["snapcraft"]), 1)
                        self.assertIn("5501-1", res_build_packages["snapcraft"])
                        self.assertEqual(len(res), res_length_with_staged_and_build)
                    else:
                        self.assertNotIn("build", res)
                        self.assertEqual(len(res), res_length_with_staged)

                    if should_show_staged_packages:
                        self.assertIn("staged", res)
                        staged_packages = res["staged"]
                        self.assertEqual(len(staged_packages), 2)
                        self.assertIn("libxcursor1", staged_packages)
                        self.assertEqual(len(staged_packages["libxcursor1"]), 1)
                        self.assertEqual(staged_packages["libxcursor1"][0], "3501-1")
                        self.assertIn("libtiff5", staged_packages)
                        self.assertEqual(len(staged_packages["libtiff5"]), 2)
                        self.assertIn("3602-1", staged_packages["libtiff5"])
                        self.assertIn("3606-1", staged_packages["libtiff5"])
                    else:
                        self.assertNotIn("stage-packages", res)

    def test_check_get_secnots_for_manifest_with_version_override_no_update(self,):
        """Test get_secnots_for_manifest() primed-stage-packages same as
           staged-packages and USN version override, snap updated"""

        from reviewtools.overrides import update_package_version

        update_package_version["libtiff5"] = {"stage-packages": "3.5"}
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision_with_installed_snap][
                "manifest_yaml"
            ],
            Loader=yaml.SafeLoader,
        )
        res = store.get_secnots_for_manifest(m, self.secnot_db)
        self.assertIsInstance(res, dict)

        self.assertNotIn("build", res)
        self.assertEqual(len(res), 1)

        self.assertIsInstance(res, dict)
        self.assertIn("staged", res)
        staged_packages = res["staged"]
        self.assertEqual(len(staged_packages), 1)
        self.assertIn("libxcursor1", staged_packages)
        self.assertEqual(len(staged_packages["libxcursor1"]), 1)
        self.assertEqual(staged_packages["libxcursor1"][0], "3501-1")

        # Since the override includes a version smaller than the one in the USN
        # libtiff5 should not be part of res
        self.assertNotIn("libtiff5", staged_packages)

    def test_check_get_secnots_for_manifest_with_version_override_update(self,):
        """Test get_secnots_for_manifest() primed-stage-packages same as
           staged-packages and USN version override, needs update"""

        from reviewtools.overrides import update_package_version

        update_package_version["libtiff5"] = {"build-packages": "8.5"}
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision_with_installed_snap][
                "manifest_yaml"
            ],
            Loader=yaml.SafeLoader,
        )

        for part in m["parts"]:
            # Valid format for entry should consider the override
            m["parts"][part]["build-packages"] = ["libtiff5=999"]

        res = store.get_secnots_for_manifest(m, self.secnot_db)
        self.assertIsInstance(res, dict)

        self.assertNotIn("build", res)
        self.assertEqual(len(res), 1)

        self.assertIn("staged", res)
        staged_packages = res["staged"]
        self.assertEqual(len(staged_packages), 2)
        self.assertIn("libxcursor1", staged_packages)
        self.assertEqual(len(staged_packages["libxcursor1"]), 1)
        self.assertEqual(staged_packages["libxcursor1"][0], "3501-1")
        self.assertIn("libtiff5", staged_packages)
        self.assertEqual(len(res["staged"]["libtiff5"]), 2)
        self.assertIn("3602-1", res["staged"]["libtiff5"])
        self.assertIn("3606-1", res["staged"]["libtiff5"])

    def test_check_get_secnots_for_manifest_with_version_override_invalid(self,):
        """Test get_secnots_for_manifest() primed-stage-packages same as
           staged-packages and USN version override"""

        from reviewtools.overrides import update_package_version

        update_package_version["libtiff5"] = {"build-packages": "3.5"}
        m = yaml.load(
            self.store_db[0]["revisions"][self.first_revision_with_installed_snap][
                "manifest_yaml"
            ],
            Loader=yaml.SafeLoader,
        )

        for part in m["parts"]:
            # Invalid format for entry should not consider the override
            m["parts"][part]["build-packages"] = ["libtiff5:111"]

        res = store.get_secnots_for_manifest(m, self.secnot_db)
        self.assertIsInstance(res, dict)

        self.assertNotIn("build", res)
        self.assertEqual(len(res), 1)

        self.assertIsInstance(res, dict)
        self.assertIn("staged", res)
        self.assertEqual(len(res["staged"]), 2)
        staged_packages = res["staged"]
        self.assertIn("libxcursor1", staged_packages)
        self.assertEqual(len(staged_packages["libxcursor1"]), 1)
        self.assertEqual(staged_packages["libxcursor1"][0], "3501-1")
        self.assertIn("libtiff5", staged_packages)
        self.assertEqual(len(staged_packages["libtiff5"]), 2)
        self.assertIn("3602-1", staged_packages["libtiff5"])
        self.assertIn("3606-1", staged_packages["libtiff5"])

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
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_stage_and_build_pkgs_db
                    )
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)
                self.assertIsInstance(res, dict)
                if build_packages and sec_not_for_build_packages:
                    self.assertIn("build", res)
                    res_build_packages = res["build"]
                    self.assertEqual(len(res_build_packages), 1)
                    self.assertIn("snapcraft", res_build_packages)
                    self.assertEqual(len(res_build_packages["snapcraft"]), 1)
                    self.assertIn("5501-1", res_build_packages["snapcraft"])
                    self.assertEqual(len(res), 2)
                else:
                    self.assertNotIn("build", res)
                    self.assertEqual(len(res), 1)

                self.assertIn("staged", res)
                staged_packages = res["staged"]
                self.assertIn("libtiff5", staged_packages)
                self.assertEqual(len(staged_packages["libtiff5"]), 2)
                self.assertIn("3602-1", staged_packages["libtiff5"])
                self.assertIn("3606-1", staged_packages["libtiff5"])
                # since it was removed from primed-stage-packages, we
                # shouldn't have a notice
                self.assertNotIn("libxcursor1", res)

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
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_stage_and_build_pkgs_db
                    )
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)
                self.assertIsInstance(res, dict)
                self.assertNotIn("staged", res)
                if build_packages and sec_not_for_build_packages:
                    self.assertIn("build", res)
                    res_build_packages = res["build"]
                    self.assertEqual(len(res_build_packages), 1)
                    self.assertIn("snapcraft", res_build_packages)
                    self.assertEqual(len(res_build_packages["snapcraft"]), 1)
                    self.assertIn("5501-1", res_build_packages["snapcraft"])
                    self.assertEqual(len(res), 1)
                else:
                    self.assertNotIn("build", res)
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
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_stage_and_build_pkgs_db
                    )
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)
                self.assertIsInstance(res, dict)
                self.assertNotIn("staged", res)
                if build_packages and sec_not_for_build_packages:
                    self.assertIn("build", res)
                    res_build_packages = res["build"]
                    self.assertEqual(len(res_build_packages), 1)
                    self.assertIn("snapcraft", res_build_packages)
                    self.assertEqual(len(res_build_packages["snapcraft"]), 1)
                    self.assertIn("5501-1", res_build_packages["snapcraft"])
                    self.assertEqual(len(res), 1)
                else:
                    self.assertNotIn("build", res)
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
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_stage_and_build_pkgs_db, with_cves=True
                    )
                else:
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_db, with_cves=True
                    )
                self.assertIsInstance(res, dict)
                self.assertNotIn("staged", res)
                if build_packages and sec_not_for_build_packages:
                    self.assertIn("build", res)
                    res_build_packages = res["build"]
                    self.assertEqual(len(res_build_packages), 1)
                    self.assertIn("snapcraft", res_build_packages)
                    self.assertEqual(len(res_build_packages["snapcraft"]), 1)
                    self.assertIn("5501-1", res_build_packages["snapcraft"])
                    self.assertIn(
                        "CVE-2020-9999", res_build_packages["snapcraft"]["5501-1"]
                    )
                    self.assertEqual(len(res), 1)
                else:
                    self.assertNotIn("build", res)
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
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_stage_and_build_pkgs_db, with_cves=True
                    )
                else:
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_db, with_cves=True
                    )
                self.assertIsInstance(res, dict)
                self.assertNotIn("staged", res)
                if build_packages and sec_not_for_build_packages:
                    self.assertIn("build", res)
                    res_build_packages = res["build"]
                    self.assertEqual(len(res_build_packages), 1)
                    self.assertIn("snapcraft", res_build_packages)
                    self.assertEqual(len(res_build_packages["snapcraft"]), 1)
                    self.assertIn("5501-1", res_build_packages["snapcraft"])
                    self.assertIn(
                        "CVE-2020-9999", res_build_packages["snapcraft"]["5501-1"]
                    )
                    self.assertEqual(len(res), 1)
                else:
                    self.assertNotIn("build", res)
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
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_stage_and_build_pkgs_db, with_cves=True
                    )
                else:
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_db, with_cves=True
                    )
                self.assertIsInstance(res, dict)
                if build_packages and sec_not_for_build_packages:
                    self.assertIn("build", res)
                    res_build_packages = res["build"]
                    self.assertEqual(len(res_build_packages), 1)
                    self.assertIn("snapcraft", res_build_packages)
                    self.assertEqual(len(res_build_packages["snapcraft"]), 1)
                    self.assertIn("5501-1", res_build_packages["snapcraft"])
                    self.assertIn(
                        "CVE-2020-9999", res_build_packages["snapcraft"]["5501-1"]
                    )
                    self.assertEqual(len(res), 2)
                else:
                    self.assertNotIn("build", res)
                    self.assertEqual(len(res), 1)

                self.assertIn("staged", res)
                staged_packages = res["staged"]
                self.assertEqual(len(staged_packages), 2)
                self.assertIn("libxcursor1", staged_packages)
                self.assertEqual(len(staged_packages["libxcursor1"]), 1)
                self.assertIn("3501-1", staged_packages["libxcursor1"])
                self.assertIsInstance(staged_packages["libxcursor1"]["3501-1"], list)
                self.assertEqual(len(staged_packages["libxcursor1"]["3501-1"]), 1)
                self.assertIn(
                    "CVE-2017-16612", staged_packages["libxcursor1"]["3501-1"]
                )
                self.assertIn("libtiff5", staged_packages)
                self.assertEqual(len(staged_packages["libtiff5"]), 2)
                self.assertIsInstance(staged_packages["libtiff5"]["3602-1"], list)
                self.assertEqual(len(staged_packages["libtiff5"]["3602-1"]), 27)
                self.assertIsInstance(staged_packages["libtiff5"]["3606-1"], list)
                self.assertEqual(len(staged_packages["libtiff5"]["3606-1"]), 12)

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
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_stage_and_build_pkgs_db, with_cves=True
                    )
                else:
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_db, with_cves=True
                    )
                self.assertIsInstance(res, dict)
                if build_packages and sec_not_for_build_packages:
                    self.assertIn("build", res)
                    res_build_packages = res["build"]
                    self.assertEqual(len(res_build_packages), 1)
                    self.assertIn("snapcraft", res_build_packages)
                    self.assertEqual(len(res_build_packages["snapcraft"]), 1)
                    self.assertIn("5501-1", res_build_packages["snapcraft"])
                    self.assertIn(
                        "CVE-2020-9999", res_build_packages["snapcraft"]["5501-1"]
                    )
                    self.assertEqual(len(res), 2)
                else:
                    self.assertNotIn("build", res)
                    self.assertEqual(len(res), 1)

                self.assertIn("staged", res)
                staged_packages = res["staged"]
                self.assertIn("libtiff5", staged_packages)
                self.assertEqual(len(staged_packages["libtiff5"]), 2)
                self.assertIsInstance(staged_packages["libtiff5"]["3602-1"], list)
                self.assertEqual(len(staged_packages["libtiff5"]["3602-1"]), 27)
                self.assertIsInstance(staged_packages["libtiff5"]["3606-1"], list)
                self.assertEqual(len(staged_packages["libtiff5"]["3606-1"]), 12)

                # since it was removed from primed-stage-packages, we
                # shouldn't have a notice
                self.assertNotIn("libxcursor1", res)

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
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_stage_and_build_pkgs_db
                    )
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)
                self.assertIsInstance(res, dict)
                if build_packages and sec_not_for_build_packages:
                    self.assertIn("build", res)
                    res_build_packages = res["build"]
                    self.assertEqual(len(res_build_packages), 1)
                    self.assertIn("snapcraft", res_build_packages)
                    self.assertEqual(len(res_build_packages["snapcraft"]), 1)
                    self.assertIn("5501-1", res["build"]["snapcraft"])
                    self.assertEqual(len(res), 1)
                else:
                    self.assertNotIn("build", res)
                    self.assertEqual(len(res), 0)

    def test_check_get_secnots_for_rock_manifest_has_newer(self,):
        """Test get_secnots_for_rock_manifest() - has newer"""
        m = yaml.load(
            self.rock_store_db[0]["revisions"][0]["manifest_yaml"],
            Loader=yaml.SafeLoader,
        )
        # clear out all the stage-packages and then add one that has a
        # newer package than what is in the security notices
        m["stage-packages"] = []
        m["stage-packages"].append("libxcursor1=999:1.1.14-1")

        res = store.get_secnots_for_manifest(m, self.secnot_db, False, "rock")
        self.assertIsInstance(res, dict)
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
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_stage_and_build_pkgs_db
                    )
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)
                self.assertIsInstance(res, dict)
                if build_packages and sec_not_for_build_packages:
                    self.assertIn("build", res)
                    res_build_packages = res["build"]
                    self.assertEqual(len(res_build_packages), 1)
                    self.assertIn("snapcraft", res_build_packages)
                    self.assertEqual(len(res_build_packages["snapcraft"]), 1)
                    self.assertIn("5501-1", res_build_packages["snapcraft"])
                    self.assertEqual(len(res), 1)
                else:
                    self.assertNotIn("build", res)
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
                    res = store.get_secnots_for_manifest(
                        m, self.secnot_stage_and_build_pkgs_db
                    )
                else:
                    res = store.get_secnots_for_manifest(m, self.secnot_db)
                self.assertIsInstance(res, dict)
                if build_packages and sec_not_for_build_packages:
                    self.assertIn("build", res)
                    res_build_packages = res["build"]
                    self.assertEqual(len(res_build_packages), 1)
                    self.assertIn("snapcraft", res_build_packages)
                    self.assertEqual(len(res_build_packages["snapcraft"]), 1)
                    self.assertIn("5501-1", res_build_packages["snapcraft"])
                    self.assertEqual(len(res), 1)
                else:
                    self.assertNotIn("build", res)
                    self.assertEqual(len(res), 0)

    def test_check_get_ubuntu_release_from_manifest_store_db(self):
        """Test get_ubuntu_release_from_manifest() - test-store-unittest-1.db"""
        store_dbs = {
            "snap": [self.store_db, self.first_revision, "xenial"],
            "rock": [self.rock_store_db, 0, "focal"],
        }
        for store_type, store_metadata in store_dbs.items():
            (store_db, revision_index, ubuntu_release,) = store_metadata
            with self.subTest(
                store_db=store_db,
                revision_index=revision_index,
                ubuntu_release=ubuntu_release,
            ):
                items = store_db[0]
                m = yaml.load(
                    items["revisions"][revision_index]["manifest_yaml"],
                    Loader=yaml.SafeLoader,
                )
                res = store.get_ubuntu_release_from_manifest(m, store_type)
                self.assertEqual(res, ubuntu_release)

    def test_check_get_ubuntu_release_from_manifest(self):
        """Test get_ubuntu_release_from_manifest() - no base, use default"""
        m = self.manifest_basic
        res = store.get_ubuntu_release_from_manifest(m)
        # no base
        self.assertEqual(res, "xenial")

    def test_check_get_ubuntu_release_from_rock_manifest_os_release_focal(self):
        """Test get_ubuntu_release_from_manifest() - focal"""
        m = self.rock_manifest_basic
        res = store.get_ubuntu_release_from_manifest(m, "rock")
        self.assertEqual(res, "focal")

    def test_check_get_ubuntu_release_from_rock_manifest_os_release_xenial(self):
        """Test get_ubuntu_release_from_manifest() - ubuntu/xenial"""
        m = copy.deepcopy(self.rock_manifest_basic)
        m["os-release-id"] = "ubuntu"
        m["os-release-version-id"] = "16.04"
        res = store.get_ubuntu_release_from_manifest(m, "rock")
        self.assertEqual(res, "xenial")

    def test_check_get_ubuntu_release_from_rock_manifest_os_release_trusty(self):
        """Test get_ubuntu_release_from_manifest() - ubuntu/trusty"""
        m = copy.deepcopy(self.rock_manifest_basic)
        m["os-release-id"] = "ubuntu"
        m["os-release-version-id"] = "14.04"
        res = store.get_ubuntu_release_from_manifest(m, "rock")
        self.assertEqual(res, "trusty")

    def test_check_get_ubuntu_release_from_rock_manifest_os_release_bionic(self):
        """Test get_ubuntu_release_from_manifest() - ubuntu/bionic"""
        m = copy.deepcopy(self.rock_manifest_basic)
        m["os-release-id"] = "ubuntu"
        m["os-release-version-id"] = "18.04"
        res = store.get_ubuntu_release_from_manifest(m, "rock")
        self.assertEqual(res, "bionic")

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

    def test_check_get_ubuntu_release_from_manifest_os_release_neon_bionic_core22(self):
        """Test get_ubuntu_release_from_manifest() - neon/18.04 with base: core22"""
        m = copy.deepcopy(self.manifest_basic)
        m["base"] = "core22"
        m["snapcraft-os-release-id"] = "neon"
        m["snapcraft-os-release-version-id"] = "18.04"
        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEqual(res, "jammy")

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
                parts = res["parts"]
                self.assertIn("faked-by-review-tools", parts)
                self.assertIn("stage-packages", parts["faked-by-review-tools"])
                self.assertIn(
                    "bar=1.2~", parts["faked-by-review-tools"]["stage-packages"]
                )
                self.assertIn("build-packages", parts["faked-by-review-tools"])
                self.assertIn(
                    "snapcraft=1.1.1", parts["faked-by-review-tools"]["build-packages"]
                )
            else:
                snapcraft_version_value = [
                    "not_present",
                    None,
                    "",
                    "'''4.2'''",
                    "$(awk '/^version:/{print }' /snap/snapcraft/current/meta/snap.yaml)",
                ]
                for invalid_snapcraft_version in snapcraft_version_value:
                    if invalid_snapcraft_version != "not_present":
                        m["snapcraft-version"] = invalid_snapcraft_version
                    else:
                        del m["snapcraft-version"]
                    res = store.get_faked_build_and_stage_packages(m)
                    self.assertIn("faked-by-review-tools", res["parts"])
                    parts = res["parts"]
                    self.assertIn("stage-packages", parts["faked-by-review-tools"])
                    self.assertIn(
                        "bar=1.2~", parts["faked-by-review-tools"]["stage-packages"]
                    )
                    self.assertIn("build-packages", parts["faked-by-review-tools"])
                    self.assertEqual(
                        len(parts["faked-by-review-tools"]["build-packages"]), 0
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
            parts = res["parts"]
            self.assertIn("faked-by-review-tools", parts)
            self.assertIn("stage-packages", parts["faked-by-review-tools"])
            self.assertIn("bar=1.2~", parts["faked-by-review-tools"]["stage-packages"])
            self.assertIn("build-packages", parts["faked-by-review-tools"])
            self.assertIn(
                "snapcraft=1.1.1", parts["faked-by-review-tools"]["build-packages"]
            )
            self.assertNotIn("faked-by-review-tools", m["parts"])

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
                parts = res["parts"]
                self.assertIn("faked-by-review-tools", parts)
                self.assertIn("stage-packages", parts["faked-by-review-tools"])
                self.assertIn(
                    "bar=1.2~", parts["faked-by-review-tools"]["stage-packages"]
                )
                self.assertIn("build-packages", parts["faked-by-review-tools"])
                self.assertIn(
                    "snapcraft=1.1.1", parts["faked-by-review-tools"]["build-packages"]
                )
            else:
                snapcraft_version_value = ["not_present", None, ""]
                for invalid_snapcraft_version in snapcraft_version_value:
                    if invalid_snapcraft_version != "not_present":
                        m["snapcraft-version"] = invalid_snapcraft_version
                    else:
                        del m["snapcraft-version"]
                    res = store.get_faked_build_and_stage_packages(m)
                    parts = res["parts"]
                    self.assertIn("faked-by-review-tools", parts)
                    self.assertIn("stage-packages", parts["faked-by-review-tools"])
                    self.assertIn(
                        "bar=1.2~", parts["faked-by-review-tools"]["stage-packages"]
                    )
                    self.assertIn("build-packages", parts["faked-by-review-tools"])
                    self.assertEqual(
                        len(parts["faked-by-review-tools"]["build-packages"]), 0
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
                parts = res["parts"]
                self.assertIn("faked-by-review-tools", parts)
                self.assertIn("bar=1.2~", res["primed-stage-packages"])
                self.assertIn("build-packages", parts["faked-by-review-tools"])
                self.assertEqual(
                    len(parts["faked-by-review-tools"]["build-packages"]), 1
                )
                self.assertIn(
                    "snapcraft=1.1.1", parts["faked-by-review-tools"]["build-packages"]
                )
            else:
                snapcraft_version_value = ["not_present", None, ""]
                for invalid_snapcraft_version in snapcraft_version_value:
                    if invalid_snapcraft_version != "not_present":
                        m["snapcraft-version"] = invalid_snapcraft_version
                    else:
                        del m["snapcraft-version"]

                res = store.get_faked_build_and_stage_packages(m)
                parts = res["parts"]
                self.assertIn("faked-by-review-tools", parts)
                self.assertIn("bar=1.2~", res["primed-stage-packages"])
                self.assertIn("build-packages", parts["faked-by-review-tools"])
                self.assertEqual(
                    len(parts["faked-by-review-tools"]["build-packages"]), 0
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
                parts = res["parts"]
                self.assertIn("faked-by-review-tools", parts)
                self.assertNotIn("faked-by-review-tools", m["parts"])
                self.assertIn("bar=1.2~", res["primed-stage-packages"])
                self.assertIn("libxcursor1=1:1.1.14-1", res["primed-stage-packages"])
                self.assertIn("build-packages", parts["faked-by-review-tools"])
                self.assertEqual(
                    len(parts["faked-by-review-tools"]["build-packages"]), 1
                )
                self.assertIn(
                    "snapcraft=1.1.1", parts["faked-by-review-tools"]["build-packages"]
                )
            else:
                snapcraft_version_value = ["not_present", None, ""]
                for invalid_snapcraft_version in snapcraft_version_value:
                    if invalid_snapcraft_version != "not_present":
                        m["snapcraft-version"] = invalid_snapcraft_version
                    else:
                        del m["snapcraft-version"]

                    res = store.get_faked_build_and_stage_packages(m)
                    parts = res["parts"]
                    self.assertIn("faked-by-review-tools", parts)
                    self.assertNotIn("faked-by-review-tools", m["parts"])
                    self.assertIn("bar=1.2~", res["primed-stage-packages"])
                    self.assertIn(
                        "libxcursor1=1:1.1.14-1", res["primed-stage-packages"]
                    )
                    self.assertIn("build-packages", parts["faked-by-review-tools"])
                    self.assertEqual(
                        len(parts["faked-by-review-tools"]["build-packages"]), 0
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
        parts = res["parts"]
        self.assertIn("faked-by-review-tools", parts)
        self.assertIn("stage-packages", parts["faked-by-review-tools"])
        self.assertIn(
            "bar=1.2-3ubuntu0.4", parts["faked-by-review-tools"]["stage-packages"]
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
        self.assertIn("faked-by-review-tools", res["parts"])
        self.assertIn("bar=1.2-3ubuntu0.4", res["primed-stage-packages"])
        self.assertIn("libxcursor1=1:1.1.14-1", res["primed-stage-packages"])

    def test_get_faked_stage_packages_auto_kernel(self):
        """Test get_faked_stage_packages"""
        from reviewtools.overrides import update_stage_packages

        update_stage_packages["foo"] = {"linux-image-generic": "auto-kernel"}
        m = {}
        m["name"] = "foo"
        m["version"] = "4.4.0-140.141"
        m["parts"] = {"foo-part": {}}

        res = store.get_faked_build_and_stage_packages(m)
        self.assertIn("faked-by-review-tools", res["parts"])
        self.assertIn("stage-packages", res["parts"]["faked-by-review-tools"])
        self.assertIn(
            "linux-image-generic=4.4.0.140.999999",
            res["parts"]["faked-by-review-tools"]["stage-packages"],
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
        self.assertIn("faked-by-review-tools", res["parts"])
        self.assertIn(
            "linux-image-generic=4.4.0.140.999999", res["primed-stage-packages"]
        )
        self.assertIn("libxcursor1=1:1.1.14-1", res["primed-stage-packages"])

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
        self.assertIn("faked-by-review-tools", res["parts"])
        self.assertIn("stage-packages", res["parts"]["faked-by-review-tools"])
        self.assertIn(
            "bar=2.0", res["parts"]["faked-by-review-tools"]["stage-packages"]
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
        self.assertIn("faked-by-review-tools", res["parts"])
        self.assertIn("bar=2.0", res["primed-stage-packages"])
        self.assertIn("libxcursor1=1:1.1.14-1", res["primed-stage-packages"])

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
        self.assertIn("faked-by-review-tools", res["parts"])
        self.assertIn("stage-packages", res["parts"]["faked-by-review-tools"])
        self.assertIn(
            "bar=1.2~", res["parts"]["faked-by-review-tools"]["stage-packages"]
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
        self.assertIn("faked-by-review-tools", res["parts"])
        self.assertIn("bar=1.2~", res["primed-stage-packages"])
        self.assertIn("libxcursor1=1:1.1.14-1", res["primed-stage-packages"])

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
        parts = res["parts"]
        self.assertIn("faked-by-review-tools", parts)
        self.assertIn("stage-packages", parts["faked-by-review-tools"])
        self.assertEqual(len(parts["faked-by-review-tools"]["stage-packages"]), 0)
        self.assertEqual(len(parts["faked-by-review-tools"]["build-packages"]), 1)
        self.assertIn(
            "snapcraft=1.1.1", parts["faked-by-review-tools"]["build-packages"]
        )
        self.assertNotIn("bar=1.2~", parts["faked-by-review-tools"]["build-packages"])
        self.assertNotIn("faked-by-review-tools", m["parts"])

    def test_check_get_package_revisions_empty_manifest(self):
        """Test get_package_revisions() - empty manifest - snaps and rocks """
        store_dbs = {
            "snap": read_file_as_json_dict("./tests/test-store-unittest-bare.db"),
            "rock": read_file_as_json_dict("./tests/test-rocks-store-unittest-bare.db"),
        }
        errors = {}
        for store_type, store_db in store_dbs.items():
            with self.subTest():
                res = store.get_pkg_revisions(
                    store_db[0], self.secnot_db, errors, store_type
                )
                self.assertEqual(len(errors), 0)
                self.assertIn("revisions", res)
                self.assertEqual(len(res["revisions"]), 0)

    def test_get_snapcraft_version_from_manifest(self,):
        """Test get_snapcraft_version_from_manifest()"""
        m = {}
        snapcraft_version_values = {
            "invalid": [
                "not_present",
                None,
                "",
                "'''4.2'''",
                "$(awk '/^version:/{print }' /snap/snapcraft/current/meta/snap.yaml",
            ],
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
                    from reviewtools.debversion import DebVersion, compare

                    m["snapcraft-version"] = valid_version
                    self.assertEqual(
                        compare(
                            store.get_snapcraft_version_from_manifest(m),
                            DebVersion(valid_version),
                        ),
                        0,
                    )
