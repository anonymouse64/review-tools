"""sr_tests.py: common setup and tests for test modules"""
#
# Copyright (C) 2013-2020 Canonical Ltd.
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

import copy
import io
import os
import yaml

from unittest.mock import patch
from unittest import TestCase
from reviewtools.common import check_results as common_check_results

# These should be set in the test cases
TEST_SNAP_YAML = ""
TEST_SNAP_MANIFEST_YAML = ""
TEST_PKGFMT_TYPE = "snap"
TEST_PKGFMT_VERSION = "16.04"
TEST_UNPACK_DIR = "/fake"
TEST_UNSQUASHFS_LLS_HDR = ""
TEST_UNSQUASHFS_LLS_ENTRIES = ("", None)
TEST_CMD_NM = (0, "")


#
# Mock override functions
#
def _mock_func(self):
    """Fake test function"""
    return


def _extract_snap_yaml(self):
    """Pretend we read the snap.yaml file"""
    return io.StringIO(TEST_SNAP_YAML)


def _extract_snap_manifest_yaml(self):
    """Pretend we read the snap/manifest.yaml file"""
    return io.StringIO(TEST_SNAP_MANIFEST_YAML)


def _path_join(self, d, fn):
    """Pretend we have a tempdir"""
    return os.path.join("/fake", fn)


def _pkgfmt_type(self):
    """Pretend we found the pkgfmt type"""
    return TEST_PKGFMT_TYPE


def __get_unpack_dir(self):
    """Pretend we found the unpack dir"""
    return TEST_UNPACK_DIR


def _unsquashfs_lls(self, fn):
    """Pretend we ran unsquashfs -lls fn"""
    return (TEST_UNSQUASHFS_LLS_HDR, TEST_UNSQUASHFS_LLS_ENTRIES)


def _cmd_nm(self, args):
    """Pretend ran nm ..."""
    return TEST_CMD_NM


def create_patches():
    # http://docs.python.org/3.4/library/unittest.mock-examples.html
    # Mock patching. Don't use decorators but instead patch in setUp() of the
    # child.
    patches = []
    patches.append(patch("reviewtools.common.Review._check_package_exists", _mock_func))
    patches.append(
        patch("reviewtools.sr_common.SnapReview._extract_snap_yaml", _extract_snap_yaml)
    )
    patches.append(
        patch(
            "reviewtools.sr_common.SnapReview._extract_snap_manifest_yaml",
            _extract_snap_manifest_yaml,
        )
    )
    patches.append(patch("reviewtools.sr_common.SnapReview._path_join", _path_join))
    patches.append(patch("reviewtools.common.unpack_pkg", _mock_func))
    patches.append(patch("reviewtools.common.raw_unpack_pkg", _mock_func))
    patches.append(
        patch("reviewtools.sr_common.SnapReview._list_all_files", _mock_func)
    )
    patches.append(
        patch(
            "reviewtools.sr_common.SnapReview._list_all_compiled_binaries", _mock_func
        )
    )

    patches.append(patch("reviewtools.common.Review._list_all_files", _mock_func))
    patches.append(
        patch("reviewtools.common.Review._list_all_compiled_binaries", _mock_func)
    )

    # sr_common
    patches.append(
        patch("reviewtools.sr_common.SnapReview._get_unpack_dir", __get_unpack_dir)
    )
    patches.append(patch("reviewtools.sr_common.SnapReview._pkgfmt_type", _pkgfmt_type))
    patches.append(
        patch("reviewtools.sr_common.SnapReview._unsquashfs_lls", _unsquashfs_lls)
    )

    # sr_functional
    patches.append(
        patch("reviewtools.sr_functional.SnapReviewFunctional._cmd_nm", _cmd_nm)
    )

    return patches


