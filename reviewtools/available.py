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

from reviewtools.common import (
    debug,
    warn,
    open_file_write,
    read_file_as_json_dict,
    MKDTEMP_PREFIX,
    _add_error,  # make a class
    get_rock_manifest,
    get_snap_manifest,
)
import reviewtools.email as email

from reviewtools.store import (
    get_pkg_revisions,
    get_secnots_for_manifest,
    get_shared_snap_without_override,
    get_faked_build_and_stage_packages,
)
from reviewtools.usn import read_usn_db

email_update_required_text = """A scan of this %s shows that it was built with packages from the Ubuntu
archive that have since received security updates. """
email_additional_build_pkgs_text = """In addition, the following lists new USNs for affected build packages in
each snap revision:
%s
"""
email_kernel_update_required_text = """A scan of this snap shows that it was built using sources based on a kernel
from the Ubuntu archive that has since received security updates. The
following lists new USNs for the Ubuntu kernel that the snap is based on in
each snap revision:
%s
"""
email_thanks_and_references_text = """

Thank you for your %s and for attending to this matter.

References:
 * %s
"""
email_rebuild_snap_text = (
    """Simply rebuilding the %s will pull in the new security updates and
resolve this. If your %s also contains vendored code, now might be a
good time to review it for any needed updates."""
    + email_thanks_and_references_text
)

email_rebuild_kernel_snap_text = """Updating the snap's git tree, adjusting the version in the snapcraft.yaml
to match that of the Ubuntu kernel this snap is based on and rebuilding the
snap should pull in the new security updates and resolve this."""

email_templates = {
    "default": (
        email_update_required_text
        + """The following lists new
USNs for affected binary packages in each %s revision:
%s
"""
        + email_rebuild_snap_text
    ),
    "build-pkgs-only": (
        email_update_required_text
        + """The following lists new
USNs for affected build packages in each %s revision:
%s
"""
        + email_rebuild_snap_text
    ),
    "build-and-stage-pkgs": (
        email_update_required_text
        + """The following lists new
USNs for affected binary packages in each snap revision:
%s
"""
        + email_additional_build_pkgs_text
        + email_rebuild_snap_text
    ),
    "kernel": (
        email_kernel_update_required_text
        + email_rebuild_kernel_snap_text
        + email_thanks_and_references_text
    ),
    "kernel-build-pkgs-only": (
        email_update_required_text
        + """The following lists new
USNs for affected build packages in each snap revision:
%s
"""
        + email_rebuild_kernel_snap_text
        + email_thanks_and_references_text
    ),
    "kernel-and-build-pkgs": (
        email_kernel_update_required_text
        + email_additional_build_pkgs_text
        + email_rebuild_kernel_snap_text
        + email_thanks_and_references_text
    ),
}


