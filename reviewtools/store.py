# Copyright (C) 2018-2020 Canonical Ltd.
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

import copy
import pprint
import re
import yaml

import reviewtools.debversion as debversion

from reviewtools.common import (
    debug,
    warn,
    get_os_codename,
    assign_type_to_dict_values,
    _add_error,  # make a class
)
import reviewtools.email as email
from reviewtools.overrides import (
    update_binaries_ignore,
    update_publisher_overrides,
    update_stage_packages,
    update_build_packages,
    update_package_version,
)
from reviewtools.sr_common import SnapReview

snap_to_release = {
    "base-18": "bionic",
    "core": "xenial",
    "core16": "xenial",
    "core18": "bionic",
    "core20": "focal",
}


# Used with auto-kernel. Assumes the binary is the meta-package with versions
# MAJ.MIN.MIC.ABI.NNN where the snap version is MAJ.MIN.MIC-ABI.NNN.
# The first three numbers for either package is the upstream kernel version
# (MAJ.MIN.MIC). MIC is always 0 since we don’t adjust for upstream stable
# version bumps e.g. 4.15.4
#
# ABI is what matches between the meta package and the binary kernel package
# in each kernel update. For the purposes of snap USN notifications, we will
# consider ABI without NNN since update practices dictate that ABI will change
# as part of the Ubuntu SRU cycle. This simplifies the comparison but also
# ensures that we don't notify when we shouldn't (eg, a packaging change revs
# NNN and now the kernel is considered out of date).
# NNN can drift as packaging fixes are made to each source package
# independently of each other.
def convert_canonical_kernel_version(s):
    v = s.split("~")[0]
    if not re.search(r"^[0-9]+\.[0-9]+\.[0-9]+-[0-9]+[-.]?.*", v):
        # Don't do any kernel version mocking if the version isn't in the
        # expected form
        return s

    # As we only care about abi, then mock up a build NNN that is very high
    if re.search(r"^[0-9]+\.[0-9]+\.[0-9]+-[0-9]+$", v):
        # Some kernels could match the pattern MAJ.MIN.MIC-ABI (e.g.
        # linux-generic-bbb=4.4.0-161), so we just append a high .NNN)
        v += ".999999"
    else:
        # We consider MAJ.MIN.MIC-ABI.NNN as well as MAJ.MIN.MIC-ABI-NNN,
        # so mock up a high NNN in both cases
        tmp = re.split("([.|-])", v)
        tmp[len(tmp) - 1] = "999999"
        v = "".join(tmp)

    # convert from MAJ.MIN.MIC-ABI.NNN to MAJ.MIN.MIC.ABI.NNN
    v = v.replace("-", ".")
    return v


# used with auto
def convert_canonical_app_version(s):
    v = s
    # discard last +git.deadbeef after 'ubuntu'
    if re.search(r"ubuntu.*\+", s):  # simplistic
        v = s.rsplit("+", 1)[0]

    return v


def get_faked_build_and_stage_packages(m):
    """fake up build and stage-packages from overrides"""
    # if the snap specifies a base, see if the override has a <snap>/<base>
    # key. If not, fallback to <snap>
    snapbase = ""
    if "base" in m:
        snapbase = m["base"]

    key = "%s/%s" % (m["name"], snapbase)
    if key not in update_stage_packages:
        key = m["name"]

    # Performing a deepcopy of m as we are adding side-effects to the
    # original manifest dict otherwise
    manifest_with_faked_packages = copy.deepcopy(m)

    # Always append faked staged packages if there are any parts since for now
    # we are unconditionally faking 'snapcraft' in all snaps with a manifest to
    # the faked part.
    # TODO: perhaps clean this up when implementing build-packages fully.
    if (
        "parts" in manifest_with_faked_packages
        and manifest_with_faked_packages["parts"]
    ):
        if (
            "primed-stage-packages" in manifest_with_faked_packages
            and manifest_with_faked_packages["primed-stage-packages"] is not None
        ):
            append_fake_packages_to_manifest(key, manifest_with_faked_packages, True)
        else:
            append_fake_packages_to_manifest(key, manifest_with_faked_packages, False)
    return manifest_with_faked_packages


