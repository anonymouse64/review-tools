'''test_usn.py: tests for the usn module'''
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

import clickreviews.usn as usn


class TestUSN(TestCase):
    """Tests for the USN functions."""

    def test_check_read_usn_dn(self):
        '''Test read_usn_db()'''
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")

        expected_db = {
            'xenial': {'libtiff-doc': {'3602-1': '4.0.6-1ubuntu0.3',
                                       '3606-1': '4.0.6-1ubuntu0.4'},
                       'libtiff-opengl': {'3602-1': '4.0.6-1ubuntu0.3',
                                          '3606-1': '4.0.6-1ubuntu0.4'},
                       'libtiff-tools': {'3602-1': '4.0.6-1ubuntu0.3',
                                         '3606-1': '4.0.6-1ubuntu0.4'},
                       'libtiff5': {'3602-1': '4.0.6-1ubuntu0.3',
                                    '3606-1': '4.0.6-1ubuntu0.4'},
                       'libtiff5-dev': {'3602-1': '4.0.6-1ubuntu0.3',
                                        '3606-1': '4.0.6-1ubuntu0.4'},
                       'libtiffxx5': {'3602-1': '4.0.6-1ubuntu0.3',
                                      '3606-1': '4.0.6-1ubuntu0.4'},
                       'libxcursor-dev': {'3501-1':
                                          '1:1.1.14-1ubuntu0.16.04.1'},
                       'libxcursor1': {'3501-1':
                                       '1:1.1.14-1ubuntu0.16.04.1'},
                       'libxcursor1-dbg': {'3501-1':
                                           '1:1.1.14-1ubuntu0.16.04.1'},
                       'libxcursor1-udeb': {'3501-1':
                                            '1:1.1.14-1ubuntu0.16.04.1'},
                       }}

        self.assertEquals(len(expected_db), len(res))
        for rel in expected_db:
            self.assertTrue(rel in res)
            self.assertEquals(len(expected_db[rel]), len(res[rel]))
            for pkg in expected_db[rel]:
                self.assertTrue(pkg in res[rel])
                self.assertEquals(len(expected_db[rel][pkg]),
                                  len(res[rel][pkg]))
                for sn in expected_db[rel][pkg]:
                    self.assertTrue(sn in res[rel][pkg])
                    self.assertEquals(expected_db[rel][pkg][sn],
                                      str(res[rel][pkg][sn]))
