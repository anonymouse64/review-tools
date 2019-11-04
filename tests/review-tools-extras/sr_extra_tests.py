'''sr_extra_tests.py: snap extra_tests'''
#
# Copyright (C) 2019 Canonical Ltd.
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


class SnapReviewExtrasTests(SnapReview):
    '''This class represents snap extras reviews'''
    def __init__(self, fn, overrides=None):
        SnapReview.__init__(self, fn, "extras-tests-v2",
                            overrides=overrides)

    def check_info(self):
        '''Check info'''
        t = 'info'
        n = self._get_check_name('info')
        s = "test info"
        self._add_result(t, n, s)

    def check_warn(self):
        '''Check warn'''
        t = 'warn'
        n = self._get_check_name('warn')
        s = "test warn"
        self._add_result(t, n, s)

    def check_error(self):
        '''Check error'''
        t = 'error'
        n = self._get_check_name('error')
        s = "test error"
        self._add_result(t, n, s)
