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

import pprint
import yaml

import clickreviews.debversion as debversion

from clickreviews.common import (
    debug,
    warn,
    get_os_codename,
    _add_error,  # make a class
)
import clickreviews.email as email
from clickreviews.overrides import (
    update_binaries_ignore,
    update_publisher_overrides,
)
from clickreviews.sr_common import (
    SnapReview,
)

snap_to_release = {'base-18': 'bionic',
                   'core': 'xenial',
                   'core16': 'xenial',
                   'core18': 'bionic',
                   }


def get_pkg_revisions(item, secnot_db, errors):
    for i in ['name', 'publisher_email', 'revisions']:
        if i not in item:
            raise ValueError("required field '%s' not found" % i)

    pkg_db = {}
    pkg_db['revisions'] = {}

    # we've already verified these are present
    pkg_db['name'] = item['name']
    pkg_db['publisher'] = email.sanitize_addr(item['publisher_email'])
    if pkg_db['publisher'] == '':
        _add_error(pkg_db['name'], errors, "publisher_email '%s' invalid" %
                   pkg_db['publisher'])
        return pkg_db

    for rev in item['revisions']:
        if 'revision' not in rev:
            _add_error(pkg_db['name'], errors, "no revisions found")
            continue

        r = str(rev['revision'])  # ensure yaml and json agree on type
        debug("Checking %s r%s" % (item['name'], r))

        if 'manifest_yaml' not in rev:
            _add_error(pkg_db['name'], errors,
                       "manifest_yaml missing for revision '%s'" % r)
            continue

        m = yaml.load(rev['manifest_yaml'])
        verify_snap_manifest(m)
        try:
            report = get_secnots_for_manifest(m, secnot_db)
        except ValueError as e:
            _add_error(pkg_db['name'], errors, "%s" % e)
            continue

        if r not in pkg_db['revisions']:
            pkg_db['revisions'][r] = {}
        pkg_db['revisions'][r]['channels'] = rev['channels']
        pkg_db['revisions'][r]['architectures'] = rev['architectures']
        pkg_db['revisions'][r]['secnot-report'] = report
        if 'uploaders' not in pkg_db:
            pkg_db['uploaders'] = []
        if 'uploader_email' in rev:
            uploader = email.sanitize_addr(rev['uploader_email'])
            if uploader == '':
                # Don't treat this as fatal for this snap
                _add_error(pkg_db['name'], errors,
                           "uploader_email '%s' invalid" % uploader)
            elif uploader != pkg_db['publisher'] and \
                    uploader not in pkg_db['uploaders']:
                pkg_db['uploaders'].append(uploader)

        if 'additional' not in pkg_db:
            pkg_db['additional'] = []
        if pkg_db['publisher'] in update_publisher_overrides and \
                pkg_db['name'] in \
                update_publisher_overrides[pkg_db['publisher']]:
            for eml in update_publisher_overrides[pkg_db['publisher']][pkg_db['name']]:
                if eml != pkg_db['publisher'] and \
                        eml not in pkg_db['uploaders'] and \
                        eml not in pkg_db['additional']:
                    pkg_db['additional'].append(eml)

    return pkg_db


def get_shared_snap_without_override(store_db):
    '''Report snaps that use a shared email but don't have an entry for
       additional addresses.
    '''
    missing = {}
    for item in store_db:
        if 'name' not in item or 'publisher_email' not in item:
            continue

        if item['publisher_email'] not in update_publisher_overrides:
            continue

        if item['name'] not in \
                update_publisher_overrides[item['publisher_email']]:
            if item['publisher_email'] not in missing:
                missing[item['publisher_email']] = []
            if item['name'] not in missing[item['publisher_email']]:
                missing[item['publisher_email']].append(item['name'])

    return missing