def _secnot_report_for_pkg(pkg_db, seen_db):
    """Generate a report for this pkg, consulting seen_db"""
    pkgname = pkg_db["name"]

    reference_urls = []

    # Since now the report can contain USNs for stage-packages only,
    # USNs for build-packages only, or both, then we prepare two reports
    # that will be joined later if needed
    stage_pkgs_report = ""
    build_pkgs_report = ""

    report_contains_build_pkgs = False
    report_contains_stage_pkgs = False

    for r in sorted(pkg_db["revisions"]):
        if len(pkg_db["revisions"][r]["secnot-report"]) == 0:
            continue

        architectures = pkg_db["revisions"][r]["architectures"]
        architectures.sort()
        architectures = ", ".join(architectures)

        rev_header = "\nRevision r%s (%s; channel%s: %s)" % (
            r,
            architectures,
            "s" if len(pkg_db["revisions"][r]["channels"]) > 0 else "",
            ", ".join(pkg_db["revisions"][r]["channels"]),
        )
        shown_rev_header_for_stage_pkgs = False
        shown_rev_header_for_build_pkgs = False

        # secnot-report report has 2 sections: staged (for secnots related to
        # primed-stage-packages and stage-packages) and build (for secnots
        # related to build-packages)
        for sec_note_per_pkg_type in pkg_db["revisions"][r]["secnot-report"]:
            for p in sorted(
                pkg_db["revisions"][r]["secnot-report"][sec_note_per_pkg_type]
            ):
                secnots = []
                for secnot in pkg_db["revisions"][r]["secnot-report"][
                    sec_note_per_pkg_type
                ][p]:
                    # only report new secnots, unless we don't know about this
                    # revision
                    if (
                        pkgname in seen_db
                        and r in seen_db[pkgname]
                        and secnot in seen_db[pkgname][r]
                    ):
                        continue
                    secnots.append(secnot)
                    # This is the fix for LP bug #1906827
                    if (
                        sec_note_per_pkg_type == "staged"
                        and not report_contains_stage_pkgs
                    ):
                        report_contains_stage_pkgs = True
                    elif (
                        sec_note_per_pkg_type == "build"
                        and not report_contains_build_pkgs
                    ):
                        report_contains_build_pkgs = True
                secnots.sort()

                if len(secnots) > 0:
                    if (
                        sec_note_per_pkg_type == "staged"
                        and not shown_rev_header_for_stage_pkgs
                    ):
                        stage_pkgs_report += rev_header
                        shown_rev_header_for_stage_pkgs = True
                    elif (
                        sec_note_per_pkg_type == "build"
                        and not shown_rev_header_for_build_pkgs
                    ):
                        build_pkgs_report += rev_header
                        shown_rev_header_for_build_pkgs = True

                    if sec_note_per_pkg_type == "staged":
                        stage_pkgs_report += "\n * %s: %s" % (p, ", ".join(secnots))
                    elif sec_note_per_pkg_type == "build":
                        build_pkgs_report += "\n * %s: %s" % (p, ", ".join(secnots))

                for secnot in secnots:
                    url = "https://ubuntu.com/security/notices/USN-%s/" % secnot
                    if url not in reference_urls:
                        reference_urls.append(url)
        if shown_rev_header_for_stage_pkgs and report_contains_stage_pkgs:
            stage_pkgs_report += "\n"
        if shown_rev_header_for_build_pkgs and report_contains_build_pkgs:
            build_pkgs_report += "\n"

    if len(reference_urls) == 0:
        # nothing to report
        return "", "", False, False

    reference_urls.sort()
    template = "default"
    pkg_type = "snap"
    if "snap_type" in pkg_db and pkg_db["snap_type"] == "kernel":
        # TODO: update when fully support build-packages
        if report_contains_stage_pkgs and report_contains_build_pkgs:
            subj = (
                "%s built from outdated Ubuntu kernel and with outdated Ubuntu packages"
                % pkgname
            )
            body = email_templates["kernel-and-build-pkgs"] % (
                stage_pkgs_report,
                build_pkgs_report,
                pkg_type,
                "\n * ".join(reference_urls),
            )
        elif report_contains_stage_pkgs:
            subj = "%s built from outdated Ubuntu kernel" % pkgname
            body = email_templates["kernel"] % (
                stage_pkgs_report,
                pkg_type,
                "\n * ".join(reference_urls),
            )
        elif report_contains_build_pkgs:
            subj = "%s was built with outdated Ubuntu packages" % pkgname
            body = email_templates["kernel-build-pkgs-only"] % (
                pkg_type,
                build_pkgs_report,
                pkg_type,
                "\n * ".join(reference_urls),
            )
        return (
            subj,
            body,
            report_contains_stage_pkgs,
            report_contains_build_pkgs,
        )
    elif "rock_type" in pkg_db and pkg_db["rock_type"] == "oci":
        pkg_type = "rock"
        # ROCKs v1 only contain staged packages
        if report_contains_stage_pkgs:
            subj = "%s contains outdated Ubuntu packages" % pkgname
            return (
                subj,
                email_templates[template]
                % (
                    pkg_type,
                    pkg_type,
                    stage_pkgs_report,
                    pkg_type,
                    pkg_type,
                    pkg_type,
                    "\n * ".join(reference_urls),
                ),
                report_contains_stage_pkgs,
                False,  # TODO: eventually, report_contains_build_pks
            )
    elif report_contains_stage_pkgs and report_contains_build_pkgs:
        # Template text containing updates for staged and build packages
        subj = "%s contains and was built with outdated Ubuntu packages" % pkgname
        template = "build-and-stage-pkgs"
        return (
            subj,
            email_templates[template]
            % (
                pkg_type,
                stage_pkgs_report,
                build_pkgs_report,
                pkg_type,
                pkg_type,
                pkg_type,
                "\n * ".join(reference_urls),
            ),
            report_contains_stage_pkgs,
            report_contains_build_pkgs,
        )
    elif report_contains_build_pkgs and not report_contains_stage_pkgs:
        # Template text containing updates for build packages only
        subj = "%s was built with outdated Ubuntu packages" % pkgname
        template = "build-pkgs-only"
        return (
            subj,
            email_templates[template]
            % (
                pkg_type,
                pkg_type,
                build_pkgs_report,
                pkg_type,
                pkg_type,
                pkg_type,
                "\n * ".join(reference_urls),
            ),
            False,
            report_contains_build_pkgs,
        )
    else:
        # Template text containing updates for staged packages only (default)
        subj = "%s contains outdated Ubuntu packages" % pkgname
        return (
            subj,
            email_templates[template]
            % (
                pkg_type,
                pkg_type,
                stage_pkgs_report,
                pkg_type,
                pkg_type,
                pkg_type,
                "\n * ".join(reference_urls),
            ),
            report_contains_stage_pkgs,
            False,  # TODO: eventually, report_contains_build_pks
        )