# append_fake_packages_to_manifest() will append packages from the
# update_stage_packages and update_build_packages override in the manifest.
# For update_stage_packages, will append to primed-stage-packages when
# primed-stage-packages is present, otherwise it will insert those packages
# into the 'faked-by-review-tools' part. For update_build_packages, will
# insert those into the 'faked-by-review-tools' part always
def append_fake_packages_to_manifest(
    key, manifest_with_faked_packages, is_primed_stage_present
):
    # TODO: consider using differently faked parts for stage and build when
    #  implementing build-packages fully.
    fake_key = "faked-by-review-tools"
    if (
        "parts" in manifest_with_faked_packages
        and manifest_with_faked_packages["parts"] is not None
        and fake_key not in manifest_with_faked_packages["parts"]
    ):
        manifest_with_faked_packages["parts"][fake_key] = {}
        manifest_with_faked_packages["parts"][fake_key]["plugin"] = "null"

        for i in ["build-packages", "prime", "stage", "stage-packages"]:
            manifest_with_faked_packages["parts"][fake_key][i] = []

        # The override for update_stage_packages is:
        #   update_stage_packages = {'<snap>': {'<deb>': '<version>|auto*'}}
        if key in update_stage_packages:
            for pkg in update_stage_packages[key]:
                version = update_stage_packages[key][pkg]
                if version == "auto":
                    version = convert_canonical_app_version(
                        manifest_with_faked_packages["version"]
                    )
                elif version == "auto-kernel":
                    version = convert_canonical_kernel_version(
                        manifest_with_faked_packages["version"]
                    )
                # append to prime-stage-packages if present, else insert into the
                # stage-packages of our faked part
                if is_primed_stage_present:
                    manifest_with_faked_packages["primed-stage-packages"].append(
                        "%s=%s" % (pkg, version)
                    )
                else:
                    manifest_with_faked_packages["parts"][fake_key][
                        "stage-packages"
                    ].append("%s=%s" % (pkg, version))

        # The override for update_build_packages is:
        #   update_build_packages = {'<snap>': {'<deb>': '<version>|auto'}}
        #   For this implementation we are only faking snapcraft for every snap
        # TODO: update when fully support build-packages
        for build_packages in update_build_packages.values():
            for pkg_name in build_packages:
                version = build_packages[pkg_name]
                if pkg_name == "snapcraft" and version == "auto":
                    pkg_version = get_snapcraft_version_from_manifest(
                        manifest_with_faked_packages
                    )
                    if pkg_version:
                        manifest_with_faked_packages["parts"][fake_key][
                            "build-packages"
                        ].append("%s=%s" % (pkg_name, pkg_version))


