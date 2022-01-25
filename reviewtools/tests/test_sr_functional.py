"""test_sr_functional.py: tests for the sr_functional module"""
#
# Copyright (C) 2017-2020 Canonical Ltd.
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
import copy
import os
import shutil
import tempfile

from reviewtools.common import cleanup_unpack
from reviewtools.common import check_results as common_check_results
from reviewtools.sr_functional import SnapReviewFunctional
import reviewtools.sr_tests as sr_tests
from reviewtools.tests import utils
from reviewtools.common import STATE_FORMAT_VERSION, StatLLN, cmd, unsquashfs_lln_parse


class TestSnapReviewFunctional(sr_tests.TestSnapReview):
    """Tests for the functional lint review tool."""

    def setUp(self):
        super().setUp()
        self.set_test_pkgfmt("snap", "16.04")
        # ["all"] is the default in sr_tests.py
        self.state_files_key = "functional-snap-v2:state_files:all"

    def tearDown(self):
        super().setUp()
        self.set_test_pkgfmt("snap", "16.04")
        if "SNAP_FORCE_STATE_CHECK" in os.environ:
            del os.environ["SNAP_FORCE_STATE_CHECK"]

    def _set_unsquashfs_lln(self, out):
        header = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

"""
        hdr, entries = unsquashfs_lln_parse(header + out)
        self.set_test_unsquashfs_lln(hdr, entries)

    def _set_default_state(self):
        self.set_test_unpack_dir = "/nonexistent"
        lln = """drwxr-xr-x 0/0               215 2020-03-23 14:23 squashfs-root
drwxr-xr-x 0/0                73 2020-03-23 14:23 squashfs-root/bin
-rwxr-xr-x 0/0             43416 2020-03-23 14:23 squashfs-root/bin/cat
-rw-r--r-- 0/0            584392 2020-03-23 14:23 squashfs-root/lib/some.so
"""
        self._set_unsquashfs_lln(lln)

        exp_state = {
            ".": {
                StatLLN.FILENAME: ".",
                StatLLN.FULLNAME: "squashfs-root",
                StatLLN.FILETYPE: "d",
                StatLLN.MODE: "rwxr-xr-x",
                StatLLN.OWNER: "0/0",
                StatLLN.UID: "0",
                StatLLN.GID: "0",
                StatLLN.SIZE: "215",
                StatLLN.DATE: "2020-03-23",
                StatLLN.TIME: "14:23",
            },
            "./bin": {
                StatLLN.FILENAME: "./bin",
                StatLLN.FULLNAME: "squashfs-root/bin",
                StatLLN.FILETYPE: "d",
                StatLLN.MODE: "rwxr-xr-x",
                StatLLN.OWNER: "0/0",
                StatLLN.UID: "0",
                StatLLN.GID: "0",
                StatLLN.SIZE: "73",
                StatLLN.DATE: "2020-03-23",
                StatLLN.TIME: "14:23",
            },
            "./bin/cat": {
                StatLLN.FILENAME: "./bin/cat",
                StatLLN.FULLNAME: "squashfs-root/bin/cat",
                StatLLN.FILETYPE: "-",
                StatLLN.MODE: "rwxr-xr-x",
                StatLLN.OWNER: "0/0",
                StatLLN.UID: "0",
                StatLLN.GID: "0",
                StatLLN.SIZE: "43416",
                StatLLN.DATE: "2020-03-23",
                StatLLN.TIME: "14:23",
            },
            "./lib/some.so": {
                StatLLN.FILENAME: "./lib/some.so",
                StatLLN.FULLNAME: "squashfs-root/lib/some.so",
                StatLLN.FILETYPE: "-",
                StatLLN.MODE: "rw-r--r--",
                StatLLN.OWNER: "0/0",
                StatLLN.UID: "0",
                StatLLN.GID: "0",
                StatLLN.SIZE: "584392",
                StatLLN.DATE: "2020-03-23",
                StatLLN.TIME: "14:23",
                "symbols": {
                    "foo": {"type": "T", "version": "@@Base"},
                    "bar": {"type": "T", "version": "@@Base"},
                },
            },
        }

        exp_override_state = copy.deepcopy(exp_state)
        # these fields aren't stored in state files
        for fname in exp_override_state:
            for k in [
                StatLLN.FULLNAME,
                StatLLN.UID,
                StatLLN.GID,
                StatLLN.SIZE,
                StatLLN.DATE,
                StatLLN.TIME,
            ]:
                del exp_override_state[fname][k]

        exp_override = {
            ".": {"filetype": "d", "mode": "rwxr-xr-x", "owner": "0/0"},
            "./bin": {"filetype": "d", "mode": "rwxr-xr-x", "owner": "0/0"},
            "./bin/cat": {"filetype": "-", "mode": "rwxr-xr-x", "owner": "0/0"},
            "./lib/some.so": {
                "filetype": "-",
                "mode": "rw-r--r--",
                "owner": "0/0",
                "symbols": {
                    "foo": {"type": "T", "version": "@@Base"},
                    "bar": {"type": "T", "version": "@@Base"},
                },
            },
        }
        self.set_test_cmd_nm(
            0,
            """000000000000089a T foo@@Base
0000000000000708 T bar@@Base""",
        )

        return exp_state, exp_override, exp_override_state

    def test_all_checks_as_v2(self):
        """Test snap v2 has checks"""
        self.set_test_pkgfmt("snap", "16.04")
        c = SnapReviewFunctional(self.test_name)
        c.do_checks()
        sum = 0
        for i in c.review_report:
            sum += len(c.review_report[i])
        self.assertTrue(sum != 0)

    def test_find_symbols_good(self):
        """Test _find_symbols()"""
        self.set_test_cmd_nm(
            0,
            """00000000000559f0 T a64l@@GLIBC_2.2.5
00000000001ed920 B __abort_msg@@GLIBC_PRIVATE
00000000001eeb20 V __after_morecore_hook@@GLIBC_2.2.5
0000000000049830 W clearenv@@GLIBC_2.2.5
00000000001eb700 D __ctype32_b@GLIBC_2.2.5
00000000001ed920 B foo@@Base
0000000000000000 A CXXABI_1.3@@CXXABI_1.3
00000000000a8e90 T operator delete[](void*)@@GLIBCXX_3.4
00000000000a9b70 T __gxx_personality_v0@@CXXABI_1.3
00000000000d15f0 T transaction clone for std::logic_error::~logic_error()@@GLIBCXX_3.4.22
""",
        )

        c = SnapReviewFunctional(self.test_name)
        res = c._find_symbols("./foo.so")
        self.assertEqual(len(res), 10)
        for symbol, symbol_type, symbol_version in [
            ("a64l", "T", "@@GLIBC_2.2.5"),
            ("__abort_msg", "B", "@@GLIBC_PRIVATE"),
            ("__after_morecore_hook", "V", "@@GLIBC_2.2.5"),
            ("clearenv", "W", "@@GLIBC_2.2.5"),
            ("__ctype32_b", "D", "@GLIBC_2.2.5"),
            ("foo", "B", "@@Base"),
            ("CXXABI_1.3", "A", "@@CXXABI_1.3"),
            ("operator delete[](void*)", "T", "@@GLIBCXX_3.4"),
            ("__gxx_personality_v0", "T", "@@CXXABI_1.3"),
            (
                "transaction clone for std::logic_error::~logic_error()",
                "T",
                "@@GLIBCXX_3.4.22",
            ),
        ]:
            self.assertTrue(symbol in res)
            self.assertEqual(symbol_type, res[symbol]["type"])
            self.assertEqual(symbol_version, res[symbol]["version"])

    def test_find_symbols_skipped(self):
        """Test _find_symbols() - debug"""
        self.set_test_cmd_nm(
            0,
            """00000000001eb700 N foo@@Base
