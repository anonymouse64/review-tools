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

USER_DATA_FILE = os.path.join(clickreviews.remote.DATA_DIR,
                              'apparmor-easyprof-ubuntu.json')

# This is a hack that shouldn't be here, but myapps doesn't have an API for
# this.
AA_POLICY_DATA_URL = \
    "http://bazaar.launchpad.net/~store-reviewers/click-reviewers-tools/trunk/download/head:/apparmoreasyprofubun-20140711222314-oeohtxzvf9a58fa6-1/apparmor-easyprof-ubuntu.json"


def get_policy_file(fn):
    if fn is None:
        fn = USER_DATA_FILE
    clickreviews.remote.get_remote_file(fn, AA_POLICY_DATA_URL)


class ApparmorPolicy(object):
    def __init__(self, local_copy_fn=None):
        self.policy = clickreviews.remote.read_cr_file(USER_DATA_FILE,
                                                       AA_POLICY_DATA_URL,
                                                       local_copy_fn)