def get_pkg_revisions(item, secnot_db, errors):
    for i in ["name", "publisher_email", "revisions"]:
        if i not in item:
            raise ValueError("required field '%s' not found" % i)

    pkg_db = {}
    pkg_db["revisions"] = {}

    # we've already verified these are present
    pkg_db["name"] = item["name"]
    pkg_db["publisher"] = email.sanitize_addr(item["publisher_email"])
    if pkg_db["publisher"] == "":
        _add_error(
            pkg_db["name"], errors, "publisher_email '%s' invalid" % pkg_db["publisher"]
        )
        return pkg_db

    pkg_db["collaborators"] = []
    if "collaborators" in item:
        for c in item["collaborators"]:
            if not isinstance(c, dict) or "email" not in c:
                continue
            cEmail = email.sanitize_addr(c["email"])
            if cEmail == "":
                # Don't treat this as fatal for this snap
                _add_error(
                    pkg_db["name"], errors, "collaborator email '%s' invalid" % cEmail
                )
            elif (
                cEmail != pkg_db["publisher"] and cEmail not in pkg_db["collaborators"]
            ):
                pkg_db["collaborators"].append(cEmail)

    for rev in item["revisions"]:
        if "revision" not in rev:
            _add_error(pkg_db["name"], errors, "no revisions found")
            continue

        r = str(rev["revision"])  # ensure yaml and json agree on type
        debug("Checking %s r%s" % (item["name"], r))

        if "manifest_yaml" not in rev:
            _add_error(
                pkg_db["name"], errors, "manifest_yaml missing for revision '%s'" % r
            )
            continue

        try:
            m = yaml.load(rev["manifest_yaml"], Loader=yaml.SafeLoader)
            if m is None:
                continue
            m = get_faked_build_and_stage_packages(m)
            normalize_and_verify_snap_manifest(m)
        except Exception as e:
            _add_error(
                pkg_db["name"],
                errors,
                "error loading manifest for revision '%s': %s" % (r, e),
            )
            continue

        try:
            report = get_secnots_for_manifest(m, secnot_db)
        except ValueError as e:
            if "not found in security notification database" not in str(e):
                _add_error(pkg_db["name"], errors, "(revision '%s') %s" % (r, e))
            continue

        if r not in pkg_db["revisions"]:
            pkg_db["revisions"][r] = {}
        pkg_db["revisions"][r]["channels"] = rev["channels"]
        pkg_db["revisions"][r]["architectures"] = rev["architectures"]
        pkg_db["revisions"][r]["secnot-report"] = report

        pkg_db["snap_type"] = "app"
        if "type" in m:
            pkg_db["snap_type"] = m["type"]

        if "uploaders" not in pkg_db:
            pkg_db["uploaders"] = []
        if "uploader_email" in rev:
            uploader = email.sanitize_addr(rev["uploader_email"])
            if uploader == "":
                # Don't treat this as fatal for this snap
                _add_error(
                    pkg_db["name"], errors, "uploader_email '%s' invalid" % uploader
                )
            elif (
                uploader != pkg_db["publisher"] and uploader not in pkg_db["uploaders"]
            ):
                pkg_db["uploaders"].append(uploader)

        if "additional" not in pkg_db:
            pkg_db["additional"] = []
        if (
            pkg_db["publisher"] in update_publisher_overrides
            and pkg_db["name"] in update_publisher_overrides[pkg_db["publisher"]]
        ):
            for eml in update_publisher_overrides[pkg_db["publisher"]][pkg_db["name"]]:
                if (
                    eml != pkg_db["publisher"]
                    and eml not in pkg_db["collaborators"]
                    and eml not in pkg_db["uploaders"]
                    and eml not in pkg_db["additional"]
                ):
                    pkg_db["additional"].append(eml)

    return pkg_db


def get_shared_snap_without_override(store_db):
    """Report snaps that use a shared email but don't have an entry for
       additional addresses.
    """
    missing = {}
    for item in store_db:
        if "name" not in item or "publisher_email" not in item:
            continue

        if item["publisher_email"] not in update_publisher_overrides:
            continue

        if item["name"] not in update_publisher_overrides[item["publisher_email"]]:
            if item["publisher_email"] not in missing:
                missing[item["publisher_email"]] = []
            if item["name"] not in missing[item["publisher_email"]]:
                missing[item["publisher_email"]].append(item["name"])

    return missing


# Since Snapcraft 3.10, the manifest includes a 'primed-stage-packages'
# section aiming to reduce the number of false positive alerts that are
# caused by staged-packages listing packages that are not eventually
# present in the snap. https://snapcraft.io/docs/release-notes-snapcraft-3-10.
# TODO: support for build-packages is not fully implemented yet.
def get_staged_and_build_packages_from_manifest(m):
    """Obtain list of packages in primed-stage-packages if section is present.
       If not, obtain it from stage-packages for various parts instead
    """
    if "parts" not in m:
        debug("Could not find 'parts' in manifest")
        return None

    if not m["parts"]:
        debug("'parts' exists in manifest but it is empty")
        return None

    d = {}

    manifest_has_primed_staged_section = False

    if "primed-stage-packages" in m and m["primed-stage-packages"] is not None:
        manifest_has_primed_staged_section = True
        # Note, prime-stage-packages is grouped with stage-packages
        get_packages_from_manifest_section(d, m["primed-stage-packages"], "staged")

    for part in m["parts"]:
        # stage-packages part is only analyzed if primed-stage-packages is not
        # present.
        if not manifest_has_primed_staged_section:
            if (
                "stage-packages" in m["parts"][part]
                and m["parts"][part]["stage-packages"] is not None
            ):
                get_packages_from_manifest_section(
                    d, m["parts"][part]["stage-packages"], "staged"
                )

        # Only adding build-packages if part is fake. This will be improved
        # once the full support for build-packages is added
        if part == "faked-by-review-tools":
            if (
                "build-packages" in m["parts"][part]
                and m["parts"][part]["build-packages"] is not None
            ):
                get_packages_from_manifest_section(
                    d, m["parts"][part]["build-packages"], "build"
                )

    if len(d) == 0:
        return None

    debug("\n" + pprint.pformat(d))
    return d


