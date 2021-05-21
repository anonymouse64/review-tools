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

from reviewtools.sr_common import SnapReview, ReviewException
import reviewtools.sr_tests as sr_tests
import reviewtools.common
from reviewtools.common import StatLLN
from reviewtools.tests import utils


class TestCommon(sr_tests.TestSnapReview):
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
        item[StatLLN.FILETYPE] = ftype
        item[StatLLN.MODE] = mode
        item[StatLLN.OWNER] = owner
        item[StatLLN.UID], item[StatLLN.GID] = owner.split("/")
        if size is not None:
            item[StatLLN.SIZE] = size
        if major is not None:
            item[StatLLN.MAJOR] = major
        if minor is not None:
            item[StatLLN.MINOR] = minor
        item[StatLLN.DATE] = date
        item[StatLLN.TIME] = time
        item[StatLLN.FILENAME] = fname
        item[StatLLN.FULLNAME] = fname_full
        return copy.copy(item)

    def test_init_override_state_input(self):
        """Test init_override_state_input()"""
        st = reviewtools.common.init_override_state_input()
        self.assertTrue(isinstance(st, dict))
        self.assertEqual(len(st), 1)
        self.assertIn("format", st)
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

    def test_unsquashfs_lln(self):
        """Test unsquashfs -lln"""
        output_dir = self.mkdtemp()
        package = utils.make_snap2(output_dir=output_dir)
        rc, out = reviewtools.common.unsquashfs_lln(package)
        self.assertEqual(rc, 0)

        for exp in [
            "squashfs-root",
            "-rw-r--r-- 0/0",
            "squashfs-root/meta/snap.yaml",
        ]:
            self.assertTrue(exp in out)

    def test_unsquashfs_lln_fail(self):
        """Test unsquashfs -lln - fail"""
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

        rc, out = reviewtools.common.unsquashfs_lln(package)
        self.assertEqual(rc, 1)
        self.assertTrue("unsquashfs failure" in out)

    def test_unsquashfs_lln_parse_good(self):
        """Test unsquashfs_lln_parse() - good"""
        input = """Parallel unsquashfs: Using 4 processors
2 inodes (2 blocks) to write

drwxrwxr-x 0/0                27 2020-03-24 09:11 squashfs-root
drwxr-xr-x 0/0                48 2020-03-24 09:11 squashfs-root/meta
-rw-r--r-- 0/0              2870 2020-03-24 09:11 squashfs-root/meta/icon.png
-rw-r--r-- 0/0                99 2020-03-24 09:11 squashfs-root/meta/snap.yaml
"""
        hdr, entries = reviewtools.common.unsquashfs_lln_parse(input)

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

    def test_unsquashfs_lln_parse_bad(self):
        """Test unsquashfs_lln_parse() - bad"""
        for input, exp in [
            (
                """output
too
short
""",
                "'unsquashfs -lln ouput too short'",
            ),
            ("", "'unsquashfs -lln ouput too short'"),
            (
                """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

:rwxrwxr-x 0/0                38 2016-03-11 12:25 squashfs-root/foo
""",
                "'malformed lines in unsquashfs output: \\'\"unknown type \\':\\' for entry \\'./foo\\'\"\\''",
            ),
        ]:
            try:
                reviewtools.common.unsquashfs_lln_parse(input)
            except reviewtools.common.ReviewException as e:
                self.assertEqual(str(e), exp)
                continue

            raise Exception("parsed input should be invalid")

    def test_unsquashfs_lln_parse_line_good(self):
        """Test unsquashfs_lln_parse() - good"""

        for input, exp in [
            # dir
            (
                "drwxr-xr-x 0/0               266 2019-06-06 08:03 squashfs-root",
                self.set_item(
                    "d",
                    "rwxr-xr-x",
                    "0/0",
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
                "-rw-r--r-- 0/0                53 2018-02-07 07:08 squashfs-root/README",
                self.set_item(
                    "-",
                    "rw-r--r--",
                    "0/0",
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
                "-rw-r--r-- 0/0                53 2018-02-07 07:08 squashfs-root/name with spaces",
                self.set_item(
                    "-",
                    "rw-r--r--",
                    "0/0",
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
                "-rw-r--r-- 0/0                53 2018-02-07 07:08 squashfs-root/name with two  spaces",
                self.set_item(
                    "-",
                    "rw-r--r--",
                    "0/0",
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
                "-rw-r--r-- 0/0                53 2018-02-07 07:08 squashfs-root/name with trailing spaces   ",
                self.set_item(
                    "-",
                    "rw-r--r--",
                    "0/0",
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
                "-rw-r--r-- 0/0                53 2018-02-07 07:08 squashfs-root/ squashfs-root with leading and trailing spaces ",
                self.set_item(
                    "-",
                    "rw-r--r--",
                    "0/0",
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
                "-rw-r--r-- 0/0                53 2018-02-07 07:08 squashfs-root/😃",
                self.set_item(
                    "-",
                    "rw-r--r--",
                    "0/0",
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
                "crw------- 0/1           1,  3 2018-02-07 10:04 squashfs-root/dev/char",
                self.set_item(
                    "c",
                    "rw-------",
                    "0/1",
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
                "brw------- 1/1         1,249 2018-02-07 10:04 squashfs-root/dev/block",
                self.set_item(
                    "b",
                    "rw-------",
                    "1/1",
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
                "lrwxrwxrwx 0/0                 6 2018-02-07 10:04 squashfs-root/symlink -> README",
                self.set_item(
                    "l",
                    "rwxrwxrwx",
                    "0/0",
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
                "prw-rw---- 0/1               0 2018-02-07 10:04 squashfs-root/pipe",
                self.set_item(
                    "p",
                    "rw-rw----",
                    "0/1",
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
                "srw-rw-rw- 0/0                 0 2018-02-07 10:04 squashfs-root/socket",
                self.set_item(
                    "s",
                    "rw-rw-rw-",
                    "0/0",
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
            item = reviewtools.common.unsquashfs_lln_parse_line(input)
            self.assertEqual(len(exp), len(item))
            for i in exp:
                self.assertEqual(item[i], exp[i])

    def test_unsquashfs_lln_parse_line_bad(self):
        """Test unsquashfs_lln_parse() - bad"""
        for input, exp in [
            # file type
            (
                ":rwxrwxr-x 0/0                38 2016-03-11 12:25 squashfs-root/foo",
                "\"unknown type ':' for entry './foo'\"",
            ),
            # unsquashfs doesn't handle these ls -l types
            (
                "?rwxrwxr-x 0/0                38 2016-03-11 12:25 squashfs-root/foo",
                "\"unknown type '?' for entry './foo'\"",
            ),
            (
                "-rwxrwxr-x 0/0                38 2016-03-11",
                "\"wrong number of fields in '-rwxrwxr-x 0/0                38 2016-03-11'\"",
            ),
            # mode
            (
                "-rwxrwxr-xx 0/0                38 2016-03-11 12:25 squashfs-root/foo",
                "\"mode 'rwxrwxr-xx' malformed for './foo'\"",
            ),
            (
                "-rwxrwxrTx 0/0                38 2016-03-11 12:25 squashfs-root/foo",
                "\"mode 'rwxrwxrTx' malformed for './foo'\"",
            ),
            # owner
            (
                "-rw-rw-r-- bad                8 2016-03-11 12:25 squashfs-root/foo",
                "\"uid/gid 'bad' malformed for './foo'\"",
            ),
            # major
            (
                "crw-rw-rw- 0/0                a,  0 2016-03-11 12:25 squashfs-root/foo",
                "\"major 'a' malformed for './foo'\"",
            ),
            (
                "crw-rw-rw- 0/0                a,120 2016-03-11 12:25 squashfs-root/foo",
                "\"major 'a' malformed for './foo'\"",
            ),
            # minor
            (
                "brw-rw-rw- 0/0                8,  a 2016-03-11 12:25 squashfs-root/foo",
                "\"minor 'a' malformed for './foo'\"",
            ),
            (
                "brw-rw-rw- 0/0                8,12a 2016-03-11 12:25 squashfs-root/foo",
                "\"minor '12a' malformed for './foo'\"",
            ),
            # size
            (
                "-rw-rw-rw- 0/0                a 2016-03-11 12:25 squashfs-root/foo",
                "\"size 'a' malformed for './foo'\"",
            ),
            # date
            (
                "-rw-rw-rw- 0/0                8 2016-0e-11 12:25 squashfs-root/foo",
                "\"date '2016-0e-11' malformed for './foo'\"",
            ),
            # time
            (
                "-rw-rw-rw- 0/0                8 2016-03-11 z2:25 squashfs-root/foo",
                "\"time 'z2:25' malformed for './foo'\"",
            ),
            # embedded NULs
            (
                "-rwxrwxr-x 0/0    \x00           38 2016-03-11 12:25 squashfs-root/foo",
                "'entry may not contain NUL characters: -rwxrwxr-x 0/0    \\x00           38 2016-03-11 12:25 squashfs-root/foo'",
            ),
            # extra fields
            (
                "extra -rwxrwxr-x 0/0               38 2016-03-11 12:25 squashfs-root/foo",
                "'could not determine filename: extra -rwxrwxr-x 0/0               38 2016-03-11 12:25 squashfs-root/foo'",
            ),
            (
                "-rwxrwxr-x extra 0/0               38 2016-03-11 12:25 squashfs-root/foo",
                "'could not determine filename: -rwxrwxr-x extra 0/0               38 2016-03-11 12:25 squashfs-root/foo'",
            ),
            (
                "-rwxrwxr-x 0/0    extra           38 2016-03-11 12:25 squashfs-root/foo",
                "'could not determine filename: -rwxrwxr-x 0/0    extra           38 2016-03-11 12:25 squashfs-root/foo'",
            ),
            (
                "-rwxrwxr-x 0/0                    38 extra 2016-03-11 12:25 squashfs-root/foo",
                "'could not determine filename: -rwxrwxr-x 0/0                    38 extra 2016-03-11 12:25 squashfs-root/foo'",
            ),
            (
                "-rwxrwxr-x 0/0                    38 2016-03-11 extra 12:25 squashfs-root/foo",
                "'could not determine filename: -rwxrwxr-x 0/0                    38 2016-03-11 extra 12:25 squashfs-root/foo'",
            ),
            (
                "-rwxrwxr-x 0/0                    38 2016-03-11 12:25 extra squashfs-root/foo",
                "'could not determine filename: -rwxrwxr-x 0/0                    38 2016-03-11 12:25 extra squashfs-root/foo'",
            ),
            (
                "brw-rw-rw- 0/0        extra        8, 12 2016-03-11 12:25 squashfs-root/foo",
                "'could not determine filename: brw-rw-rw- 0/0        extra        8, 12 2016-03-11 12:25 squashfs-root/foo'",
            ),
            (
                "brw-rw-rw- 0/0                     8, extra 12 2016-03-11 12:25 squashfs-root/foo",
                "'could not determine filename: brw-rw-rw- 0/0                     8, extra 12 2016-03-11 12:25 squashfs-root/foo'",
            ),
            (
                "brw-rw-rw- 0/0                     8, 12 extra 2016-03-11 12:25 squashfs-root/foo",
                "'could not determine filename: brw-rw-rw- 0/0                     8, 12 extra 2016-03-11 12:25 squashfs-root/foo'",
            ),
            (
                "brw-rw-rw- 0/0                     8, 12 2016-03-11 12:25 extra squashfs-root/foo",
                "'could not determine filename: brw-rw-rw- 0/0                     8, 12 2016-03-11 12:25 extra squashfs-root/foo'",
            ),
        ]:
            try:
                reviewtools.common.unsquashfs_lln_parse_line(input)
            except reviewtools.common.ReviewException as e:
                self.assertEqual(str(e), exp)
                continue

            raise Exception("parsed input should be invalid")

    def test_check_pkg_uncompressed_size_ok(self):
        """Test check_pkg_uncompressed_size() - rocks and snaps """
        pkgs = [
            "./tests/test-rock-redis_5.0-20.04.tar",
            "./tests/test-snapcraft-manifest-unittest_0_amd64.snap",
        ]
        max_size = 3 * 1024 * 1024
        size = 1 * 1024 * 1024
        for pkg in pkgs:
            with self.subTest(pkg=pkg):
                valid_size, _ = reviewtools.common.is_pkg_uncompressed_size_valid(
                    max_size, size, pkg
                )
                self.assertTrue(valid_size)

    def test_check_pkg_uncompressed_size_max_size_error(self):
        """Test check_pkg_uncompressed_size() - rocks and snaps """
        pkgs = [
            "./tests/test-rock-redis_5.0-20.04.tar",
            "./tests/test-snapcraft-manifest-unittest_0_amd64.snap",
        ]
        max_size = 1024
        size = 1 * 1024 * 1024
        for pkg in pkgs:
            with self.subTest(pkg=pkg):
                valid_size, _ = reviewtools.common.is_pkg_uncompressed_size_valid(
                    max_size, size, pkg
                )
                self.assertFalse(valid_size)

    def test_unpack_rock_invalid_format(self):
        """Test unpack_rock() - invalid rock format """
        invalid_rock = "./tests/test-snapcraft-manifest-unittest_0_amd64.snap"
        with self.assertRaises(SystemExit) as e:
            reviewtools.common.unpack_rock(invalid_rock)
        self.assertEqual(e.exception.code, 1)

    def test_unpack_rock_valid_format(self):
        """Test unpack_rock() - valid rock format """
        # TODO: add further unit testing for tar unpacking functionality
        valid_rock = "./tests/test-rock-redis_5.0-20.04.tar"
        unpack_dir = reviewtools.common.unpack_rock(valid_rock)
        self.assertIn("review-tools-", unpack_dir)

    def test_unpack_rock_invalid_format_filename_starting_with_slash(self):
        """Test unpack_rock() - invalid - filename starting with slash """
        # TODO: add further unit testing for tar unpacking functionality
        invalid_rock = "./tests/test-rock-invalid-1.tar"
        with self.assertRaises(SystemExit) as e:
            reviewtools.common.unpack_rock(invalid_rock)
        self.assertEqual(e.exception.code, 1)

    def test_unpack_rock_invalid_format_filename_with_two_dots(self):
        """Test unpack_rock() - invalid - filename with two dots """
        # TODO: add further unit testing for tar unpacking functionality
        invalid_rock = "./tests/test-rock-invalid-2.tar"
        with self.assertRaises(SystemExit) as e:
            reviewtools.common.unpack_rock(invalid_rock)
        self.assertEqual(e.exception.code, 1)

    def test_get_rock_manifest(self):
        """Test get_rock_manifest() """
        valid_rock_fn = "./tests/test-rock-redis_5.0-20.04.tar"
        expected_manifest_yaml = {
            "manifest-version": "1",
            "os-release-id": "ubuntu",
            "os-release-version-id": "20.04",
            "stage-packages": [
                "adduser=3.118ubuntu2,adduser=3.118ubuntu2",
                "apt=2.0.2ubuntu0.2,apt=2.0.2ubuntu0.2",
                "base-files=11ubuntu5.2,base-files=11ubuntu5.2",
                "base-passwd=3.5.47,base-passwd=3.5.47",
                "bash=5.0-6ubuntu1.1,bash=5.0-6ubuntu1.1",
                "bsdutils=1:2.34-0.1ubuntu9.1," "util-linux=2.34-0.1ubuntu9.1",
                "bzip2=1.0.8-2,bzip2=1.0.8-2",
                "coreutils=8.30-3ubuntu2," "coreutils=8.30-3ubuntu2",
                "dash=0.5.10.2-6,dash=0.5.10.2-6",
                "debconf=1.5.73,debconf=1.5.73",
                "debianutils=4.9.1,debianutils=4.9.1",
                "diffutils=1:3.7-3,diffutils=1:3.7-3",
                "dpkg=1.19.7ubuntu3,dpkg=1.19.7ubuntu3",
                "e2fsprogs=1.45.5-2ubuntu1," "e2fsprogs=1.45.5-2ubuntu1",
                "fdisk=2.34-0.1ubuntu9.1," "util-linux=2.34-0.1ubuntu9.1",
                "findutils=4.7.0-1ubuntu1," "findutils=4.7.0-1ubuntu1",
                "gcc-10-base:amd64=10.2.0-5ubuntu1~20.04,"
                "gcc-10=10.2.0-5ubuntu1~20.04",
                "gpgv=2.2.19-3ubuntu2,gnupg2=2.2.19-3ubuntu2",
                "grep=3.4-1,grep=3.4-1",
                "gzip=1.10-0ubuntu4,gzip=1.10-0ubuntu4",
                "hostname=3.23,hostname=3.23",
                "init-system-helpers=1.57," "init-system-helpers=1.57",
                "libacl1:amd64=2.2.53-6,acl=2.2.53-6",
                "libapt-pkg6.0:amd64=2.0.2ubuntu0.2," "apt=2.0.2ubuntu0.2",
                "libatomic1:amd64=10.2.0-5ubuntu1~20.04,"
                "gcc-10=10.2.0-5ubuntu1~20.04",
                "libattr1:amd64=1:2.4.48-5,attr=1:2.4.48-5",
                "libaudit-common=1:2.8.5-2ubuntu6," "audit=1:2.8.5-2ubuntu6",
                "libaudit1:amd64=1:2.8.5-2ubuntu6," "audit=1:2.8.5-2ubuntu6",
                "libblkid1:amd64=2.34-0.1ubuntu9.1," "util-linux=2.34-0.1ubuntu9.1",
                "libbz2-1.0:amd64=1.0.8-2,bzip2=1.0.8-2",
                "libc-bin=2.31-0ubuntu9.1," "glibc=2.31-0ubuntu9.1",
                "libc6:amd64=2.31-0ubuntu9.1," "glibc=2.31-0ubuntu9.1",
                "libcap-ng0:amd64=0.7.9-2.1build1," "libcap-ng=0.7.9-2.1build1",
                "libcom-err2:amd64=1.45.5-2ubuntu1," "e2fsprogs=1.45.5-2ubuntu1",
                "libcrypt1:amd64=1:4.4.10-10ubuntu4," "libxcrypt=1:4.4.10-10ubuntu4",
                "libdb5.3:amd64=5.3.28+dfsg1-0.6ubuntu2,"
                "db5.3=5.3.28+dfsg1-0.6ubuntu2",
                "libdebconfclient0:amd64=0.251ubuntu1," "cdebconf=0.251ubuntu1",
                "libext2fs2:amd64=1.45.5-2ubuntu1," "e2fsprogs=1.45.5-2ubuntu1",
                "libfdisk1:amd64=2.34-0.1ubuntu9.1," "util-linux=2.34-0.1ubuntu9.1",
                "libffi7:amd64=3.3-4,libffi=3.3-4",
                "libgcc-s1:amd64=10.2.0-5ubuntu1~20.04," "gcc-10=10.2.0-5ubuntu1~20.04",
                "libgcrypt20:amd64=1.8.5-5ubuntu1," "libgcrypt20=1.8.5-5ubuntu1",
                "libgmp10:amd64=2:6.2.0+dfsg-4," "gmp=2:6.2.0+dfsg-4",
                "libgnutls30:amd64=3.6.13-2ubuntu1.3," "gnutls28=3.6.13-2ubuntu1.3",
                "libgpg-error0:amd64=1.37-1," "libgpg-error=1.37-1",
                "libhiredis0.14:amd64=0.14.0-6," "hiredis=0.14.0-6",
                "libhogweed5:amd64=3.5.1+really3.5.1-2," "nettle=3.5.1+really3.5.1-2",
                "libidn2-0:amd64=2.2.0-2,libidn2=2.2.0-2",
                "libjemalloc2:amd64=5.2.1-1ubuntu1," "jemalloc=5.2.1-1ubuntu1",
                "liblua5.1-0:amd64=5.1.5-8.1build4," "lua5.1=5.1.5-8.1build4",
                "liblz4-1:amd64=1.9.2-2,lz4=1.9.2-2",
                "liblzma5:amd64=5.2.4-1ubuntu1," "xz-utils=5.2.4-1ubuntu1",
                "libmount1:amd64=2.34-0.1ubuntu9.1," "util-linux=2.34-0.1ubuntu9.1",
                "libncurses6:amd64=6.2-0ubuntu2," "ncurses=6.2-0ubuntu2",
                "libncursesw6:amd64=6.2-0ubuntu2," "ncurses=6.2-0ubuntu2",
                "libnettle7:amd64=3.5.1+really3.5.1-2," "nettle=3.5.1+really3.5.1-2",
                "libp11-kit0:amd64=0.23.20-1build1," "p11-kit=0.23.20-1build1",
                "libpam-modules:amd64=1.3.1-5ubuntu4.1," "pam=1.3.1-5ubuntu4.1",
                "libpam-modules-bin=1.3.1-5ubuntu4.1," "pam=1.3.1-5ubuntu4.1",
                "libpam-runtime=1.3.1-5ubuntu4.1," "pam=1.3.1-5ubuntu4.1",
                "libpam0g:amd64=1.3.1-5ubuntu4.1," "pam=1.3.1-5ubuntu4.1",
                "libpcre2-8-0:amd64=10.34-7,pcre2=10.34-7",
                "libpcre3:amd64=2:8.39-12build1," "pcre3=2:8.39-12build1",
                "libprocps8:amd64=2:3.3.16-1ubuntu2," "procps=2:3.3.16-1ubuntu2",
                "libseccomp2:amd64=2.4.3-1ubuntu3.20.04.3,"
                "libseccomp=2.4.3-1ubuntu3.20.04.3",
                "libselinux1:amd64=3.0-1build2,libselinux=3.0-1build2",
                "libsemanage-common=3.0-1build2,libsemanage=3.0-1build2",
                "libsemanage1:amd64=3.0-1build2,libsemanage=3.0-1build2",
                "libsepol1:amd64=3.0-1,libsepol=3.0-1",
                "libsmartcols1:amd64=2.34-0.1ubuntu9.1,util-linux=2.34-0.1ubuntu9.1",
                "libss2:amd64=1.45.5-2ubuntu1,e2fsprogs=1.45.5-2ubuntu1",
                "libstdc++6:amd64=10.2.0-5ubuntu1~20.04,gcc-10=10.2.0-5ubuntu1~20.04",
                "libsystemd0:amd64=245.4-4ubuntu3.3,systemd=245.4-4ubuntu3.3",
                "libtasn1-6:amd64=4.16.0-2,libtasn1-6=4.16.0-2",
                "libtinfo6:amd64=6.2-0ubuntu2,ncurses=6.2-0ubuntu2",
                "libudev1:amd64=245.4-4ubuntu3.3,systemd=245.4-4ubuntu3.3",
                "libunistring2:amd64=0.9.10-2,libunistring=0.9.10-2",
                "libuuid1:amd64=2.34-0.1ubuntu9.1,util-linux=2.34-0.1ubuntu9.1",
                "libxcursor1=4.0.0-2,tiff=4.0.0-2",
                "libzstd1:amd64=1.4.4+dfsg-3,libzstd=1.4.4+dfsg-3",
                "login=1:4.8.1-1ubuntu5.20.04,shadow=1:4.8.1-1ubuntu5.20.04",
                "logsave=1.45.5-2ubuntu1,e2fsprogs=1.45.5-2ubuntu1",
                "lsb-base=11.1.0ubuntu2,lsb=11.1.0ubuntu2",
                "lua-bitop:amd64=1.0.2-5,lua-bitop=1.0.2-5",
                "lua-cjson:amd64=2.1.0+dfsg-2.1,lua-cjson=2.1.0+dfsg-2.1",
                "mawk=1.3.4.20200120-2,mawk=1.3.4.20200120-2",
                "mount=2.34-0.1ubuntu9.1,util-linux=2.34-0.1ubuntu9.1",
                "ncurses-base=6.2-0ubuntu2,ncurses=6.2-0ubuntu2",
                "ncurses-bin=6.2-0ubuntu2,ncurses=6.2-0ubuntu2",
                "passwd=1:4.8.1-1ubuntu5.20.04,shadow=1:4.8.1-1ubuntu5.20.04",
                "perl-base=5.30.0-9ubuntu0.2,perl=5.30.0-9ubuntu0.2",
                "procps=2:3.3.16-1ubuntu2,procps=2:3.3.16-1ubuntu2",
                "pwgen=2.08-2,pwgen=2.08-2",
                "redis-server=5:5.0.7-2,redis=5:5.0.7-2",
                "redis-tools=5:5.0.7-2,redis=5:5.0.7-2",
                "sed=4.7-1,sed=4.7-1",
                "sensible-utils=0.0.12+nmu1,sensible-utils=0.0.12+nmu1",
                "sysvinit-utils=2.96-2.1ubuntu1,sysvinit=2.96-2.1ubuntu1",
                "tar=1.30+dfsg-7,tar=1.30+dfsg-7",
                "tzdata=2020d-0ubuntu0.20.04,tzdata=2020d-0ubuntu0.20.04",
                "ubuntu-keyring=2020.02.11.2,ubuntu-keyring=2020.02.11.2",
                "util-linux=2.34-0.1ubuntu9.1,util-linux=2.34-0.1ubuntu9.1",
                "zlib1g:amd64=1:1.2.11.dfsg-2ubuntu1.2,zlib=1:1.2.11.dfsg-2ubuntu1.2",
            ],
        }
        self.assertDictEqual(
            expected_manifest_yaml, reviewtools.common.get_rock_manifest(valid_rock_fn)
        )

    def test_get_rock_manifest_invalid_rock(self):
        """Test get_rock_manifest() - invalid rock tar"""
        invalid_rock_fn = "./tests/invalid_rock_multiple_layer_tar_archives.tar"
        with self.assertRaises(ReviewException) as e:
            reviewtools.common.get_rock_manifest(invalid_rock_fn)
        self.assertEqual(
            e.exception.value,
            "Unexpected number of layer tar archives inside layer directory: 2",
        )
