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

import os
import re

import reviewtools.debversion as debversion

from reviewtools.common import (
    read_file_as_json_dict,
)

tracked_releases = ['xenial', 'bionic']


# For fast checks:
# usn_db[release][binary][usn][version]
def read_usn_db(fn):
    raw = read_file_as_json_dict(fn)
    epoch_pat = re.compile(r'^[0-9]+:')

    usn_db = {}
    for usn in raw:
        if "releases" not in raw[usn]:
            continue
        for rel in tracked_releases:
            if rel not in raw[usn]["releases"]:
                continue

            # Now we have a USN for a tracked Ubuntu release
            if rel not in usn_db:
                usn_db[rel] = {}

            if "sources" not in raw[usn]["releases"][rel]:
                continue

            # XXX: We don't use this below... is it needed for parsing ancient
            # USNs we just want to ignore?
            if "binaries" not in raw[usn]["releases"][rel]:
                continue

            #
            # see if we can use "allbinaries" which is authoritative but only
            # available in USNs after Dec 2018
            #

            # FIXME: note that prior to Sept 2019, "allbinaries" assumed the
            # binaries had the same version as the source. To account for that,
            # we should examine the Packages files for tracked_releases and
            # come up with an override mechanism
            if "allbinaries" in raw[usn]["releases"][rel]:
                for bin in raw[usn]["releases"][rel]["allbinaries"]:
                    version = debversion.DebVersion(raw[usn]["releases"][rel]["allbinaries"][bin]["version"])
                    if bin not in usn_db[rel]:
                        usn_db[rel][bin] = {}
                    if usn not in usn_db[rel][bin]:
                        usn_db[rel][bin][usn] = {}
                        usn_db[rel][bin][usn]['version'] = version
                        if 'cves' in raw[usn]:
                            usn_db[rel][bin][usn]['cves'] = raw[usn]['cves']
                            usn_db[rel][bin][usn]['cves'].sort()

                # nothing more to do with this USN
                continue

            #
            # "allbinaries" not available for this USN. Fallback to guessing
            #

            # for checking epochs, later
            source_versions = []
            for src in raw[usn]["releases"][rel]["sources"]:
                if "version" not in raw[usn]["releases"][rel]["sources"][src]:
                    continue
                sv = raw[usn]["releases"][rel]["sources"][src]["version"]
                if sv not in source_versions:
                    source_versions.append(sv)
            source_versions.sort(reverse=True)

            # Find the binaries from the arch URLs to work around lack of
            # source_map, etc
            if "archs" not in raw[usn]["releases"][rel]:
                continue
            for arch in raw[usn]["releases"][rel]["archs"]:
                if "urls" not in raw[usn]["releases"][rel]["archs"][arch]:
                    continue
                for u in raw[usn]["releases"][rel]["archs"][arch]["urls"]:
                    # foo_1.2_amd64.deb
                    tmp = os.path.basename(u).split('_')
                    if len(tmp) < 3:
                        continue
                    bin = tmp[0]

                    # obtain the version for this binary
                    usn_version = tmp[1]
                    # Note: handle epochs. source_versions is a reverse sorted
                    # list which means we will always assume the snap has the
                    # higher epoch (eg 2:1.2-1 over 1:1.2-1) which is
                    # technically wrong but in practice we don't bump the epoch
                    # in security updates within an Ubuntu release so in
                    # practice this is not a problem.
                    if usn_version not in source_versions:
                        for v in source_versions:
                            if epoch_pat.search(v) and \
                                    v.endswith(':%s' % usn_version):
                                usn_version = v
                                break
                    version = debversion.DebVersion(usn_version)

                    if bin not in usn_db[rel]:
                        usn_db[rel][bin] = {}
                    if usn not in usn_db[rel][bin]:
                        usn_db[rel][bin][usn] = {}
                        usn_db[rel][bin][usn]['version'] = version
                        if 'cves' in raw[usn]:
                            usn_db[rel][bin][usn]['cves'] = raw[usn]['cves']
                            usn_db[rel][bin][usn]['cves'].sort()

    return usn_db
