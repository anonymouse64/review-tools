#!/usr/bin/python3
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

import json
import os
import shutil
import tempfile

from clickreviews.common import (
    debug,
    open_file_write,
    read_file_as_json_dict,
    MKDTEMP_PREFIX,
)
import clickreviews.email as email


def generate_report(pkg_db, seen_db):
    '''Generate a report for this pkg, consulting seen_db'''
    pkgname = pkg_db['name']

    report = '''A scan of this snap shows that it was built with packages from the Ubuntu
archive that have since received security updates. The following lists new USNs
for affected binary packages in each snap revision:
'''

    reference_urls = []

    for r in sorted(pkg_db['revisions']):
        if len(pkg_db['revisions'][r]['secnot-report']) == 0:
            continue

        architectures = pkg_db['revisions'][r]['architectures']
        architectures.sort()
        architectures = ", ".join(architectures)

        rev_header = "\nRevision r%s (%s; channel%s: %s)" % \
            (r, architectures,
             "s" if len(pkg_db['revisions'][r]['channels']) > 0 else "",
             ", ".join(pkg_db['revisions'][r]['channels']))
        shown_rev_header = False

        for p in sorted(pkg_db['revisions'][r]['secnot-report']):
            secnots = []
            for secnot in pkg_db['revisions'][r]['secnot-report'][p]:
                # only report new secnots, unless we don't know about this
                # revision
                if pkgname in seen_db and r in seen_db[pkgname] and \
                        secnot in seen_db[pkgname][r]:
                    continue
                secnots.append(secnot)
            secnots.sort()

            if len(secnots) > 0:
                if not shown_rev_header:
                    report += rev_header
                    shown_rev_header = True
                report += "\n * %s: %s" % (p, ", ".join(secnots))

            for secnot in secnots:
                url = "https://usn.ubuntu.com/%s/" % secnot
                if url not in reference_urls:
                    reference_urls.append(url)

        if shown_rev_header:
            report += "\n"

    if len(reference_urls) == 0:
        # nothing to report
        return ""

    report += '''
Simply rebuilding the snap will pull in the new security updates and resolve
this. If your snap also contains vendored code, now might be a good time to
review it for any needed updates.

Thank you for your snap and for attending to this matter.
'''

    reference_urls.sort()
    report += '''
References:
 * %s
''' % "\n * ".join(reference_urls)

    return report


def email_report(pkg_db, seen_db):
    '''Send email report for this pkgname'''
    pkgname = pkg_db['name']

    body = generate_report(pkg_db, seen_db)
    if body == "":
        return False

    subj = "%s contains outdated Ubuntu packages" % pkgname

    # Send to the publisher and any affected uploaders
    email_to_addr = pkg_db['publisher']
    if len(pkg_db['uploaders']) > 0:
        email_to_addr += ", %s" % ", ".join(pkg_db['uploaders'])
    if len(pkg_db['additional']) > 0:
        email_to_addr += ", %s" % ", ".join(pkg_db['additional'])
    email_to_addr += ", security@ubuntu.com"

    email.send(email_to_addr, subj, body)

    debug("Sent email for '%s'" % pkgname)
    return True


def read_seen_db(fn):
    if not os.path.exists(fn):
        # write out an empty seen_db
        with open_file_write(fn) as fd:
            fd.write('{}\n')
            fd.close()

    return read_file_as_json_dict(fn)


def update_seen(seen_fn, seen_db, pkg_db):
    pkgname = pkg_db['name']
    if pkgname not in seen_db:
        seen_db[pkgname] = {}

    # update to add new revisions
    for r in pkg_db['revisions']:
        if len(pkg_db['revisions'][r]['secnot-report']) == 0:
            continue

        if r not in seen_db[pkgname]:
            seen_db[pkgname][r] = []

        for p in pkg_db['revisions'][r]['secnot-report']:
            for secnot in pkg_db['revisions'][r]['secnot-report'][p]:
                if secnot not in seen_db[pkgname][r]:
                    seen_db[pkgname][r].append(secnot)
        seen_db[pkgname][r].sort()

    # remove old revisions
    remove = []
    for r in seen_db[pkgname]:
        if r not in pkg_db['revisions']:
            remove.append(r)
    if len(remove) > 0:
        for r in remove:
            del seen_db[pkgname][r]

    # TODO: update seen more efficiently (right now it is only 70k so not a
    # huge deal, but should probably move to sqlite)
    (fd, fn) = tempfile.mkstemp(prefix=MKDTEMP_PREFIX)
    os.write(fd, bytes(json.dumps(seen_db, sort_keys=True, indent=2), 'UTF-8'))
    os.close(fd)

    shutil.move(fn, seen_fn)