def _email_report_for_pkg(pkg_db, seen_db):
    """Send email report for this pkgname"""
    pkgname = pkg_db["name"]
    (
        subj,
        body,
        report_contains_stage_pks,
        report_contains_build_pks,
    ) = _secnot_report_for_pkg(pkg_db, seen_db)
    if body == "":
        return (None, None, None)

    # Send to the publisher and any collaborators. If no collaborators,
    # fallback to any uploaders for the revision
    email_to_addr = pkg_db["publisher"]
    if len(pkg_db["collaborators"]) > 0:
        email_to_addr += ", %s" % ", ".join(pkg_db["collaborators"])
    elif len(pkg_db["uploaders"]) > 0:
        email_to_addr += ", %s" % ", ".join(pkg_db["uploaders"])
    if len(pkg_db["additional"]) > 0:
        email_to_addr += ", %s" % ", ".join(pkg_db["additional"])
    # temporary
    bcc = "alex.murray@canonical.com, emilia.torino@canonical.com"

    email.send(email_to_addr, subj, body, bcc)

    debug("Sent email for '%s'" % pkgname)
    return (email_to_addr, subj, body)


def read_seen_db(fn):
    if not os.path.exists(fn):
        # write out an empty seen_db
        with open_file_write(fn) as fd:
            fd.write("{}\n")
            fd.close()

    return read_file_as_json_dict(fn)


def _update_seen(seen_fn, seen_db, pkg_db):
    pkgname = pkg_db["name"]
    if pkgname not in seen_db:
        seen_db[pkgname] = {}

    # update to add new revisions
    for r in pkg_db["revisions"]:
        if len(pkg_db["revisions"][r]["secnot-report"]) == 0:
            continue

        if r not in seen_db[pkgname]:
            seen_db[pkgname][r] = []

        # secnot-report can contain now stage-packages and build-packages
        # sections
        for sec_note_per_pkg_type in pkg_db["revisions"][r]["secnot-report"]:
            for p in pkg_db["revisions"][r]["secnot-report"][sec_note_per_pkg_type]:
                for secnot in pkg_db["revisions"][r]["secnot-report"][
                    sec_note_per_pkg_type
                ][p]:
                    if secnot not in seen_db[pkgname][r]:
                        seen_db[pkgname][r].append(secnot)
        seen_db[pkgname][r].sort()

    # remove old revisions
    remove = []
    for r in seen_db[pkgname]:
        if r not in pkg_db["revisions"]:
            remove.append(r)
    if len(remove) > 0:
        for r in remove:
            del seen_db[pkgname][r]

    # TODO: update seen more efficiently (right now it is only 70k so not a
    # huge deal, but should probably move to sqlite)
    (fd, fn) = tempfile.mkstemp(prefix=MKDTEMP_PREFIX)
    os.write(fd, bytes(json.dumps(seen_db, sort_keys=True, indent=2), "UTF-8"))
    os.close(fd)

    shutil.move(fn, seen_fn)


