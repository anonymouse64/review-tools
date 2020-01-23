"""sr_skeleton.py: snap skeleton"""
#
# Copyright (C) 2014-2015 Canonical Ltd.
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
from reviewtools.sr_common import SnapReview


class SnapReviewSkeleton(SnapReview):
    """This class represents snap lint reviews"""

    def __init__(self, fn, overrides=None):
        SnapReview.__init__(self, fn, "skeleton-snap-v2", overrides=overrides)

    def check_foo(self):
        """Check foo"""
        t = "info"
        n = self._get_check_name("foo")
        s = "OK"
        if False:
            t = "error"
            s = "some message"
        self._add_result(t, n, s)

    def check_bar(self):
        """Check bar"""
        t = "info"
        n = self._get_check_name("bar")
        s = "OK"
        if True:
            t = "error"
            s = "some message"
        self._add_result(t, n, s)

    def check_baz(self):
        """Check baz"""
        n = self._get_check_name("baz")
        self._add_result("warn", n, "TODO", link="http://example.com")

        # Spawn a shell to pause the script (run 'exit' to continue)
        # import subprocess
        # print(self.unpack_dir)
        # subprocess.call(['bash'])
