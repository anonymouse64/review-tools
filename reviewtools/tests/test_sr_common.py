"""test_sr_common.py: tests for the sr_common module"""
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

from reviewtools.sr_common import SnapReview
import reviewtools.sr_tests as sr_tests


class TestSnapReviewCommon(sr_tests.TestSnapReview):
    def setUp(self):
        super().setUp()
        self.review = SnapReview("app.snap", "sr_common_review_type")

    def test_verify_pkgversion(self):
        """Check _verify_pkgversion"""
        for ok in [
            "0",
            "v1.0",
            "0.12+16.04.20160126-0ubuntu1",
            "1:6.0.1+r16-3",
            "1.0~",
            "1.0+",
            "README.~1~",
            "a+++++++++++++++++++++++++++++++",
            "AZaz:.+~-123",
        ]:
            self.assertTrue(self.review._verify_pkgversion(ok))
        for nok in [
            "~foo",
            "+foo",
            "foo:",
            "foo.",
            "foo-",
            "horrible_underscores",
            "foo($bar^baz$)meep",
            "árbol",
            "日本語",
            "한글",
            "ру́сский язы́к",
            "~foo$bar:",
        ]:
            self.assertFalse(self.review._verify_pkgversion(nok))
