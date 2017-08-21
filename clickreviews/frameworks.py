#
#  Copyright (C) 2014 Canonical Ltd.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 3 of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import clickreviews.remote

USER_DATA_FILE = os.path.join(clickreviews.remote.DATA_DIR, 'frameworks.json')
FRAMEWORKS_DATA_URL = \
    "https://myapps.developer.ubuntu.com/dev/api/click-framework/"


def get_frameworks_file(fn):
    if fn is None:
        fn = USER_DATA_FILE
    clickreviews.remote.get_remote_file(fn, FRAMEWORKS_DATA_URL)


class Frameworks(object):
    DEPRECATED_FRAMEWORKS = []
    OBSOLETE_FRAMEWORKS = []
    AVAILABLE_FRAMEWORKS = []

    def __init__(self, overrides=None):
        local_copy_fn = None
        if 'SNAP' in os.environ:
            fn = os.path.join(os.environ['SNAP'], 'data/click-frameworks.json')
            if os.path.exists(fn):
                local_copy_fn = fn

        self.FRAMEWORKS = clickreviews.remote.read_cr_file(USER_DATA_FILE,
                                                           FRAMEWORKS_DATA_URL,
                                                           local_copy_fn=local_copy_fn)
        if overrides is not None:
            self.FRAMEWORKS.update(overrides)

        for name, data in self.FRAMEWORKS.items():
            if type(data) is dict:
                state = data.get('state')
            else:
                state = data

            if state == 'deprecated':
                self.DEPRECATED_FRAMEWORKS.append(name)
            elif state == 'obsolete':
                self.OBSOLETE_FRAMEWORKS.append(name)
            elif state == 'available':
                self.AVAILABLE_FRAMEWORKS.append(name)
