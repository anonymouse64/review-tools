"""rr_common.py: common classes and functions"""
#
# Copyright (C) 2013-2021 Canonical Ltd.
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


from reviewtools.common import verify_type


# XXX: Since the base Review class needs a lot of refactoring to support rocks,
# RockReview does not inherit from it yet. We will consider that when rock
# reviews are needed
class RockReview(object):
    """This class represents rock reviews"""

    rock_required = ["name"]
    # optional rock fields here (may be required by appstore)
    rock_optional = [
        "type",
    ]

    rock_manifest_required = {
        "manifest-version": "",
        "os-release-id": "",
        "os-release-version-id": "",
    }
    rock_manifest_optional = {
        "staged-packages": [],
        "publisher-emails": [],
        "architectures": [],
    }

    # Valid values for 'type' in packaging yaml
    # - oci
    valid_rock_types = ["oci"]

    # Architectures obtained from the list of supported rocks from docker hub.
    # TODO: Update when server team confirms this list
    valid_compiled_architectures = [
        "amd64",
        "arm64",
        "ppc64el",
        "s390x",
    ]

    def verify_rock_manifest(self, manifest):
        """Verify manifest.yaml.
            TODO: Update when rock manifest is implemented
        """

        # Only worry about missing keys and the format of known keys, not
        # unknown keys, the same way we do for snaps
        # https://forum.snapcraft.io/t/builds-failing-automated-review/7112
        missing = []
        for f in self.rock_required + list(self.rock_manifest_required.keys()):
            if f not in manifest:
                missing.append(f)
        if len(missing) > 0:
            t = "error"
            s = "missing keys in rock/manifest.yaml: %s" % ",".join(sorted(missing))
            return (False, t, s)

        (valid, t, s) = verify_type(manifest, self.rock_manifest_required)
        if not valid:
            return (valid, t, s)

        (valid, t, s) = verify_type(manifest, self.rock_manifest_optional)
        if not valid:
            return (valid, t, s)

        return (True, "info", "OK")
