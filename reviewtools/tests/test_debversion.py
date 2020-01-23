"""test_debversion.py: tests for the debversion module"""
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
from reviewtools.debversion import DebVersion, compare, _order


class TestDebVersion(TestCase):
    """Tests for the debian version functions."""

    def test_check_version_compare(self):
        """Test compare(a, b) == x"""
        # based on lib/dpkg/t/t-version.c
        versions = [
            ("1:0", "2:0", -1),
            ("2:0", "1:0", 1),
            ("1-1", "2-1", -1),
            ("2-1", "1-1", 1),
            ("1-1", "1-2", -1),
            ("1-2", "1-1", 1),
            ("0", "0", 0),
            ("0-00", "00-0", 0),
            ("1:2-3", "1:2-3", 0),
            ("0:0", "1:0", -1),
            ("1:0", "0:0", 1),
            ("a-0", "b-0", -1),
            ("b-0", "a-0", 1),
            ("0-a", "0-b", -1),
            ("0-b", "0-a", 1),
            ("0", "0:0", 0),
            ("0:0", "0:0", 0),
            ("0:0-", "0:0-", 0),
            ("0:0-0", "0:0-0", 0),
            ("0:0.0-0.0", "0:0.0-0.0", 0),
            ("0:0-0-0", "0:0-0-0", 0),
            ("0:0:0-0", "0:0:0-0", 0),
            ("0:0:0:0-0", "0:0:0:0-0", 0),
            ("0:0:0-0-0", "0:0:0-0-0", 0),
            ("0:0-0:0-0", "0:0-0:0-0", 0),
            ("0:09azAZ.-+~:", "0:09azAZ.-+~:", 0),
            ("0:0-azAZ09.+~", "0:0-azAZ09.+~", 0),
            ("1.2-3", "1.2-3build1", -1),
            ("1.2-3build1", "1.2-3", 1),
            ("1.2-3build1", "1.2-3build1", 0),
            ("1.2-3", "1.2-3+foo", -1),
            ("1.2-3+foo", "1.2-3", 1),
            ("1.2-3+foo", "1.2-3+foo", 0),
            ("1.2-3", "1.2-3~foo", 1),
            ("1.2-3~foo", "1.2-3", -1),
            ("1.2-3~foo", "1.2-3~foo", 0),
            ("1:9.10.3.dfsg.P4-8ubuntu1.6", "1:9.10.3.dfsg.P4-8ubuntu1.10", -1),
            ("1:9.10.3.dfsg.P4-8ubuntu1.10", "1:9.10.3.dfsg.P4-8ubuntu1.6", 1),
            ("1:9.10.3.dfsg.P4-8ubuntu1.10", "1:9.10.3.dfsg.P4-8ubuntu1.10", 0),
            (
                "1:0.30.0~git20131003.d20b8d+really20110821-0.2ubuntu12.2",
                "1:0.30.0~git20131003.d20b8d+really20110821-0.2ubuntu12.3",
                -1,
            ),
            (
                "1:0.30.0~git20131003.d20b8d+really20110821-0.2ubuntu12.3",
                "1:0.30.0~git20131003.d20b8d+really20110821-0.2ubuntu12.2",
                1,
            ),
            (
                "1:0.30.0~git20131003.d20b8d+really20110821-0.2ubuntu12.2",
                "1:0.30.0~git20131003.d20b8d+really20110821-0.2ubuntu12.2",
                0,
            ),
        ]
        print("")
        for (av, bv, expected) in versions:
            print("  checking compare(%s, %s) == %d" % (av, bv, expected))
            a = DebVersion(av)
            b = DebVersion(bv)

            rc = compare(a, b)
            if rc < 0:
                rc = -1
            elif rc > 0:
                rc = 1

            self.assertEquals(rc, expected)

    def test_check_version_invalid(self):
        """Test DebVersion(<version>) - invalid"""
        # based on lib/dpkg/t/t-version.c
        versions = [
            "",
            "0:",
            "0:0 0-1",
            "-1:0-1",
            "999999999999999999999999:0-1",
            # invalid in epoch
            "a:0-0",
            "A:0-0",
            # version doesn't start with digit is only a warning
            # '0:abc3-0',
            # invalid in version
            "0:0!-0",
            "0:0#-0",
            "0:0@-0",
            "0:0$-0",
            "0:0%-0",
            "0:0&-0",
            "0:0/-0",
            "0:0|-0",
            "0:0\\-0",
            "0:0<-0",
            "0:0>-0",
            "0:0(-0",
            "0:0)-0",
            "0:0[-0",
            "0:0]-0",
            "0:0{-0",
            "0:0}-0",
            "0:0;-0",
            "0:0,-0",
            "0:0_-0",
            "0:0=-0",
            "0:0*-0",
            "0:0^-0",
            "0:0'-0",
            '0:0"-0',
            # invalid in revision
            "0:0-!",
            "0:0-#",
            "0:0-@",
            "0:0-$",
            "0:0-%",
            "0:0-&",
            "0:0-/",
            "0:0-|",
            "0:0-\\",
            "0:0-<",
            "0:0->",
            "0:0-(",
            "0:0-)",
            "0:0-[",
            "0:0-]",
            "0:0-{",
            "0:0-}",
            "0:0-;",
            "0:0-,",
            "0:0-_",
            "0:0-=",
            "0:0-*",
            "0:0-^",
            "0:0-'",
            '0:0-"',
            # added based on https://www.debian.org/doc/debian-policy/#s-f-version
            "1-2-",
        ]
        print("")
        for v in versions:
            print("  checking DebVersion('%s')" % v)
            try:
                DebVersion(v)
            except ValueError:
                continue

            raise Exception("Should have raised ValueError")  # pragma: nocover

    def test_check___repr__(self):
        """Test __repr()__"""
        v = DebVersion("1.0")
        self.assertEquals("%s" % v.__repr__(), "1.0")

    def test_check___str__(self):
        """Test __str()__"""
        v = DebVersion("1.0")
        self.assertEquals(str(v), "1.0")

    def test_check__order(self):
        """Test __str()__"""
        expected_db = [
            ("1", 0),
            ("a", 97),
            ("~", -1),
            ("@", 320),  # (ord'@') + 256
            ("", 0),
        ]
        for ver, expected in expected_db:
            res = _order(ver)
            self.assertEquals(res, expected)
