'''sr_functional.py: snap functional'''
#
# Copyright (C) 2017-2019 Canonical Ltd.
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
from reviewtools.sr_common import (
    SnapReview,
)
from reviewtools.common import (
    cmd,
)
from reviewtools.overrides import (
    func_execstack_overrides,
    func_execstack_skipped_pats,
    func_base_mountpoints_overrides,
)
import os
import re


class SnapReviewFunctional(SnapReview):
    '''This class represents snap functional reviews'''
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

        def in_patterns(pats, f):
            for pat in pats:
                if pat.search(f):
                    return True
            return False

        t = 'info'
        n = self._get_check_name('execstack')
        s = "OK"
        link = None
        bins = []

        # execstack not supported on arm64, so skip this check on arm64
        if 'SNAP_ARCH' in os.environ and os.environ['SNAP_ARCH'] == "arm64":
            s = 'OK (skipped on %s)' % os.environ['SNAP_ARCH']
            self._add_result(t, n, s, link=link)
            return

        skipped_pats = []
        for p in func_execstack_skipped_pats:
            skipped_pats.append(re.compile(r'%s' % p))

        for i in self.pkg_bin_files:
            if has_execstack(i) and not in_patterns(skipped_pats, i):
                bins.append(os.path.relpath(i, self.unpack_dir))

        if len(bins) > 0:
            bins.sort()
            if self.snap_yaml['name'] in func_execstack_overrides:
                t = 'info'
                s = 'OK (allowing files with executable stack: %s)' % \
                    ", ".join(bins)
            else:
                t = 'warn'
                # Only warn for strict mode snaps, since they are the ones that
                # will break
                if 'confinement' in self.snap_yaml and \
                        self.snap_yaml['confinement'] != 'strict':
                    t = 'info'
                s = "Found files with executable stack. This adds PROT_EXEC to mmap(2) during mediation which may cause security denials. Either adjust your program to not require an executable stack, strip it with 'execstack --clear-execstack ...' or remove the affected file from your snap. Affected files: %s" % ", ".join(bins)
                link = 'https://forum.snapcraft.io/t/snap-and-executable-stacks/1812'

        self._add_result(t, n, s, link=link)

    def check_base_mountpoints(self):
        '''Verify base snap has all the expected mountpoints'''
        if not self.is_snap2 or self.snap_yaml['type'] != 'base':
            return

        t = 'info'
        n = self._get_check_name('base_mountpoints')
        s = "OK"
        missing = []

        for i in self.base_required_dirs:
            # self.base_required_dirs are absolute paths
            mp = os.path.join(self.unpack_dir, i[1:])
            if not os.path.isdir(mp):
                missing.append(i)

        if len(missing) > 0:
            missing.sort()
            s = 'missing required mountpoints: %s' % ", ".join(missing)
            if self.snap_yaml['name'] not in func_base_mountpoints_overrides:
                t = 'error'
            else:
                s += " (overridden)"
        self._add_result(t, n, s)