00000000001eb700 U bar@@Base
""",
        )
        c = SnapReviewFunctional(self.test_name)
        res = c._find_symbols("./foo.so")
        # debug symbols should be skipped
        self.assertEqual(len(res), 0)

    def test_find_symbols_cpp_demangled(self):
        """Test _find_symbols() - c++ demangled"""
        self.set_test_cmd_nm(
            0,
            """00000000000d15f0 T transaction clone for std::logic_error::~logic_error()@@GLIBCXX_3.4.22
00000000000d15d0 T transaction clone for std::logic_error::~logic_error()@@GLIBCXX_3.4.22
00000000000d15d0 T transaction clone for std::logic_error::~logic_error()@@GLIBCXX_3.4.22
00000000000aae00 T __cxxabiv1::__pbase_type_info::~__pbase_type_info()@@CXXABI_1.3
00000000000aade0 T __cxxabiv1::__pbase_type_info::~__pbase_type_info()@@CXXABI_1.3
00000000000aade0 T __cxxabiv1::__pbase_type_info::~__pbase_type_info()@@CXXABI_1.3
""",
        )
        c = SnapReviewFunctional(self.test_name)
        res = c._find_symbols("./foo.so")
        self.assertEqual(len(res), 2)
        for symbol, symbol_type, symbol_version in [
            (
                "transaction clone for std::logic_error::~logic_error()",
                "T",
                "@@GLIBCXX_3.4.22",
            ),
            (
                "__cxxabiv1::__pbase_type_info::~__pbase_type_info()",
                "T",
                "@@CXXABI_1.3",
            ),
        ]:
            self.assertTrue(symbol in res)
            self.assertEqual(symbol_type, res[symbol]["type"])
            self.assertEqual(symbol_version, res[symbol]["version"])

    def test_find_symbols_bad_rc(self):
        """Test _find_symbols() - bad rc"""
        self.set_test_cmd_nm(-1, "error")
        c = SnapReviewFunctional(self.test_name)
        res = c._find_symbols("./foo.so")
        self.assertTrue(res is None)

    def test_find_symbols_bad_file(self):
        """Test _find_symbols() - bad file"""
        c = SnapReviewFunctional(self.test_name)
        res = c._find_symbols("blah")
        print(res)
        self.assertTrue(res is None)

    def test_find_symbols_bad_result(self):
        """Test _find_symbols() - bad result"""
        self.set_test_cmd_nm(0, "000000000000089a T")
        c = SnapReviewFunctional(self.test_name)
        res = c._find_symbols("./foo.so")
        self.assertEqual(len(res), 0)

    def test__serialize(self):
        """Test _serialize()"""
        # convenient way to get a list of items
        lln = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

drwxr-xr-x 0/0               215 2020-03-23 14:32 squashfs-root
drwxr-xr-x 0/0                73 2020-03-23 14:23 squashfs-root/bin
-rwxr-xr-x 0/0             43416 2020-03-23 14:23 squashfs-root/bin/cat
drwxr-xr-x 0/0               181 2020-03-23 14:27 squashfs-root/lib/x86_64-linux-gnu
-rwxr-xr-x 0/0           2029224 2020-03-23 14:24 squashfs-root/lib/x86_64-linux-gnu/libc-2.31.so
lrwxrwxrwx 0/0                12 2020-03-14 18:21 squashfs-root/lib/x86_64-linux-gnu/libc.so.6 -> libc-2.31.so
crw-rw-rw- 0/0             1,  3 2020-03-14 18:21 squashfs-root/dev/null
"""
        hdr, entries = unsquashfs_lln_parse(lln)

        state = {}
        for (line, item) in entries:
            state[item[StatLLN.FILENAME]] = item
            if "libc-2.31.so" in line:
                state[item[StatLLN.FILENAME]]["symbols"] = {
                    "GLIBC_2.10": {"type": "A", "version": "@@GLIBC_2.10"},
                    "GLIBC_2.11": {"type": "A", "version": "@@GLIBC_2.10"},
                }

        c = SnapReviewFunctional(self.test_name)
        serial = c._serialize(state)

        self.assertEqual(len(entries), len(serial))
        self.assertEqual(len(serial), 7)
        for (idx, map) in [
            (".", {"filetype": "d", "mode": "rwxr-xr-x", "owner": "0/0"}),
            ("./bin", {"filetype": "d", "mode": "rwxr-xr-x", "owner": "0/0"}),
            ("./bin/cat", {"filetype": "-", "mode": "rwxr-xr-x", "owner": "0/0"}),
            (
                "./lib/x86_64-linux-gnu",
                {"filetype": "d", "mode": "rwxr-xr-x", "owner": "0/0"},
            ),
            (
                "./lib/x86_64-linux-gnu/libc-2.31.so",
                {
                    "filetype": "-",
                    "mode": "rwxr-xr-x",
                    "owner": "0/0",
                    "symbols": {
                        "GLIBC_2.10": {"type": "A", "version": "@@GLIBC_2.10"},
                        "GLIBC_2.11": {"type": "A", "version": "@@GLIBC_2.10"},
                    },
                },
            ),
            (
                "./lib/x86_64-linux-gnu/libc.so.6 -> libc-2.31.so",
                {"filetype": "l", "mode": "rwxrwxrwx", "owner": "0/0"},
            ),
            (
                "./dev/null",
                {
                    "filetype": "c",
                    "mode": "rw-rw-rw-",
                    "owner": "0/0",
                    "major": "1",
                    "minor": "3",
                },
            ),
        ]:
            self.assertTrue(idx in serial)
            for k in map:
                self.assertTrue(k in serial[idx])
                self.assertEqual(serial[idx][k], map[k])

    def test__serialize_bad_item(self):
        """Test _serialize() - bad item"""
        # mock a bad entry
        entries = [
            # one bad missing StatLLN.OWNER
            (
                "-rwxr-xr-x 0/0             43416 2020-03-23 14:23 squashfs-root/bin/cat",
                {
                    StatLLN.FILENAME: "./bin/cat",
                    StatLLN.FILETYPE: "-",
                    StatLLN.MODE: "rwxr-xr-x",
                },
            ),
            # another badly formatted
            (
                "-rwxr-xr-x 0/0             43416 2020-03-23 14:23 squashfs-root/bin/cp",
                {
                    StatLLN.FILENAME: "./bin/cp",
                    StatLLN.FILETYPE: "-",
                    StatLLN.MODE: [],
                    StatLLN.OWNER: "0/0",
                },
            ),
            # one good but with one bad symbol
            (
                "-rwxr-xr-x 0/0           2029224 2020-03-23 14:24 squashfs-root/lib/x86_64-linux-gnu/libc-2.31.so",
                {
                    StatLLN.FILENAME: "./lib/x86_64-linux-gnu/libc-2.31.so",
                    StatLLN.FILETYPE: "-",
                    StatLLN.MODE: "rwxr-xr-x",
                    StatLLN.OWNER: "0/0",
                    "symbols": {
                        "foo": {"type": "T", "version": "@@Base"},
                        "bad": {"type": [], "version": "@@Base"},
                    },
                },
            ),
        ]
        c = SnapReviewFunctional(self.test_name)

        state = {}
        for (line, item) in entries:
            state[item[StatLLN.FILENAME]] = item

        serial = c._serialize(state)

        self.assertEqual(len(serial), 1)
        self.assertTrue("./bin/cat" not in serial)
        self.assertTrue("./bin/cp" not in serial)
        idx = "./lib/x86_64-linux-gnu/libc-2.31.so"
        map = {
            "filetype": "-",
            "mode": "rwxr-xr-x",
            "owner": "0/0",
            "symbols": {"foo": {"type": "T", "version": "@@Base"}},
        }
        self.assertTrue(idx in serial)
        for k in map:
            self.assertTrue(k in serial[idx])
            self.assertEqual(serial[idx][k], map[k])

    def test__deserialize(self):
        """Test _deserialize()"""
        # convenient way to get a list of items
        lln = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