def get_staged_packages_from_manifest(m):
    '''Obtain list of packages in stage-packages for various parts'''
    if 'parts' not in m:
        debug("Could not find 'parts' in manifest")
        return None

    d = {}
    for part in m['parts']:
        if 'stage-packages' in m['parts'][part]:
            for entry in m['parts'][part]['stage-packages']:
                if '=' not in entry:
                    warn("'%s' not properly formatted. Skipping" % entry)
                    continue
                pkg, ver = entry.split('=')

                if pkg in update_binaries_ignore:
                    debug("Skipping ignored binary: '%s'" % pkg)
                    continue

                if pkg not in d:
                    d[pkg] = []
                if ver not in d[pkg]:
                    d[pkg].append(ver)

    if len(d) == 0:
        return None

    debug("\n" + pprint.pformat(d))
    return d


def verify_snap_manifest(m):
    '''Verify snap manifest is well-formed and has everything we expect'''
    (valid, level, msg) = SnapReview.verify_snap_manifest(SnapReview, m)
    if not valid:
        raise ValueError(msg)


def get_secnots_for_manifest(m, secnot_db):
    '''Find new security notifications for packages in the manifest'''
    debug("snap/manifest.yaml:\n" + pprint.pformat(m))

    rel = get_ubuntu_release_from_manifest(m)  # can raise ValueError
    pkgs = get_staged_packages_from_manifest(m)
    if rel not in secnot_db:
        raise ValueError("'%s' not found in security notification database" %
                         rel)

    pending_secnots = {}

    if pkgs is None:
        debug("no stage-packages found")
        return pending_secnots

    for pkg in pkgs:
        if pkg in secnot_db[rel]:
            for v in pkgs[pkg]:
                pkgversion = debversion.DebVersion(v)
                for secnot in secnot_db[rel][pkg]:
                    secnotversion = secnot_db[rel][pkg][secnot]
                    if debversion.compare(pkgversion, secnotversion) < 0:
                        debug('adding %s: %s (pkg:%s < secnot:%s)' %
                              (pkg, secnot, pkgversion.full_version,
                               secnotversion.full_version))
                        if pkg not in pending_secnots:
                            pending_secnots[pkg] = []
                        if secnot not in pending_secnots[pkg]:
                            pending_secnots[pkg].append(secnot)
                    else:
                        debug('skipping %s: %s (pkg:%s >= secnot:%s)' %
                              (pkg, secnot, pkgversion.full_version,
                               secnotversion.full_version))

                    if pkg in pending_secnots:
                        pending_secnots[pkg].sort()

    return pending_secnots


# XXX: When LP: #1768820 is fixed, just use the manifest.yaml key
def get_ubuntu_release_from_manifest(m):
    '''Determine the Ubuntu release from the manifest'''
    if 'parts' not in m:
        raise ValueError("Could not determine Ubuntu release ('parts' not in "
                         "manifest)")

    installed_snaps = []
    for part in m['parts']:
        if 'installed-snaps' in m['parts'][part]:
            for entry in m['parts'][part]['installed-snaps']:
                if '=' not in entry:
                    warn("'%s' not properly formatted. Skipping" % entry)
                pkg = entry.split('=')[0]  # we don't care about the version

                if pkg in snap_to_release and pkg not in installed_snaps:
                    installed_snaps.append(pkg)

    # if we have an os-release, let's try to use it, otherwise fall back to old
    # behavior
    if 'snapcraft-os-release-id' in m and \
            'snapcraft-os-release-version-id' in m:
        try:
            ubuntu_release = get_os_codename(m['snapcraft-os-release-id'],
                                             m['snapcraft-os-release-version-id'])
            debug("Ubuntu release=%s" % ubuntu_release)
            return ubuntu_release
        except ValueError:
            pass

    if len(installed_snaps) == 0:
        default = "xenial"
        debug("Could not determine Ubuntu release (no installed snaps). "
              "Defaulting to '%s'" % default)
        ubuntu_release = default
    else:
        # NOTE: this will have to change if a snap ever has multiple cores or
        # base snaps installed
        if len(installed_snaps) > 1:
            raise ValueError("Could not determine Ubuntu release (multiple "
                             "bases/cores: %s)" % ",".join(installed_snaps))

        ubuntu_release = snap_to_release[installed_snaps[0]]

    debug("Ubuntu release=%s" % ubuntu_release)

    return ubuntu_release
