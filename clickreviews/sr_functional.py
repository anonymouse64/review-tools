'''sr_functional.py: snap functional'''
#
# Copyright (C) 2017 Canonical Ltd.
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
from clickreviews.sr_common import (
    SnapReview,
)
from clickreviews.common import (
    cmd,
)
import os


class SnapReviewFunctional(SnapReview):
    '''This class represents snap lint reviews'''
    def __init__(self, fn, overrides=None):
        SnapReview.__init__(self, fn, "functional-snap-v2", overrides=overrides)
        self._list_all_compiled_binaries()

    def check_execstack(self):
        '''Check execstack'''
        if not self.is_snap2:
            return

        # core snap is known to have these due to klibc. Executable stack
        # checks only make sense for app snaps anyway.
        if self.snap_yaml['type'] != 'app':
            return

        def has_execstack(fn):
            (rc, out) = cmd(['execstack', '-q', fn])
            if rc != 0:
                return False

            if out.startswith('X '):
                return True
            return False

        t = 'info'
        n = self._get_check_name('execstack')
        s = "OK"
        link = None
        bins = []

        for i in self.pkg_bin_files:
            if has_execstack(i):
                bins.append(os.path.relpath(i, self.unpack_dir))

        if len(bins) > 0:
            t = 'warn'
            s = "Found files with executable stack. This adds PROT_EXEC to mmap(2) during mediation which may cause security denials. Either adjust your program to not require an executable stack or strip it with 'execstack --clear-execstack ...'. Affected files: %s" % ", ".join(bins)
            link = 'https://forum.snapcraft.io/t/snap-and-executable-stacks/1812'

        # Only warn for strict mode snaps, since they are the ones that will
        # break
        if 'confinement' in self.snap_yaml and \
                self.snap_yaml['confinement'] != 'strict':
            t = 'info'

        self._add_result(t, n, s, link=link)