class TestSnapReview(TestCase):
    """Tests for the snap review tool."""

    def __init__(self, *args):
        TestCase.__init__(self, *args)
        self._reset_test_data()

    def _reset_test_data(self):
        self.test_snap_yaml = dict()
        self.test_snap_manifest_yaml = dict()
        self.set_test_pkgfmt("snap", "16.04")

        self.set_test_snap_yaml("name", "foo")
        self.set_test_snap_yaml("version", "0.1")
        self.set_test_snap_yaml("description", "Test description")
        self.set_test_snap_yaml("summary", "Test summary")
        self.set_test_snap_yaml("architectures", ["all"])
        apps = dict()
        apps["bar"] = dict()
        apps["bar"]["command"] = "bin/bar"
        self.set_test_snap_yaml("apps", apps)

        # mockup a package name
        self._update_test_name()

    def _update_test_snap_yaml(self):
        global TEST_SNAP_YAML
        TEST_SNAP_YAML = yaml.dump(
            self.test_snap_yaml, default_flow_style=False, indent=4
        )

    def _update_test_snap_manifest_yaml(self):
        global TEST_SNAP_MANIFEST_YAML
        TEST_SNAP_MANIFEST_YAML = yaml.dump(
            self.test_snap_manifest_yaml, default_flow_style=False, indent=4
        )

    def _update_test_name(self):
        self.test_name = "%s.origin_%s_%s.snap" % (
            self.test_snap_yaml["name"],
            self.test_snap_yaml["version"],
            self.test_snap_yaml["architectures"][0],
        )

    def check_results(
        self, report, expected_counts={"info": 1, "warn": 0, "error": 0}, expected=None
    ):
        common_check_results(self, report, expected_counts, expected)

    def check_manual_review(
        self, report, check_name, result_type="error", manual_review=True
    ):
        result = report[result_type][check_name]
        self.assertEqual(result["manual_review"], manual_review)

    def set_test_snap_yaml(self, key, value):
        """Set key in meta/snap.yaml to value. If value is None, remove
           key"""
        if value is None:
            if key in self.test_snap_yaml:
                self.test_snap_yaml.pop(key, None)
        else:
            self.test_snap_yaml[key] = value
        self._update_test_snap_yaml()

    def set_test_snap_manifest_yaml(self, key, value):
        """Set key in snap/manifest.yaml to value. If value is None, remove
           key"""
        if value is None:
            if key in self.test_snap_manifest_yaml:
                self.test_snap_manifest_yaml.pop(key, None)
        else:
            self.test_snap_manifest_yaml[key] = value
        self._update_test_snap_manifest_yaml()

    def set_test_pkgfmt(self, t, v):
        global TEST_PKGFMT_TYPE
        global TEST_PKGFMT_VERSION
        TEST_PKGFMT_TYPE = t
        TEST_PKGFMT_VERSION = v

    def set_test_unpack_dir(self, d):
        global TEST_UNPACK_DIR
        TEST_UNPACK_DIR = d

    def set_test_unsquashfs_lls(self, hdr, entries):
        global TEST_UNSQUASHFS_LLS_HDR
        global TEST_UNSQUASHFS_LLS_ENTRIES
        TEST_UNSQUASHFS_LLS_HDR = hdr
        TEST_UNSQUASHFS_LLS_ENTRIES = copy.copy(entries)

    def set_test_cmd_nm(self, rc, s):
        global TEST_CMD_NM
        TEST_CMD_NM = (rc, s)

    def setUp(self):
        """Make sure our patches are applied everywhere"""
        patches = create_patches()
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.old_umask = os.umask(0o022)

    def tearDown(self):
        """Make sure we reset everything to known good values"""
        global TEST_SNAP_YAML
        TEST_SNAP_YAML = ""
        global TEST_SNAP_MANIFEST_YAML
        TEST_SNAP_MANIFEST_YAML = ""
        global TEST_PKGFMT_TYPE
        TEST_PKGFMT_TYPE = "snap"
        global TEST_PKGFMT_VERSION
        TEST_PKGFMT_VERSION = "16.04"
        global TEST_UNPACK_DIR
        TEST_UNPACK_DIR = "/fake"
        global TEST_UNSQUASHFS_LLS_HDR
        TEST_UNSQUASHFS_LLS_HDR = ""
        global TEST_UNSQUASHFS_LLS_ENTRIES
        TEST_UNSQUASHFS_LLS_ENTRIES = ("", None)
        global TEST_CMD_NM
        TEST_CMD_NM = (0, "")

        self._reset_test_data()
        os.umask(self.old_umask)