drwxr-xr-x 0/0               215 2020-03-23 14:32 squashfs-root
drwxr-xr-x 0/0                73 2020-03-23 14:23 squashfs-root/bin
-rwxr-xr-x 0/0             43416 2020-03-23 14:23 squashfs-root/bin/cat
drwxr-xr-x 0/0               181 2020-03-23 14:27 squashfs-root/lib/x86_64-linux-gnu
-rwxr-xr-x 0/0           2029224 2020-03-23 14:24 squashfs-root/lib/x86_64-linux-gnu/libc-2.31.so
lrwxrwxrwx 0/0                12 2020-03-14 18:21 squashfs-root/lib/x86_64-linux-gnu/libc.so.6 -> libc-2.31.so
crw-rw-rw- 0/0             1,  3 2020-03-14 18:21 squashfs-root/dev/null
"""
        hdr, entries = unsquashfs_lln_parse(lln)

        serial = {
            ".": {"filetype": "d", "mode": "rwxr-xr-x", "owner": "0/0"},
            "./bin": {"filetype": "d", "mode": "rwxr-xr-x", "owner": "0/0"},
            "./bin/cat": {"filetype": "-", "mode": "rwxr-xr-x", "owner": "0/0"},
            "./dev/null": {
                "filetype": "c",
                "major": "1",
                "minor": "3",
                "mode": "rw-rw-rw-",
                "owner": "0/0",
            },
            "./lib/x86_64-linux-gnu": {
                "filetype": "d",
                "mode": "rwxr-xr-x",
                "owner": "0/0",
            },
            "./lib/x86_64-linux-gnu/libc-2.31.so": {
                "filetype": "-",
                "mode": "rwxr-xr-x",
                "owner": "0/0",
                "symbols": {
                    "GLIBC_2.10": {"type": "A", "version": "@@GLIBC_2.10"},
                    "GLIBC_2.11": {"type": "A", "version": "@@GLIBC_2.10"},
                },
            },
            "./lib/x86_64-linux-gnu/libc.so.6 -> libc-2.31.so": {
                "filetype": "l",
                "mode": "rwxrwxrwx",
                "owner": "0/0",
            },
        }

        c = SnapReviewFunctional(self.test_name)
        state = c._deserialize(serial)
        self.assertEqual(len(state), len(entries))
        self.assertEqual(len(state), 7)

        for (idx, item) in [
            (
                ".",
                {
                    StatLLN.FILENAME: ".",
                    StatLLN.FILETYPE: "d",
                    StatLLN.MODE: "rwxr-xr-x",
                    StatLLN.OWNER: "0/0",
                },
            ),
            (
                "./bin",
                {
                    StatLLN.FILENAME: "./bin",
                    StatLLN.FILETYPE: "d",
                    StatLLN.MODE: "rwxr-xr-x",
                    StatLLN.OWNER: "0/0",
                },
            ),
            (
                "./bin/cat",
                {
                    StatLLN.FILENAME: "./bin/cat",
                    StatLLN.FILETYPE: "-",
                    StatLLN.MODE: "rwxr-xr-x",
                    StatLLN.OWNER: "0/0",
                },
            ),
            (
                "./lib/x86_64-linux-gnu",
                {
                    StatLLN.FILENAME: "./lib/x86_64-linux-gnu",
                    StatLLN.FILETYPE: "d",
                    StatLLN.MODE: "rwxr-xr-x",
                    StatLLN.OWNER: "0/0",
                },
            ),
            (
                "./lib/x86_64-linux-gnu/libc-2.31.so",
                {
                    StatLLN.FILENAME: "./lib/x86_64-linux-gnu/libc-2.31.so",
                    StatLLN.FILETYPE: "-",
                    StatLLN.MODE: "rwxr-xr-x",
                    StatLLN.OWNER: "0/0",
                    "symbols": {
                        "GLIBC_2.10": {"type": "A", "version": "@@GLIBC_2.10"},
                        "GLIBC_2.11": {"type": "A", "version": "@@GLIBC_2.10"},
                    },
                },
            ),
            (
                "./lib/x86_64-linux-gnu/libc.so.6 -> libc-2.31.so",
                {
                    StatLLN.FILENAME: "./lib/x86_64-linux-gnu/libc.so.6 -> libc-2.31.so",
                    StatLLN.FILETYPE: "l",
                    StatLLN.MODE: "rwxrwxrwx",
                    StatLLN.OWNER: "0/0",
                },
            ),
            (
                "./dev/null",
                {
                    StatLLN.FILENAME: "./dev/null",
                    StatLLN.FILETYPE: "c",
                    StatLLN.MODE: "rw-rw-rw-",
                    StatLLN.OWNER: "0/0",
                    StatLLN.MAJOR: "1",
                    StatLLN.MINOR: "3",
                },
            ),
        ]:
            self.assertTrue(idx in state)
            for k in item:
                self.assertTrue(k in state[idx])
                self.assertEqual(state[idx][k], item[k])

    def test__deserialize_bad_entry(self):
        """Test _serialize() - bad entry"""
        serial = {
            "./bin": {},
            ".": {"filetype": "d", "mode": "rwxr-xr-x", "owner": "0/0"},
            "./bad": {"filetype": "-", "mode": [], "owner": "0/0"},
        }

        c = SnapReviewFunctional(self.test_name)
        state = c._deserialize(serial)
        self.assertEqual(len(state), 1)

        self.assertTrue("./bin" not in state)
        self.assertTrue("./bad" not in state)
        fname = "."
        exp = {
            fname: {
                StatLLN.FILENAME: fname,
                StatLLN.FILETYPE: "d",
                StatLLN.MODE: "rwxr-xr-x",
                StatLLN.OWNER: "0/0",
            }
        }
        self.assertTrue(fname in state)
        self.assertEqual(len(exp[fname]), len(state[fname]))
        for k in exp[fname]:
            self.assertTrue(k in state[fname])
            self.assertEqual(exp[fname][k], state[fname][k])

    def test__deserialize_bad_symbol(self):
        """Test _serialize() - bad symbol"""
        serial = {
            "./lib.so": {
                "filetype": "-",
                "mode": "rw-r--r--",
                "owner": "0/0",
                "symbols": {
                    "foo": {"type": "T", "version": []},
                    "bar": {"type": "T", "version": "@@Base"},
                },
            }
        }

        c = SnapReviewFunctional(self.test_name)
        state = c._deserialize(serial)
        self.assertEqual(len(state), 1)

        fname = "./lib.so"
        exp = {
            fname: {
                StatLLN.FILENAME: fname,
                StatLLN.FILETYPE: "-",
                StatLLN.MODE: "rw-r--r--",
                StatLLN.OWNER: "0/0",
                "symbols": {"bar": {"type": "T", "version": "@@Base"}},
            }
        }
        self.assertTrue(fname in state)
        self.assertEqual(len(exp[fname]), len(state[fname]))
        for k in exp[fname]:
            self.assertTrue(k in state[fname])
            self.assertEqual(exp[fname][k], state[fname][k])

    def test_serialize_deserialize_roundtrip(self):
        """Test serialize()/deserialize() round trip"""
        serial = {
            ".": {"filetype": "d", "mode": "rwxr-xr-x", "owner": "0/0"},
            "./bin": {"filetype": "d", "mode": "rwxr-xr-x", "owner": "0/0"},
            "./bin/cat": {"filetype": "-", "mode": "rwxr-xr-x", "owner": "0/0"},
            "./dev/null": {
                "filetype": "c",
                "major": "1",
                "minor": "3",
                "mode": "rw-rw-rw-",
                "owner": "0/0",
            },
            "./lib/x86_64-linux-gnu": {
                "filetype": "d",
                "mode": "rwxr-xr-x",
                "owner": "0/0",
            },
            "./lib/x86_64-linux-gnu/libc-2.31.so": {
                "filetype": "-",
                "mode": "rwxr-xr-x",
                "owner": "0/0",
            },
            "./lib/x86_64-linux-gnu/libc.so.6 -> libc-2.31.so": {
                "filetype": "l",
                "mode": "rwxrwxrwx",
                "owner": "0/0",
            },
            "./😃": {"filetype": "-", "mode": "rw-r--r--", "owner": "0/0"},
        }

        c = SnapReviewFunctional(self.test_name)
        state = c._deserialize(serial)
        self.assertEqual(len(state), len(serial))

        serial2 = c._serialize(state)
        self.assertEqual(len(serial2), len(serial))

        state2 = c._deserialize(serial2)
        self.assertEqual(len(state2), len(serial))

        for j in serial:
            self.assertTrue(j in serial2)
            self.assertTrue(len(serial[j]), len(serial2[j]))
            for k in serial[j]:
                self.assertTrue(k in serial2[j])
                self.assertEqual(serial[j][k], serial2[j][k])

    def test_check_state_base_files_app(self):
        """Test check_state_base_files() - app"""
        self._set_default_state()

        c = SnapReviewFunctional(self.test_name)
        c.check_state_base_files()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        # verify prev_state not set
        self.assertTrue(c.prev_state is None)

        # verify curr_state not set
        self.assertTrue(c.curr_state is None)

        # verify state_input not set
        self.assertFalse("state_input" in c.overrides)

        # verify state_output not set
        self.assertFalse("state_output" in c.overrides)

    def test_check_state_base_files_app_output(self):
        """Test check_state_base_files() - --state-output (app)"""
        self._set_default_state()

        overrides = {
            "state_input": {"format": STATE_FORMAT_VERSION},
            "state_output": {"format": STATE_FORMAT_VERSION},
        }
        c = SnapReviewFunctional(self.test_name, overrides=overrides)
        c.check_state_base_files()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        # verify prev_state not set
        self.assertTrue(c.prev_state is None)

        # verify curr_state not set
        self.assertTrue(c.curr_state is None)

        # verify state_input not set
        self.assertFalse(self.state_files_key in c.overrides["state_input"])

        # verify state_output not set
        self.assertFalse(self.state_files_key in c.overrides["state_output"])

    def test_check_state_base_files_app_input_output(self):
        """Test check_state_base_files() - --state-input/--state-output (app)"""
        self._set_default_state()

        overrides = {
            "state_input": {"format": STATE_FORMAT_VERSION, "something": "else"},
            "state_output": {"format": STATE_FORMAT_VERSION},
        }
        c = SnapReviewFunctional(self.test_name, overrides=overrides)
        c.check_state_base_files()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        # verify prev_state not set
        self.assertTrue(c.prev_state is None)

        # verify curr_state not set
        self.assertTrue(c.curr_state is None)

        # verify state_input not set
        self.assertFalse(self.state_files_key in c.overrides["state_input"])

        # verify state_output not set
        self.assertFalse(self.state_files_key in c.overrides["state_output"])

    def test_check_state_base_files_no_state(self):
        """Test check_state_base_files() - no state"""
        os.environ["SNAP_FORCE_STATE_CHECK"] = "1"
        self._set_default_state()

        self.set_test_snap_yaml("type", "base")
        c = SnapReviewFunctional(self.test_name)
        c.check_state_base_files()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        # verify prev_state not set
        self.assertTrue(c.prev_state is None)

        # verify curr_state not set
        self.assertTrue(c.curr_state is None)

        # verify state_input not set
        self.assertFalse("state_input" in c.overrides)

        # verify state_output not set
        self.assertFalse("state_output" in c.overrides)

    def test_check_state_base_files_output(self):
        """Test check_state_base_files() - --state-output"""
        os.environ["SNAP_FORCE_STATE_CHECK"] = "1"
        exp_state, exp_override, exp_override_state = self._set_default_state()

        self.set_test_snap_yaml("type", "base")
        overrides = {
            "state_input": {"format": STATE_FORMAT_VERSION},
            "state_output": {"format": STATE_FORMAT_VERSION},
        }
        c = SnapReviewFunctional(self.test_name, overrides=overrides)
        c.check_state_base_files()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "functional-snap-v2:state_base_files"
        expected["info"][name] = {"text": "OK (no previous state)"}
        self.check_results(report, expected=expected)

        # verify prev_state is empty
        self.assertEqual(c.prev_state, {})

        # verify curr_state has expected state
        self.assertEqual(c.curr_state, exp_state)

        # verify state_input is not set
        self.assertFalse(self.state_files_key in c.overrides["state_input"])

        # verify state_output is set
        self.assertTrue(self.state_files_key in c.overrides["state_output"])
        self.assertEqual(
            c.overrides["state_output"][self.state_files_key], exp_override
        )

    def test_check_state_base_files_output_base_not_overridden(self):
        """Test check_state_base_files() - --state-output and base not
           overridden
        """
        os.environ["SNAP_FORCE_STATE_CHECK"] = "0"
        exp_state, exp_override, exp_override_state = self._set_default_state()

        self.set_test_snap_yaml("type", "base")
        overrides = {
            "state_input": {"format": STATE_FORMAT_VERSION},
            "state_output": {"format": STATE_FORMAT_VERSION},
        }
        c = SnapReviewFunctional(self.test_name, overrides=overrides)
        c.check_state_base_files()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "functional-snap-v2:state_base_files"
        expected["info"][name] = {
            "text": "OK (skipped, snap type not overridden for this snap)"
        }
        self.check_results(report, expected=expected)

        # verify prev_state is empty
        self.assertEqual(c.prev_state, {})

        # verify curr_state has expected state
        self.assertEqual(c.curr_state, exp_state)

        # verify state_input is not set
        self.assertFalse(self.state_files_key in c.overrides["state_input"])

        # verify state_output is not state
        self.assertFalse(self.state_files_key in c.overrides["state_output"])

    def test_check_state_base_files_input_output_base_not_overridden(self):
        """Test check_state_base_files() - --state-input/--state-output and
           base not overridden
        """
        os.environ["SNAP_FORCE_STATE_CHECK"] = "0"
        exp_state, exp_override, exp_override_state = self._set_default_state()
        prev_override = copy.deepcopy(exp_override)
        prev_override["./bin/ls"] = {
            "filetype": "-",
            "mode": "rwxr-xr-x",
            "owner": "0/0",
        }

        self.set_test_snap_yaml("type", "base")
        overrides = {
            "state_input": {
                "format": STATE_FORMAT_VERSION,
                self.state_files_key: prev_override,
            },
            "state_output": {"format": STATE_FORMAT_VERSION},
        }
        c = SnapReviewFunctional(self.test_name, overrides=overrides)
        c.check_state_base_files()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "functional-snap-v2:state_base_files"
        expected["info"][name] = {
            "text": "OK (skipped, snap type not overridden for this snap)"
        }
        self.check_results(report, expected=expected)

        # verify state_input didn't change
        self.assertTrue(self.state_files_key in c.overrides["state_input"])
        self.assertEqual(
            c.overrides["state_input"][self.state_files_key], prev_override
        )

        # verify state_input is copied to state_output
        self.assertTrue(self.state_files_key in c.overrides["state_output"])
        self.assertEqual(
            c.overrides["state_output"][self.state_files_key], prev_override
        )

    def test_check_state_base_files_output_bad_item(self):
        """Test check_state_base_files() - --state-output"""
        os.environ["SNAP_FORCE_STATE_CHECK"] = "1"
        lln = """Parallel unsquashfs: Using 4 processors