# To support ROCKs USN notifications, scan_store is extended to be able to not
# only scan a store-db of published snaps but also a store-db of published
# rocks
def scan_store(secnot_db_fn, store_db_fn, seen_db_fn, pkgname, store_db_type="snap"):
    """For each entry in store db (either snap or rock), see if there are any
       binary packages with security notices, if see report them if not in the
       seen db. We perform these actions on each snap and rock and do not form
       a queue to keep the implementation simple.
    """
    secnot_db = read_usn_db(secnot_db_fn)
    store_db = read_file_as_json_dict(store_db_fn)
    if seen_db_fn:
        seen_db = read_seen_db(seen_db_fn)
    else:
        seen_db = {}

    errors = {}
    sent = []
    for item in store_db:
        if pkgname and "name" in item and pkgname != item["name"]:
            continue

        try:
            pkg_db = get_pkg_revisions(item, secnot_db, errors, store_db_type)
        except ValueError as e:
            if "name" in item:
                _add_error(item["name"], errors, "%s" % e)
            continue

        # (At least) the 'bare' snap is in the db but doesn't have a manifest
        # so there are no revisions to report on
        if "revisions" in pkg_db and len(pkg_db["revisions"]) == 0:
            continue

        try:
            (to_addr, subj, body) = _email_report_for_pkg(pkg_db, seen_db)
            sent.append((to_addr, subj, body))
        except Exception as e:  # pragma: nocover
            _add_error(pkg_db["name"], errors, "%s" % e)
            continue

        if body is None:  # pragma: nocover
            debug("Skipped email for '%s': up to date" % pkg_db["name"])

        if seen_db_fn:
            _update_seen(seen_db_fn, seen_db, pkg_db)

    if len(errors) > 0:
        for p in errors:
            for e in errors[p]:
                warn("%s: %s" % (p, e))

    return sent, errors


def scan_snap(secnot_db_fn, snap_fn, with_cves=False):
    """Scan snap for packages with security notices"""
    out = ""
    (man, dpkg) = get_snap_manifest(snap_fn)
    man = get_faked_build_and_stage_packages(man)

    # Use dpkg.list when the snap ships it in a spot we honor. This is limited
    # to snap scans since dpkg.list doesn't exist in the store.
    if dpkg is not None:
        fake_key = "faked-by-review-tools-dpkg"
        if "parts" in man and fake_key not in man["parts"]:
            man["parts"][fake_key] = {}
            man["parts"][fake_key]["stage-packages"] = []
            for line in dpkg:
                if not line.startswith("ii "):
                    continue
                tmp = line.split()
                man["parts"][fake_key]["stage-packages"].append(
                    "%s=%s" % (tmp[1], tmp[2])
                )

    secnot_db = read_usn_db(secnot_db_fn)
    original_report = get_secnots_for_manifest(
        manifest=man, secnot_db=secnot_db, with_cves=with_cves
    )
    # removing package types separation for json output to no break
    # existing API
    report = {}
    for pkg_type in original_report:
        report.update(original_report[pkg_type])

    if len(report) != 0:
        # needs to be json since snap-check-notices parses this output
        out += json.dumps(report, indent=2, sort_keys=True)

    return out


def scan_rock(secnot_db_fn, rock_fn, with_cves=False):
    """Scan rock for packages with security notices"""
    out = ""
    man = get_rock_manifest(rock_fn)
    secnot_db = read_usn_db(secnot_db_fn)
    original_report = get_secnots_for_manifest(
        manifest=man, secnot_db=secnot_db, with_cves=with_cves, manifest_type="rock"
    )
    # Keeping same interface as snaps report
    report = {}
    for pkg_type in original_report:
        report.update(original_report[pkg_type])

    if len(report) != 0:
        # needs to be json since snap-check-notices parses this output
        out += json.dumps(report, indent=2, sort_keys=True)

    return out


def scan_shared_publishers(store_fn):
    """Check store db for any snaps with a shared email that don't also have a
       mapping.
    """
    store_db = read_file_as_json_dict(store_fn)
    report = get_shared_snap_without_override(store_db)

    out = ""
    if len(report) != 0:
        out += "The following snaps are missing from overrides.py:\n"
        for eml in sorted(report):
            out += "%s:\n- %s" % (eml, "\n- ".join(report[eml]))

    return out
