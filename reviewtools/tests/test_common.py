"""test_common.py: tests for the common module"""
#
# Copyright (C) 2020 Canonical Ltd.
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
import os
import shutil
import tempfile

from reviewtools.sr_common import SnapReview
import reviewtools.sr_tests as sr_tests
import reviewtools.common
from reviewtools.common import StatLLS
from reviewtools.tests import utils


class TestSnapReviewSkeleton(sr_tests.TestSnapReview):
    """Tests for common module"""

    def setUp(self):
        super().setUp()
        # This allows calling instance methods via:
        #   self.review.foo()
        self.review = SnapReview("app.snap", "common_review_type")

    def mkdtemp(self):
        """Create a temp dir which is cleaned up after test."""
        tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp_dir)
        return tmp_dir

    def set_item(
        self, ftype, mode, owner, size, major, minor, date, time, fname, fname_full
    ):
        item = {}
        item[StatLLS.FILETYPE] = ftype
        item[StatLLS.MODE] = mode
        item[StatLLS.OWNER] = owner
        item[StatLLS.USER], item[StatLLS.GROUP] = owner.split("/")
        if size is not None:
            item[StatLLS.SIZE] = size
        if major is not None:
            item[StatLLS.MAJOR] = major
        if minor is not None:
            item[StatLLS.MINOR] = minor
        item[StatLLS.DATE] = date
        item[StatLLS.TIME] = time
        item[StatLLS.FILENAME] = fname
        item[StatLLS.FULLNAME] = fname_full
        return copy.copy(item)

    def test_init_override_state_input(self):
        """Test init_override_state_input()"""
        st = reviewtools.common.init_override_state_input()
        self.assertTrue(isinstance(st, dict))
        self.assertEqual(len(st), 1)
        self.assertTrue("format" in st)
        self.assertEqual(st["format"], reviewtools.common.STATE_FORMAT_VERSION)

    def test_verify_override_state(self):
        """Test verify_override_state()"""
        st = reviewtools.common.init_override_state_input()
        reviewtools.common.verify_override_state(st)

        try:
            reviewtools.common.verify_override_state([])
        except ValueError as e:
            self.assertEqual(str(e), "state object is not a dict")

        try:
            reviewtools.common.verify_override_state({})
        except ValueError as e:
            self.assertEqual(str(e), "missing required 'format' key")

        try:
            reviewtools.common.verify_override_state({"format": 0})
        except ValueError as e:
            self.assertEqual(
                str(e),
                "'format' should be a positive JSON integer <= %d"
                % reviewtools.common.STATE_FORMAT_VERSION,
            )

    def test_unsquashfs_lls(self):
        """Test unsquashfs -lls"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        rc, out = reviewtools.common.unsquashfs_lls(package)
        self.assertEqual(rc, 0)

        for exp in [
            "squashfs-root",
            "-rw-r--r-- root/root",
            "squashfs-root/meta/snap.yaml",
        ]:
            self.assertTrue(exp in out)

    def test_unsquashfs_lls_fail(self):
        """Test unsquashfs -lls - fail"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)

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

        rc, out = reviewtools.common.unsquashfs_lls(package)
        self.assertEqual(rc, 1)
        self.assertTrue("unsquashfs failure" in out)

    def test_unsquashfs_lls_parse_good(self):
        """Test unsquashfs_lls_parse() - good"""
        input = """Parallel unsquashfs: Using 4 processors
2 inodes (2 blocks) to write

drwxrwxr-x root/root                27 2020-03-24 09:11 squashfs-root
drwxr-xr-x root/root                48 2020-03-24 09:11 squashfs-root/meta
-rw-r--r-- root/root              2870 2020-03-24 09:11 squashfs-root/meta/icon.png
-rw-r--r-- root/root                99 2020-03-24 09:11 squashfs-root/meta/snap.yaml
"""
        hdr, entries = reviewtools.common.unsquashfs_lls_parse(input)

        for exp in [
            "Parallel unsquashfs: Using 4 processors",
            "2 inodes (2 blocks) to write",
        ]:
            self.assertTrue(exp in hdr)

        # individual line parsing done elsewhere
        self.assertEqual(4, len(entries))
        for line, item in entries:
            self.assertTrue("squashfs-root" in line)
            self.assertFalse(item is None)

    def test_unsquashfs_lls_parse_bad(self):
        """Test unsquashfs_lls_parse() - bad"""
        for input, exp in [
            (
                """output
too
short
""",
                "'unsquashfs -lls ouput too short'",
            ),
            ("", "'unsquashfs -lls ouput too short'"),
            (
                """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

:rwxrwxr-x root/root                38 2016-03-11 12:25 squashfs-root/foo
""",
                "'malformed lines in unsquashfs output: \\'\"unknown type \\':\\' for entry \\'./foo\\'\"\\''",
            ),
        ]:
            try:
                reviewtools.common.unsquashfs_lls_parse(input)
            except reviewtools.common.ReviewException as e:
                self.assertEqual(str(e), exp)
                continue

            raise Exception("parsed input should be invalid")

    def test_unsquashfs_lls_parse_line_good(self):
        """Test unsquashfs_lls_parse() - good"""

        for input, exp in [
            # dir
            (
                "drwxr-xr-x root/root               266 2019-06-06 08:03 squashfs-root",
                self.set_item(
                    "d",
                    "rwxr-xr-x",
                    "root/root",
                    "266",
                    None,
                    None,
                    "2019-06-06",
                    "08:03",
                    ".",
                    "squashfs-root",
                ),
            ),
            # file
            (
                "-rw-r--r-- root/root                53 2018-02-07 07:08 squashfs-root/README",
                self.set_item(
                    "-",
                    "rw-r--r--",
                    "root/root",
                    "53",
                    None,
                    None,
                    "2018-02-07",
                    "07:08",
                    "./README",
                    "squashfs-root/README",
                ),
            ),
            (
                "-rw-r--r-- root/root                53 2018-02-07 07:08 squashfs-root/name with spaces",
                self.set_item(
                    "-",
                    "rw-r--r--",
                    "root/root",
                    "53",
                    None,
                    None,
                    "2018-02-07",
                    "07:08",
                    "./name with spaces",
                    "squashfs-root/name with spaces",
                ),
            ),
            (
                "-rw-r--r-- root/root                53 2018-02-07 07:08 squashfs-root/name with two  spaces",
                self.set_item(
                    "-",
                    "rw-r--r--",
                    "root/root",
                    "53",
                    None,
                    None,
                    "2018-02-07",
                    "07:08",
                    "./name with two  spaces",
                    "squashfs-root/name with two  spaces",
                ),
            ),
            (
                "-rw-r--r-- root/root                53 2018-02-07 07:08 squashfs-root/name with trailing spaces   ",
                self.set_item(
                    "-",
                    "rw-r--r--",
                    "root/root",
                    "53",
                    None,
                    None,
                    "2018-02-07",
                    "07:08",
                    "./name with trailing spaces   ",
                    "squashfs-root/name with trailing spaces   ",
                ),
            ),
            (
                "-rw-r--r-- root/root                53 2018-02-07 07:08 squashfs-root/ squashfs-root with leading and trailing spaces ",
                self.set_item(
                    "-",
                    "rw-r--r--",
                    "root/root",
                    "53",
                    None,
                    None,
                    "2018-02-07",
                    "07:08",
                    "./ squashfs-root with leading and trailing spaces ",
                    "squashfs-root/ squashfs-root with leading and trailing spaces ",
                ),
            ),
            # unicode filename
            (
                "-rw-r--r-- root/root                53 2018-02-07 07:08 squashfs-root/😃",
                self.set_item(
                    "-",
                    "rw-r--r--",
                    "root/root",
                    "53",
                    None,
                    None,
                    "2018-02-07",
                    "07:08",
                    "./😃",
                    "squashfs-root/😃",
                ),
            ),
            # char (major/minor variant 1)
            (
                "crw------- root/daemon           1,  3 2018-02-07 10:04 squashfs-root/dev/char",
                self.set_item(
                    "c",
                    "rw-------",
                    "root/daemon",
                    None,
                    "1",
                    "3",
                    "2018-02-07",
                    "10:04",
                    "./dev/char",
                    "squashfs-root/dev/char",
                ),
            ),
            # block (major/minor variant 2)
            (
                "brw------- daemon/daemon         1,249 2018-02-07 10:04 squashfs-root/dev/block",
                self.set_item(
                    "b",
                    "rw-------",
                    "daemon/daemon",
                    None,
                    "1",
                    "249",
                    "2018-02-07",
                    "10:04",
                    "./dev/block",
                    "squashfs-root/dev/block",
                ),
            ),
            # symlink
            (
                "lrwxrwxrwx root/root                 6 2018-02-07 10:04 squashfs-root/symlink -> README",
                self.set_item(
                    "l",
                    "rwxrwxrwx",
                    "root/root",
                    "6",
                    None,
                    None,
                    "2018-02-07",
                    "10:04",
                    "./symlink -> README",
                    "squashfs-root/symlink -> README",
                ),
            ),
            # pipe
            (
                "prw-rw---- root/daemon               0 2018-02-07 10:04 squashfs-root/pipe",
                self.set_item(
                    "p",
                    "rw-rw----",
                    "root/daemon",
                    "0",
                    None,
                    None,
                    "2018-02-07",
                    "10:04",
                    "./pipe",
                    "squashfs-root/pipe",
                ),
            ),
            # socket
            (
                "srw-rw-rw- root/root                 0 2018-02-07 10:04 squashfs-root/socket",
                self.set_item(
                    "s",
                    "rw-rw-rw-",
                    "root/root",
                    "0",
                    None,
                    None,
                    "2018-02-07",
                    "10:04",
                    "./socket",
                    "squashfs-root/socket",
                ),
            ),
        ]:
            item = reviewtools.common.unsquashfs_lls_parse_line(input)
            self.assertEqual(len(exp), len(item))
            for i in exp:
                self.assertEqual(item[i], exp[i])

    def test_unsquashfs_lls_parse_line_bad(self):
        """Test unsquashfs_lls_parse() - bad"""
        for input, exp in [
            # file type
            (
                ":rwxrwxr-x root/root                38 2016-03-11 12:25 squashfs-root/foo",
                "\"unknown type ':' for entry './foo'\"",
            ),
            # unsquashfs doesn't handle these ls -l types
            (
                "?rwxrwxr-x root/root                38 2016-03-11 12:25 squashfs-root/foo",
                "\"unknown type '?' for entry './foo'\"",
            ),
            (
                "-rwxrwxr-x root/root                38 2016-03-11",
                "\"wrong number of fields in '-rwxrwxr-x root/root                38 2016-03-11'\"",
            ),
            # mode
            (
                "-rwxrwxr-xx root/root                38 2016-03-11 12:25 squashfs-root/foo",
                "\"mode 'rwxrwxr-xx' malformed for './foo'\"",
            ),
            (
                "-rwxrwxrTx root/root                38 2016-03-11 12:25 squashfs-root/foo",
                "\"mode 'rwxrwxrTx' malformed for './foo'\"",
            ),
            # owner
            (
                "-rw-rw-r-- bad                8 2016-03-11 12:25 squashfs-root/foo",
                "\"user/group 'bad' malformed for './foo'\"",
            ),
            # major
            (
                "crw-rw-rw- root/root                a,  0 2016-03-11 12:25 squashfs-root/foo",
                "\"major 'a' malformed for './foo'\"",
            ),
            (
                "crw-rw-rw- root/root                a,120 2016-03-11 12:25 squashfs-root/foo",
                "\"major 'a' malformed for './foo'\"",
            ),
            # minor
            (
                "brw-rw-rw- root/root                8,  a 2016-03-11 12:25 squashfs-root/foo",
                "\"minor 'a' malformed for './foo'\"",
            ),
            (
                "brw-rw-rw- root/root                8,12a 2016-03-11 12:25 squashfs-root/foo",
                "\"minor '12a' malformed for './foo'\"",
            ),
            # size
            (
                "-rw-rw-rw- root/root                a 2016-03-11 12:25 squashfs-root/foo",
                "\"size 'a' malformed for './foo'\"",
            ),
            # date
            (
                "-rw-rw-rw- root/root                8 2016-0e-11 12:25 squashfs-root/foo",
                "\"date '2016-0e-11' malformed for './foo'\"",
            ),
            # time
            (
                "-rw-rw-rw- root/root                8 2016-03-11 z2:25 squashfs-root/foo",
                "\"time 'z2:25' malformed for './foo'\"",
            ),
            # embedded NULs
            (
                "-rwxrwxr-x root/root    \x00           38 2016-03-11 12:25 squashfs-root/foo",
                "'entry may not contain NUL characters: -rwxrwxr-x root/root    \\x00           38 2016-03-11 12:25 squashfs-root/foo'",
            ),
            # extra fields
            (
                "extra -rwxrwxr-x root/root               38 2016-03-11 12:25 squashfs-root/foo",
                "'could not determine filename: extra -rwxrwxr-x root/root               38 2016-03-11 12:25 squashfs-root/foo'",
            ),
            (
                "-rwxrwxr-x extra root/root               38 2016-03-11 12:25 squashfs-root/foo",
                "'could not determine filename: -rwxrwxr-x extra root/root               38 2016-03-11 12:25 squashfs-root/foo'",
            ),
            (
                "-rwxrwxr-x root/root    extra           38 2016-03-11 12:25 squashfs-root/foo",
                "'could not determine filename: -rwxrwxr-x root/root    extra           38 2016-03-11 12:25 squashfs-root/foo'",
            ),
            (
                "-rwxrwxr-x root/root                    38 extra 2016-03-11 12:25 squashfs-root/foo",
                "'could not determine filename: -rwxrwxr-x root/root                    38 extra 2016-03-11 12:25 squashfs-root/foo'",
            ),
            (
                "-rwxrwxr-x root/root                    38 2016-03-11 extra 12:25 squashfs-root/foo",
                "'could not determine filename: -rwxrwxr-x root/root                    38 2016-03-11 extra 12:25 squashfs-root/foo'",
            ),
            (
                "-rwxrwxr-x root/root                    38 2016-03-11 12:25 extra squashfs-root/foo",
                "'could not determine filename: -rwxrwxr-x root/root                    38 2016-03-11 12:25 extra squashfs-root/foo'",
            ),
            (
                "brw-rw-rw- root/root        extra        8, 12 2016-03-11 12:25 squashfs-root/foo",
                "'could not determine filename: brw-rw-rw- root/root        extra        8, 12 2016-03-11 12:25 squashfs-root/foo'",
            ),
            (
                "brw-rw-rw- root/root                     8, extra 12 2016-03-11 12:25 squashfs-root/foo",
                "'could not determine filename: brw-rw-rw- root/root                     8, extra 12 2016-03-11 12:25 squashfs-root/foo'",
            ),
            (
                "brw-rw-rw- root/root                     8, 12 extra 2016-03-11 12:25 squashfs-root/foo",
                "'could not determine filename: brw-rw-rw- root/root                     8, 12 extra 2016-03-11 12:25 squashfs-root/foo'",
            ),
            (
                "brw-rw-rw- root/root                     8, 12 2016-03-11 12:25 extra squashfs-root/foo",
                "'could not determine filename: brw-rw-rw- root/root                     8, 12 2016-03-11 12:25 extra squashfs-root/foo'",
            ),
        ]:
            try:
                reviewtools.common.unsquashfs_lls_parse_line(input)
            except reviewtools.common.ReviewException as e:
                self.assertEqual(str(e), exp)
                continue

            raise Exception("parsed input should be invalid")