8 inodes (8 blocks) to write

drwxr-xr-x 0/0               215 2020-03-23 14:23 squashfs-root
drwxr-xr-x 0/0                73 2020-03-23 14:23 squashfs-root/bin
-rwxr-xr-x 0/0             43416 2020-03-23 14:23 squashfs-root/bin/cat
"""
        hdr, entries = unsquashfs_lln_parse(lln)
        entries.append(("bad line ./squashfs-root/bad", None))
        self.set_test_unsquashfs_lln(hdr, entries)

        self.set_test_snap_yaml("type", "base")
        overrides = {
            "state_input": {"format": STATE_FORMAT_VERSION},
            "state_output": {"format": STATE_FORMAT_VERSION},
        }
        c = SnapReviewFunctional(self.test_name, overrides=overrides)
        c.check_state_base_files()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "functional-snap-v2:state_base_files"
        expected["info"][name] = {"text": "OK (no previous state)"}
        self.check_results(report, expected=expected)

        self.assertEqual(len(c.curr_state), 3)
        self.assertTrue(self.state_files_key in c.overrides["state_output"])
        self.assertEqual(len(c.overrides["state_output"][self.state_files_key]), 3)
        for fname in [".", "./bin", "./bin/cat"]:
            self.assertTrue(fname in c.curr_state)
            self.assertTrue(fname in c.overrides["state_output"][self.state_files_key])

    def test_check_state_base_files_input_output_same(self):
        """Test check_state_base_files() - with --state-input/--state-output"""
        os.environ["SNAP_FORCE_STATE_CHECK"] = "1"
        exp_state, exp_override, exp_override_state = self._set_default_state()

        self.set_test_snap_yaml("type", "base")
        overrides = {
            "state_input": {
                "format": STATE_FORMAT_VERSION,
                self.state_files_key: exp_override,
            },
            "state_output": {"format": STATE_FORMAT_VERSION},
        }
        c = SnapReviewFunctional(self.test_name, overrides=overrides)
        c.check_state_base_files()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "functional-snap-v2:state_base_files"
        expected["info"][name] = {"text": "OK"}
        self.check_results(report, expected=expected)

        # https://docs.python.org/3/library/unittest.html#unittest.TestCase.assertDictEqual
        # verify prev_state has expected state
        self.assertEqual(c.prev_state, exp_override_state)

        # verify curr_state has expected state
        self.assertEqual(c.curr_state, exp_state)

        # verify state_input is present and same as state_output
        self.assertTrue(self.state_files_key in c.overrides["state_input"])
        self.assertEqual(c.overrides["state_input"][self.state_files_key], exp_override)

        # verify state_output is present with expected output
        self.assertTrue(self.state_files_key in c.overrides["state_output"])
        self.assertEqual(
            c.overrides["state_output"][self.state_files_key], exp_override
        )

    def test_check_state_base_files_input_output_missing(self):
        """Test check_state_base_files() - --state-input/--state-output
           (missing file)
        """
        os.environ["SNAP_FORCE_STATE_CHECK"] = "1"
        exp_state, exp_override, exp_override_state = self._set_default_state()

        prev_override = copy.deepcopy(exp_override)
        prev_override["./bin/ls"] = {
            "filetype": "-",
            "mode": "rwxr-xr-x",
            "owner": "0/0",
        }
        self.set_test_snap_yaml("type", "base")
        overrides = {
            "state_input": {
                "format": STATE_FORMAT_VERSION,
                self.state_files_key: prev_override,
            },
            "state_output": {"format": STATE_FORMAT_VERSION},
        }
        c = SnapReviewFunctional(self.test_name, overrides=overrides)
        c.check_state_base_files()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "functional-snap-v2:state_base_files:missing"
        expected["warn"][name] = {"text": "missing files since last review: ./bin/ls"}
        self.check_results(report, expected=expected)

    def test_check_state_base_files_input_output_missing_snap_in_override(self):
        """Test check_state_base_files() - --state-input/--state-output
           (missing file)
        """
        exp_state, exp_override, exp_override_state = self._set_default_state()

        prev_override = copy.deepcopy(exp_override)
        prev_override["./bin/ls"] = {
            "filetype": "-",
            "mode": "rwxr-xr-x",
            "owner": "0/0",
        }
        self.set_test_snap_yaml("type", "base")
        overrides = {
            "state_input": {
                "format": STATE_FORMAT_VERSION,
                self.state_files_key: prev_override,
            },
            "state_output": {"format": STATE_FORMAT_VERSION},
        }

        # update overrides for our snap
        from reviewtools.overrides import func_base_state_files_snaps_overrides

        func_base_state_files_snaps_overrides.append("foo")

        c = SnapReviewFunctional(self.test_name, overrides=overrides)
        c.check_state_base_files()
        report = c.review_report

        # restore override
        func_base_state_files_snaps_overrides.remove("foo")
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)
        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "functional-snap-v2:state_base_files"
        expected["info"][name] = {
            "text": "OK (skipped, not checking files for this snap)"
        }
        self.check_results(report, expected=expected)

    def test_check_state_base_files_input_output_different(self):
        """Test check_state_base_files() - --state-input/--state-output
           (different file)
        """
        os.environ["SNAP_FORCE_STATE_CHECK"] = "1"
        exp_state, exp_override, exp_override_state = self._set_default_state()

        prev_override = copy.deepcopy(exp_override)
        prev_override["./bin/cat"]["mode"] = "rwxrwxr-x"
        self.set_test_snap_yaml("type", "base")
        overrides = {
            "state_input": {
                "format": STATE_FORMAT_VERSION,
                self.state_files_key: prev_override,
            },
            "state_output": {"format": STATE_FORMAT_VERSION},
        }
        c = SnapReviewFunctional(self.test_name, overrides=overrides)
        c.check_state_base_files()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "functional-snap-v2:state_base_files:metadata:different"
        expected["warn"][name] = {
            "text": "differing metadata since last review: ./bin/cat (current mode 'rwxr-xr-x' != 'rwxrwxr-x')"
        }
        self.check_results(report, expected=expected)

    def test_check_state_base_files_input_output_metadata_missing(self):
        """Test check_state_base_files() - --state-input/--state-output
           (missing metadata)
        """
        os.environ["SNAP_FORCE_STATE_CHECK"] = "1"
        exp_state, exp_override, exp_override_state = self._set_default_state()

        self.set_test_snap_yaml("type", "base")
        overrides = {
            "state_input": {
                "format": STATE_FORMAT_VERSION,
                self.state_files_key: exp_override,
            },
            "state_output": {"format": STATE_FORMAT_VERSION},
        }
        c = SnapReviewFunctional(self.test_name, overrides=overrides)

        # modify one of the files
        del c.curr_state["./bin/cat"][StatLLN.MODE]

        c.check_state_base_files()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "functional-snap-v2:state_base_files:metadata:missing"
        expected["warn"][name] = {
            "text": "missing metadata since last review: ./bin/cat (mode)"
        }
        self.check_results(report, expected=expected)

    def test_check_state_base_files_input_output_missing_symbols(self):
        """Test check_state_base_files() - --state-input/--state-output
           (missing symbols)
        """
        os.environ["SNAP_FORCE_STATE_CHECK"] = "1"
        exp_state, exp_override, exp_override_state = self._set_default_state()

        prev_override = copy.deepcopy(exp_override)
        prev_override["./lib/some.so"]["symbols"] = {
            "foo": {"type": "T", "version": "@@Base"},
            "bar": {"type": "T", "version": "@@Base"},
            "norf": {"type": "T", "version": "@@Base"},
            "baz": {"type": "T", "version": "@@Base"},
        }
        self.set_test_snap_yaml("type", "base")
        overrides = {
            "state_input": {
                "format": STATE_FORMAT_VERSION,
                self.state_files_key: prev_override,
            },
            "state_output": {"format": STATE_FORMAT_VERSION},
        }
        c = SnapReviewFunctional(self.test_name, overrides=overrides)
        c.check_state_base_files()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "functional-snap-v2:state_base_files:symbols:missing"
        expected["warn"][name] = {
            "text": "missing symbols since last review: ./lib/some.so (baz@@Base, norf@@Base)"
        }
        self.check_results(report, expected=expected)

    def test_check_state_base_files_input_output_different_symbols(self):
        """Test check_state_base_files() - --state-input/--state-output
           (different symbols)
        """
        os.environ["SNAP_FORCE_STATE_CHECK"] = "1"
        exp_state, exp_override, exp_override_state = self._set_default_state()

        prev_override = copy.deepcopy(exp_override)
        prev_override["./lib/some.so"]["symbols"] = {
            "foo": {"type": "A", "version": "@@Base"},
            "bar": {"type": "T", "version": "@@Other"},
        }
        self.set_test_snap_yaml("type", "base")
        overrides = {
            "state_input": {
                "format": STATE_FORMAT_VERSION,
                self.state_files_key: prev_override,
            },
            "state_output": {"format": STATE_FORMAT_VERSION},
        }
        c = SnapReviewFunctional(self.test_name, overrides=overrides)
        c.check_state_base_files()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "functional-snap-v2:state_base_files:symbols:different"
        expected["warn"][name] = {
            "text": "differing symbols since last review: ./lib/some.so (current 'bar@@Base T' != 'bar@@Other T', current 'foo@@Base T' != 'foo@@Base A')"
        }
        self.check_results(report, expected=expected)

    def test_check_state_base_files_input_output_same_core(self):
        """Test check_state_base_files() - with --state-input/--state-output
           for core snap
        """
        exp_state, exp_override, exp_override_state = self._set_default_state()

        self.set_test_snap_yaml("type", "os")
        self.set_test_snap_yaml("name", "core")
        overrides = {
            "state_input": {
                "format": STATE_FORMAT_VERSION,
                self.state_files_key: exp_override,
            },
            "state_output": {"format": STATE_FORMAT_VERSION},
        }
        c = SnapReviewFunctional(self.test_name, overrides=overrides)
        c.check_state_base_files()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "functional-snap-v2:state_base_files"
        expected["info"][name] = {"text": "OK"}
        self.check_results(report, expected=expected)

        # verify prev_state has expected state
        self.assertEqual(c.prev_state, exp_override_state)

        # verify curr_state has expected state
        self.assertEqual(c.curr_state, exp_state)

        # verify state_input is present and same as state_output
        self.assertTrue(self.state_files_key in c.overrides["state_input"])
        self.assertEqual(c.overrides["state_input"][self.state_files_key], exp_override)

        # verify state_output is present with expected output
        self.assertTrue(self.state_files_key in c.overrides["state_output"])
        self.assertEqual(
            c.overrides["state_output"][self.state_files_key], exp_override
        )

    def test_check_state_base_files_input_output_missing_override(self):
        """Test check_state_base_files() - with --state-input/--state-output
           missing with override
        """
        os.environ["SNAP_FORCE_STATE_CHECK"] = "1"
        exp_state, exp_override, exp_override_state = self._set_default_state()
        prev_override = copy.deepcopy(exp_override)
        prev_override["./skipped/foo"] = {
            "filetype": "-",
            "mode": "rwxr-xr-x",
            "owner": "0/0",
        }
        prev_override["./not-skipped/bar"] = {
            "filetype": "-",
            "mode": "rwxr-xr-x",
            "owner": "0/0",
        }

        self.set_test_snap_yaml("type", "base")
        self.set_test_snap_yaml("name", "somebase")
        overrides = {
            "state_input": {
                "format": STATE_FORMAT_VERSION,
                self.state_files_key: prev_override,
            },
            "state_output": {"format": STATE_FORMAT_VERSION},
        }
        c = SnapReviewFunctional(self.test_name, overrides=overrides)
        # update overrides for our snap
        from reviewtools.overrides import func_base_state_files_overrides

        func_base_state_files_overrides["somebase"] = ["skipped/.*"]

        c.check_state_base_files()

        # restore override
        del func_base_state_files_overrides["somebase"]

        report = c.review_report
        expected_counts = {"info": 0, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

        expected = dict()
        expected["error"] = dict()
        expected["warn"] = dict()
        expected["info"] = dict()
        name = "functional-snap-v2:state_base_files:missing"
        expected["warn"][name] = {
            "text": "missing files since last review: ./not-skipped/bar"
        }
        self.check_results(report, expected=expected)


class TestSnapReviewFunctionalNoMock(TestCase):
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

    def _execstack_has_lp1850861(self):
        """See if execstack breaks on LP: 1850861"""
        fn = os.path.join(self.mkdtemp(), "ls")
        shutil.copyfile("/bin/ls", fn)
        (rc, out) = cmd(["execstack", "--set-execstack", fn])
        if rc != 0:
            return True

    def test_check_execstack_inject_link(self):
        """Workaround the fact that newer releases don't have a functional
           execstack (LP: #1850861). This isn't an actual check but rather
           an injection so collect-check-names-from-tests returns consistent
           results when the testsuite is run on systems with and without a
           functional execstack.
        """
        if not self._execstack_has_lp1850861():
            return
        package = utils.make_snap2(output_dir=self.mkdtemp())
        c = SnapReviewFunctional(package)
        c._add_result(
            "info",
            "functional-snap-v2:execstack",
            "OK (faked via test_check_execstack_inject_link())",
            manual_review=False,
            link="https://forum.snapcraft.io/t/snap-and-executable-stacks/1812",
        )
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_execstack(self):
        """Test check_execstack() - execstack found execstack binary"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return

        # copy /bin/ls nonexecstack.bin
        package = utils.make_snap2(
            output_dir=self.mkdtemp(), extra_files=["/bin/ls:nonexecstack.bin"]
        )
        c = SnapReviewFunctional(package)
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_execstack_found_binary(self):
        """Test check_execstack() - execstack found execstack binary"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return
        elif self._execstack_has_lp1850861():
            print("SKIPPING: execstack failed (LP: #1850861)")
            return

        output_dir = self.mkdtemp()
        fn = os.path.join(output_dir, "hasexecstack.bin")
        shutil.copyfile("/bin/ls", fn)
        # create a /bin/ls with executable stack
        cmd(["execstack", "--set-execstack", fn])

        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = [fn]
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": None, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

        # with how we mocked, we have the absolute path of the file in the
        # tmpdir, so verify beginning of warn only
        self.assertTrue("warn" in report)
        name = "functional-snap-v2:execstack"
        self.assertTrue(name in report["warn"])
        self.assertTrue("text" in report["warn"][name])
        self.assertTrue(
            report["warn"][name]["text"].startswith("Found files with executable stack")
        )

    def test_check_execstack_found_binary_devmode(self):
        """Test check_execstack() - execstack found execstack binary - devmode"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return
        elif self._execstack_has_lp1850861():
            print("SKIPPING: execstack failed (LP: #1850861)")
            return

        output_dir = self.mkdtemp()
        fn = os.path.join(output_dir, "hasexecstack.bin")
        shutil.copyfile("/bin/ls", fn)
        # create a /bin/ls with executable stack
        cmd(["execstack", "--set-execstack", fn])

        yaml = """architectures: [ all ]
name: test
version: 1.0
summary: An application
description: An application
confinement: devmode
"""
        package = utils.make_snap2(output_dir=output_dir, yaml=yaml)
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = [fn]
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        # with how we mocked, we have the absolute path of the file in the
        # tmpdir, so verify beginning of info only
        self.assertTrue("info" in report)
        name = "functional-snap-v2:execstack"
        self.assertTrue(name in report["info"])
        self.assertTrue("text" in report["info"][name])
        self.assertTrue(
            report["info"][name]["text"].startswith("Found files with executable stack")
        )

    def test_check_execstack_found_binary_override(self):
        """Test check_execstack() - execstack found execstack binary - override"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return
        elif self._execstack_has_lp1850861():
            print("SKIPPING: execstack failed (LP: #1850861)")
            return

        output_dir = self.mkdtemp()
        fn = os.path.join(output_dir, "hasexecstack.bin")
        shutil.copyfile("/bin/ls", fn)
        # create a /bin/ls with executable stack
        cmd(["execstack", "--set-execstack", fn])
        package = utils.make_snap2(name="test-override", output_dir=output_dir)
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = [fn]

        # update overrides for our snap
        from reviewtools.overrides import func_execstack_overrides

        func_execstack_overrides.append("test-override")
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        # with how we mocked, we have the absolute path of the file in the
        # tmpdir, so verify beginning of info only
        self.assertTrue("info" in report)
        name = "functional-snap-v2:execstack"
        self.assertTrue(name in report["info"])
        self.assertTrue("text" in report["info"][name])
        self.assertTrue(
            report["info"][name]["text"].startswith(
                "OK (allowing files with executable stack:"
            )
        )

    def test_check_execstack_os(self):
        """Test check_execstack() - os snap"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return
        elif self._execstack_has_lp1850861():
            print("SKIPPING: execstack failed (LP: #1850861)")
            return

        output_dir = self.mkdtemp()
        fn = os.path.join(output_dir, "hasexecstack.bin")
        shutil.copyfile("/bin/ls", fn)
        # create a /bin/ls with executable stack
        cmd(["execstack", "--set-execstack", fn])

        yaml = """architectures: [ all ]
name: test
version: 1.0
summary: An application
description: An application
type: os
"""
        package = utils.make_snap2(output_dir=output_dir, yaml=yaml)
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = [fn]
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_execstack_rc_nonzero(self):
        """Test check_execstack() - execstack returns non-zero"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return

        package = utils.make_snap2(output_dir=self.mkdtemp())
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = ["path/to/nonexistent/file"]
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_execstack_binary_skip(self):
        """Test check_execstack() - execstack found only skipped execstack
           binaries"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return
        elif self._execstack_has_lp1850861():
            print("SKIPPING: execstack failed (LP: #1850861)")
            return

        test_files = [
            "boot/memtest86+_multiboot.bin",
            "lib/klibc-T5LXP1hTwH_ezt-1EUSxPbNR_es.so",
            "usr/alpha-linux-gnu/lib/libgnatprj.so.6",
            "usr/bin/aarch64-linux-gnu-gnatmake-5",
            "usr/bin/gnatcheck",
            "usr/bin/grub-emu",
            "usr/bin/i686-w64-mingw32-gnatclean-posix",
            "usr/lib/debug/usr/bin/iac",
            "usr/lib/grub/i386-coreboot/kernel.exec",
            "usr/lib/i386-linux-gnu/libgnatprj.so.6",
            "usr/lib/klibc/bin/cat",
            "usr/lib/libatlas-test/xcblat1",
            "usr/lib/nvidia-340/bin/nvidia-cuda-mps-control",
            "usr/lib/syslinux/modules/bios/gfxboot.c32",
            "usr/share/dpdk/test/test",
        ]
        output_dir = self.mkdtemp()

        pkg_bin_files = []
        for f in test_files:
            dir = os.path.join(output_dir, os.path.dirname(f))
            if not os.path.exists(dir):
                os.makedirs(dir, 0o0755)
            fn = os.path.join(output_dir, f)
            shutil.copyfile("/bin/ls", fn)
            # create a /bin/ls with executable stack
            cmd(["execstack", "--set-execstack", fn])
            pkg_bin_files.append(fn)

        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = pkg_bin_files
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_execstack_found_with_binary_skip(self):
        """Test check_execstack() - execstack found skipped execstack binary"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return
        elif self._execstack_has_lp1850861():
            print("SKIPPING: execstack failed (LP: #1850861)")
            return

        test_files = ["hasexecstack.bin", "usr/lib/klibc/bin/cat"]
        output_dir = self.mkdtemp()

        pkg_bin_files = []
        for f in test_files:
            dir = os.path.join(output_dir, os.path.dirname(f))
            if not os.path.exists(dir):
                os.makedirs(dir, 0o0755)
            fn = os.path.join(output_dir, f)
            shutil.copyfile("/bin/ls", fn)
            # create a /bin/ls with executable stack
            cmd(["execstack", "--set-execstack", fn])
            pkg_bin_files.append(fn)

        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = pkg_bin_files
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": None, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

        # with how we mocked, we have the absolute path of the file in the
        # tmpdir, so verify beginning of warn only
        self.assertTrue("warn" in report)
        name = "functional-snap-v2:execstack"
        self.assertTrue(name in report["warn"])
        self.assertTrue("text" in report["warn"][name])
        self.assertTrue(
            report["warn"][name]["text"].startswith("Found files with executable stack")
        )
        self.assertTrue("hasexecstack.bin" in report["warn"][name]["text"])
        self.assertTrue("klibc" not in report["warn"][name]["text"])

    def test_check_execstack_skipped_arm64(self):
        """Test check_execstack() - skipped on arm64"""
        os.environ["SNAP_ARCH"] = "arm64"

        package = utils.make_snap2()
        c = SnapReviewFunctional(package)
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        self.assertTrue("info" in report)
        name = "functional-snap-v2:execstack"
        self.assertTrue(name in report["info"])
        self.assertTrue("text" in report["info"][name])
        self.assertTrue(report["info"][name]["text"] == ("OK (skipped on arm64)"))

    def test_check_base_mountpoints(self):
        """Test check_base_mountpoints()"""
        test_files = [
            "/dev/",
            "/etc/",
            "/home/",
            "/root/",
            "/proc/",
            "/sys/",
            "/tmp/",
            "/var/snap/",
            "/var/lib/snapd/",
            "/var/tmp/",
            "/run/",
            "/usr/src/",
            "/var/log/",
            "/media/",
            "/usr/lib/snapd/",
            "/usr/local/share/fonts/",
            "/usr/share/fonts/",
            "/var/cache/fontconfig/",
            "/lib/modules/",
            "/mnt/",
        ]

        yaml = """
name: test
version: 1.0
type: base
"""
        package = utils.make_snap2(extra_files=test_files, yaml=yaml)
        c = SnapReviewFunctional(package)
        c.check_base_mountpoints()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_base_mountpoints_missing(self):
        """Test check_base_mountpoints() - missing"""
        test_files = [
            "/dev/",
            "/home/",
            "/root/",
            "/proc/",
            "/sys/",
            "/tmp/",
            "/var/snap/",
            "/var/lib/snapd/",
            "/var/tmp/",
            "/run/",
            "/usr/src/",
            "/var/log/",
            "/media/",
            "/usr/lib/snapd/",
            "/usr/local/share/fonts/",
            "/usr/share/fonts/",
            "/var/cache/fontconfig/",
            "/lib/modules/",
            "/mnt/",
        ]

        yaml = """
name: test
version: 1.0
type: base
"""
        package = utils.make_snap2(extra_files=test_files, yaml=yaml)
        c = SnapReviewFunctional(package)
        c.check_base_mountpoints()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        self.assertTrue("info" in report)
        name = "functional-snap-v2:base_mountpoints"
        self.assertTrue(name in report["error"])
        self.assertTrue("text" in report["error"][name])
        self.assertTrue(
            report["error"][name]["text"] == ("missing required mountpoints: /etc")
        )

    def test_check_base_mountpoints_missing_overridden(self):
        """Test check_base_mountpoints() - missing (overridden)"""
        test_files = [
            "/dev/",
            "/home/",
            "/root/",
            "/proc/",
            "/sys/",
            "/tmp/",
            "/var/snap/",
            "/var/lib/snapd/",
            "/var/tmp/",
            "/run/",
            "/usr/src/",
            "/var/log/",
            "/media/",
            "/usr/lib/snapd/",
            "/usr/local/share/fonts/",
            "/usr/share/fonts/",
            "/var/cache/fontconfig/",
            "/lib/modules/",
            "/mnt/",
        ]

        yaml = """
name: test-override
version: 1.0
type: base
"""
        package = utils.make_snap2(extra_files=test_files, yaml=yaml)
        c = SnapReviewFunctional(package)
        from reviewtools.overrides import func_base_mountpoints_overrides

        func_base_mountpoints_overrides.append("test-override")
        c.check_base_mountpoints()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        self.assertTrue("info" in report)
        name = "functional-snap-v2:base_mountpoints"
        self.assertTrue(name in report["info"])
        self.assertTrue("text" in report["info"][name])
        self.assertTrue(
            report["info"][name]["text"]
            == ("missing required mountpoints: /etc (overridden)")
        )