# package_type helps to group the pkgs based on the manifest section:
# primed-stage-packages and stage-packages from each part are grouped
# into the stage-packages key. build-packages are added to the build-packages
# key.
def get_packages_from_manifest_section(d, manifest_section, package_type):
    """Obtain packages from a given manifest section (primed-stage-packages
       or stage-packages along with any build-packages for a given part)
    """
    for entry in manifest_section:
        if "=" not in entry:
            warn("'%s' not properly formatted. Skipping" % entry)
            continue
        pkg, ver = entry.split("=")
        if pkg in update_binaries_ignore:
            debug("Skipping ignored binary: '%s'" % pkg)
            continue
        if package_type not in d:
            d[package_type] = {}
        if pkg not in d[package_type]:
            d[package_type][pkg] = []
        if ver not in d[package_type][pkg]:
            d[package_type][pkg].append(ver)


def normalize_and_verify_snap_manifest(m):
    """Normalize manifest (ie, assign empty types if None for SafeLoader
       defaults) and verify snap manifest is well-formed and has everything we
       expect"""
    # normalize toplevel keys
    assign_type_to_dict_values(m, SnapReview.snap_manifest_required)
    assign_type_to_dict_values(m, SnapReview.snap_manifest_optional)

    if "parts" in m and isinstance(m["parts"], dict):
        for p in m["parts"]:
            # normalize parts keys
            partm = m["parts"][p]
            assign_type_to_dict_values(partm, SnapReview.snap_manifest_parts_required)
            assign_type_to_dict_values(partm, SnapReview.snap_manifest_parts_optional)
            m["parts"][p] = partm

    (valid, level, msg) = SnapReview.verify_snap_manifest(SnapReview, m)
    if not valid:
        raise ValueError(msg)


def get_secnots_for_manifest(m, secnot_db, with_cves=False):
    """Find new security notifications for packages in the manifest"""
    debug("snap/manifest.yaml:\n" + pprint.pformat(m))

    rel = get_ubuntu_release_from_manifest(m)  # can raise ValueError
    stage_and_build_pkgs = get_staged_and_build_packages_from_manifest(m)
    if rel not in secnot_db:
        raise ValueError("'%s' not found in security notification database" % rel)

    pending_secnots = {}

    if stage_and_build_pkgs is None:
        debug("no stage-packages found")
        return pending_secnots
    # Since stage_and_build_pkgs can have stage-packages and build-packages
    # keys, adding secnots into each group
    for pkg_type in stage_and_build_pkgs:
        for pkg in stage_and_build_pkgs[pkg_type]:
            if pkg in secnot_db[rel]:
                for v in stage_and_build_pkgs[pkg_type][pkg]:
                    pkgversion = debversion.DebVersion(v)
                    for secnot in secnot_db[rel][pkg]:
                        # The override for update_package_version is:
                        #   update_package_version = {'<pkg>': {'<part-key>':
                        #   '<version>'}
                        # TODO: update when fully support installed-snaps
                        #  or further snapcraft updates
                        secnotversion = None
                        if pkg in update_package_version:
                            for part in m["parts"]:
                                for key in update_package_version[pkg]:
                                    if key in m["parts"][part]:
                                        for entry in m["parts"][part][key]:
                                            if "=" not in entry:
                                                warn(
                                                    "'%s' not properly "
                                                    "formatted. Skipping" % entry
                                                )
                                                continue
                                            if pkg == entry.split("=")[0]:
                                                secnotversion = debversion.DebVersion(
                                                    update_package_version[pkg][key]
                                                )
                                                # For this situation is enough
                                                # to find pkg in at least one
                                                # part and break as the version
                                                # will come from the override
                                                break
                        if secnotversion is None:
                            secnotversion = secnot_db[rel][pkg][secnot]["version"]

                        if debversion.compare(pkgversion, secnotversion) < 0:
                            debug(
                                "adding %s: %s (pkg:%s < secnot:%s)"
                                % (
                                    pkg,
                                    secnot,
                                    pkgversion.full_version,
                                    secnotversion.full_version,
                                )
                            )
                            # Only adding pkg_type if there is a pending secnote
                            if pkg_type not in pending_secnots:
                                pending_secnots[pkg_type] = {}
                            if pkg not in pending_secnots[pkg_type]:
                                if with_cves:
                                    pending_secnots[pkg_type][pkg] = {}
                                else:
                                    pending_secnots[pkg_type][pkg] = []
                            if secnot not in pending_secnots[pkg_type][pkg]:
                                if with_cves:
                                    pending_secnots[pkg_type][pkg][secnot] = secnot_db[
                                        rel
                                    ][pkg][secnot]["cves"]
                                else:
                                    pending_secnots[pkg_type][pkg].append(secnot)
                        else:
                            debug(
                                "skipping %s: %s (pkg:%s >= secnot:%s)"
                                % (
                                    pkg,
                                    secnot,
                                    pkgversion.full_version,
                                    secnotversion.full_version,
                                )
                            )

                        if (
                            pkg_type in pending_secnots
                            and pkg in pending_secnots[pkg_type]
                            and not with_cves
                        ):
                            pending_secnots[pkg_type][pkg].sort()
    return pending_secnots


