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

from reviewtools.sr_common import SnapReview
import reviewtools.sr_tests as sr_tests
import reviewtools.common


class TestSnapReviewSkeleton(sr_tests.TestSnapReview):
    """Tests for common module"""

    def setUp(self):
        super().setUp()
        # This allows calling instance methods via:
        #   self.review.foo()
        self.review = SnapReview("app.snap", "common_review_type")

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
