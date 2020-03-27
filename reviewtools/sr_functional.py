"""sr_functional.py: snap functional"""
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
from reviewtools.sr_common import SnapReview
from reviewtools.common import cmd, StatLLS
from reviewtools.overrides import (
    func_execstack_overrides,
    func_execstack_skipped_pats,
    func_base_mountpoints_overrides,
    redflagged_snap_types_overrides,
)
import copy
import os
import re


class SnapReviewFunctional(SnapReview):
    """This class represents snap functional reviews"""

    def __init__(self, fn, overrides=None):
        SnapReview.__init__(self, fn, "functional-snap-v2", overrides=overrides)
        self._list_all_compiled_binaries()

        # State files only for base snaps, if have -lls output and
        # --state-output is specified
        self.curr_state = None
        self.prev_state = None
        if (
            # also see check_state_base_files()
            (
                self.snap_yaml["type"] == "base"
                or (
                    self.snap_yaml["type"] in ["core", "os"]
                    and self.snap_yaml["name"] == "core"
                )
            )
            and self.unsquashfs_lls_entries is not None
            and "state_output" in self.overrides
        ):
            # if the name of this changes, then this field in the last state
            # input file won't match and all previous state will be ignored
            self.state_key = self._get_check_name(
                "state_files", extra=",".join(sorted(self.pkg_arch))
            )

            # read in current state
            self.curr_state = {}
            for (line, item) in self.unsquashfs_lls_entries:
                if item is None:
                    continue
                self.curr_state[item[StatLLS.FILENAME]] = item

            # update state_output with our current state
            self.overrides["state_output"][self.state_key] = self._serialize(
                self.curr_state
            )

            # read in previous state
            self.prev_state = {}
            if self.state_key in self.overrides["state_input"]:
                self.prev_state = self._deserialize(
                    self.overrides["state_input"][self.state_key]
                )

    def _serialize(self, state):
        """Serialize a review-tools state"""

        def item2dict(item):
            for required in [
                StatLLS.FILENAME,
                StatLLS.FILETYPE,
                StatLLS.MODE,
                StatLLS.OWNER,
            ]:
                if required not in item:
                    return {}

            d = {}
            fname = item[StatLLS.FILENAME]

            d[fname] = {}
            d[fname]["filetype"] = item[StatLLS.FILETYPE]
            d[fname]["mode"] = item[StatLLS.MODE]
            d[fname]["owner"] = item[StatLLS.OWNER]
            if StatLLS.MAJOR in item and item[StatLLS.MAJOR] is not None:
                d[fname]["major"] = item[StatLLS.MAJOR]
            if StatLLS.MINOR in item and item[StatLLS.MINOR] is not None:
                d[fname]["minor"] = item[StatLLS.MINOR]

            return d

        serial = {}
        for fname in state:
            d = item2dict(state[fname])
            if fname in d:
                serial[fname] = d[fname]
        return copy.deepcopy(serial)

    def _deserialize(self, serial):
        """Deserialize a review-tools serialized state"""

        def dict2item(d):
            fname = list(d)[0]
            for required in ["filetype", "mode", "owner"]:
                if required not in d[fname]:
                    return None

            item = {}
            item[StatLLS.FILENAME] = fname
            item[StatLLS.FILETYPE] = d[fname]["filetype"]
            item[StatLLS.MODE] = d[fname]["mode"]
            item[StatLLS.OWNER] = d[fname]["owner"]
            if "major" in d[fname]:
                item[StatLLS.MAJOR] = d[fname]["major"]
            if "minor" in d[fname]:
                item[StatLLS.MINOR] = d[fname]["minor"]

            return item

        state = {}
        for entry in serial:
            item = dict2item({entry: serial[entry]})
            if item is None:
                continue
            fname = item[StatLLS.FILENAME]
            state[fname] = item
        return copy.deepcopy(state)

    def check_execstack(self):
        """Check execstack"""
        # core snap is known to have these due to klibc. Executable stack
        # checks only make sense for app snaps anyway.
        if self.snap_yaml["type"] != "app":
            return

        def has_execstack(fn):
            (rc, out) = cmd(["execstack", "-q", fn])
            if rc != 0:
                return False

            if out.startswith("X "):
                return True
            return False

        def in_patterns(pats, f):
            for pat in pats:
                if pat.search(f):
                    return True
            return False

        t = "info"
        n = self._get_check_name("execstack")
        s = "OK"
        link = None
        bins = []

        # execstack not supported on arm64, so skip this check on arm64
        if "SNAP_ARCH" in os.environ and os.environ["SNAP_ARCH"] == "arm64":
            s = "OK (skipped on %s)" % os.environ["SNAP_ARCH"]
            self._add_result(t, n, s, link=link)
            return

        skipped_pats = []
        for p in func_execstack_skipped_pats:
            skipped_pats.append(re.compile(r"%s" % p))

        for i in self.pkg_bin_files:
            if has_execstack(i) and not in_patterns(skipped_pats, i):
                bins.append(os.path.relpath(i, self.unpack_dir))

        if len(bins) > 0:
            bins.sort()
            if self.snap_yaml["name"] in func_execstack_overrides:
                t = "info"
                s = "OK (allowing files with executable stack: %s)" % ", ".join(bins)
            else:
                t = "warn"
                # Only warn for strict mode snaps, since they are the ones that
                # will break
                if (
                    "confinement" in self.snap_yaml
                    and self.snap_yaml["confinement"] != "strict"
                ):
                    t = "info"
                s = (
                    "Found files with executable stack. This adds PROT_EXEC to mmap(2) during mediation which may cause security denials. Either adjust your program to not require an executable stack, strip it with 'execstack --clear-execstack ...' or remove the affected file from your snap. Affected files: %s"
                    % ", ".join(bins)
                )
                link = "https://forum.snapcraft.io/t/snap-and-executable-stacks/1812"

        self._add_result(t, n, s, link=link)

    def check_base_mountpoints(self):
        """Verify base snap has all the expected mountpoints"""
        if self.snap_yaml["type"] != "base":
            return

        t = "info"
        n = self._get_check_name("base_mountpoints")
        s = "OK"
        missing = []

        for i in self.base_required_dirs:
            # self.base_required_dirs are absolute paths
            mp = os.path.join(self.unpack_dir, i[1:])
            if not os.path.isdir(mp):
                missing.append(i)

        if len(missing) > 0:
            missing.sort()
            s = "missing required mountpoints: %s" % ", ".join(missing)
            if self.snap_yaml["name"] not in func_base_mountpoints_overrides:
                t = "error"
            else:
                s += " (overridden)"
        self._add_result(t, n, s)

    def check_state_base_files(self):
        """Verify base snap has the expected files"""
        # Don't check state if not a base snap or the "core" os snap (which
        # historically functions as a base). Also no need to to check if
        # --state-input/--state-ouput not specified (note, self.prev_state is
        # empty (ie, not None) when only --state-output is specified)
        if (
            # also see __init__()
            "type" not in self.snap_yaml
            or (
                self.snap_yaml["type"] != "base"
                and (
                    self.snap_yaml["type"] not in ["core", "os"]
                    and self.snap_yaml["name"] != "core"
                )
            )
            or self.prev_state is None
            or self.curr_state is None
        ):
            return

        t = "info"
        n = self._get_check_name("state_base_files")
        s = "OK"

        # Skip checking base snaps that we haven't yet allowed in the store. In
        # this manner, they can keep changing as needed. Allow the historic
        # core os snap.
        if (
            self.snap_yaml["name"] not in redflagged_snap_types_overrides["base"]
            and self.snap_yaml["name"] != "core"
        ):
            if (
                "SNAP_FORCE_STATE_CHECK" not in os.environ
                or os.environ["SNAP_FORCE_STATE_CHECK"] != "1"
            ):
                s = "OK (skipped, snap type not overridden for this snap)"
                self._add_result(t, n, s)
                # preserve previous state if not an approved snap
                if (
                    "state_output" in self.overrides
                    and self.state_key in self.overrides["state_output"]
                ):
                    if (
                        "state_input" in self.overrides
                        and self.state_key in self.overrides["state_input"]
                    ):
                        self.overrides["state_output"][self.state_key] = copy.deepcopy(
                            self.overrides["state_input"][self.state_key]
                        )
                    else:
                        del self.overrides["state_output"][self.state_key]
                return

        if len(self.prev_state) == 0:
            s = "OK (no previous state)"
            self._add_result(t, n, s)
            return

        missing = []
        missing_keys = {}
        different_keys = {}

        # iterate through files in prev_state since this naturally ignores
        # newly added files
        for fname in self.prev_state:
            if fname not in self.curr_state:
                missing.append(fname)
                continue
            # likewise, iterate through metadata keys in prev_state since this
            # allows us to freely add new metadata as our checks evolve
            for k in self.prev_state[fname]:
                kname = str(k).split(".")[1].lower()
                if k not in self.curr_state[fname]:
                    if fname not in missing_keys:
                        missing_keys[fname] = []
                    missing_keys[fname].append(kname)
                elif self.prev_state[fname][k] != self.curr_state[fname][k]:
                    if fname not in different_keys:
                        different_keys[fname] = []
                    different_keys[fname].append(
                        "current %s '%s' != '%s'"
                        % (kname, self.curr_state[fname][k], self.prev_state[fname][k])
                    )

        if len(missing) == 0 and len(missing_keys) == 0 and len(different_keys) == 0:
            self._add_result(t, n, s)
            return

        if len(missing) > 0:
            t = "warn"
            n = self._get_check_name("state_base_files", app="missing")
            s = "missing files since last review: %s" % " ,".join(sorted(missing))
            self._add_result(t, n, s)

        if len(missing_keys) > 0:
            t = "warn"
            n = self._get_check_name(
                "state_base_files", app="metadata", extra="missing"
            )
            tmp = []
            for fn in missing_keys:
                tmp.append("%s (%s)" % (fn, ", ".join(missing_keys[fn])))
            s = "missing metadata since last review: %s" % ", ".join(sorted(tmp))
            self._add_result(t, n, s)

        if len(different_keys) > 0:
            t = "warn"
            n = self._get_check_name(
                "state_base_files", app="metadata", extra="different"
            )
            tmp = []
            for fn in different_keys:
                tmp.append("%s (%s)" % (fn, ", ".join(different_keys[fn])))
            s = "differing metadata since last review: %s" % ", ".join(sorted(tmp))
            self._add_result(t, n, s)