def get_ubuntu_release_from_manifest(m):
    """Determine the Ubuntu release from the manifest"""
    if "parts" not in m:
        raise ValueError(
            "Could not determine Ubuntu release ('parts' not in " "manifest)"
        )

    ubuntu_release = None

    # Record any installed snaps where we know the Ubuntu release that should
    # be used
    installed_snaps = []
    for part in m["parts"]:
        if "installed-snaps" in m["parts"][part]:
            for entry in m["parts"][part]["installed-snaps"]:
                if "=" not in entry:
                    warn("'%s' not properly formatted. Skipping" % entry)
                    continue
                pkg = entry.split("=")[0]  # we don't care about the version

                if pkg in snap_to_release and pkg not in installed_snaps:
                    installed_snaps.append(pkg)

    # if we have an os-release, let's try to use it, otherwise fall back to old
    # behavior
    if "snapcraft-os-release-id" in m and "snapcraft-os-release-version-id" in m:
        try:
            ubuntu_release = get_os_codename(
                m["snapcraft-os-release-id"], m["snapcraft-os-release-version-id"]
            )
            debug("Ubuntu release=%s" % ubuntu_release)
            return ubuntu_release
        except ValueError:
            pass

    # Couldn't determine the ubuntu release from snapcraft-os-release-id and
    # snapcraft-os-release-version-id, so let's make some guesses
    default = "xenial"

    # if no base is specified, use default
    if "base" not in m:
        ubuntu_release = default

    # if we have a base we know about, use it
    elif m["base"] in snap_to_release:
        ubuntu_release = snap_to_release[m["base"]]

    # otherwise we have a base we don't know about. Let's try to guess
    else:
        # make an educated guess if one installed snap
        if len(installed_snaps) == 1:
            ubuntu_release = snap_to_release[installed_snaps[0]]

        # fake "ubuntu" and see if the ID matches something we know about.
        # XXX: if/when snapcraft is updated to include ID_LIKE (eg,
        # snapcraft-os-release-version-id), we could consider this as well.
        elif "snapcraft-os-release-version-id" in m:
            try:
                ubuntu_release = get_os_codename(
                    "ubuntu", m["snapcraft-os-release-version-id"]
                )
                debug(
                    "Could not determine Ubuntu release (non-core base)."
                    "Guessing based on snapcraft-os-release-version-id: %s"
                    % (m["snapcraft-os-release-version-id"])
                )
            except ValueError:
                ubuntu_release = None

        if ubuntu_release is None:
            # no installed snaps, use default
            if len(installed_snaps) == 0:
                debug(
                    "Could not determine Ubuntu release (non-core base with no "
                    "installed snaps). Defaulting to '%s'" % default
                )
                ubuntu_release = default

            # error if more than one installed snap since we can't guess (note,
            # we already checked for installed_snaps == 1, above)
            elif len(installed_snaps) > 1:
                raise ValueError(
                    "Could not determine Ubuntu release (non-core base with "
                    "multiple installed snaps: %s)" % ",".join(installed_snaps)
                )

    debug("Ubuntu release=%s" % ubuntu_release)

    return ubuntu_release


def get_snapcraft_version_from_manifest(m):
    if (
        "snapcraft-version" in m
        and m["snapcraft-version"] is not None
        and m["snapcraft-version"]
    ):
        try:
            return debversion.DebVersion(m["snapcraft-version"])
        except ValueError as e:
            warn("Invalid Snapcraft version: %s" % e)
            return None
