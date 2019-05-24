'''test_email.py: tests for the email module'''
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
from reviewtools.email import (
    sanitize_addr,
)


class TestEmail(TestCase):
    """Tests for email functions."""

    def test_check_sanitize_addr_valid(self):
        '''Test sanitize_addr() - valid'''
        addresses = [('foo@bar.com', 'foo@bar.com'),
                     ('Foo Bar <foo.bar@example.com>', 'foo.bar@example.com'),
                     ('snaps@canonical.com',
                      'snaps@canonical.com'),
                     ]
        for (addr, expected) in addresses:
            self.assertEquals(sanitize_addr(addr), expected)

    def test_check_sanitize_addr_invalid(self):
        '''Test sanitize_addr() - invalid'''
        addresses = [('', ''),
                     ('foo.bar', ''),
                     ('foo.bar@', ''),
                     ('@foo.bar', ''),
                     ('foo@@bar', ''),
                     ]
        for (addr, expected) in addresses:
            self.assertEquals(sanitize_addr(addr), expected)
