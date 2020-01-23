"""debversion.py: classes for debversion module"""
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

import re
import struct


# reimplemented from lib/dpkg/version.c
class DebVersion:
    valid_pat = re.compile(
        r"^((\d+):)?"  # epoch
        "([A-Za-z0-9.+:~-]+?)"  # upstream
        "(-([A-Za-z0-9+.~]+))?$"
    )  # debian
    epoch_pat = re.compile(r"^\d+:")
    revision_pat = re.compile(r"^[a-zA-Z0-9+.~]+$")

    def __init__(self, version):
        if not self.valid_pat.search(str(version)):
            raise ValueError("%s not a valid Debian version" % version)

        self.full_version = str(version)
        self.epoch = 0

        tmp = version
        # if version starts with '<int>:' then int is an epoch
        if self.epoch_pat.search(tmp):
            self.epoch = int(tmp.split(":")[0])
            tmp = tmp.split(":", 1)[1]

        # if version has a '-', then (the last) may be the revision
        self.revision = "0"
        if tmp.count("-") > 0:
            poss_revision = tmp.split("-")[-1]
            if self.revision_pat.search(poss_revision):
                self.revision = poss_revision
                self.version = tmp.rsplit("-", 1)[0]
            else:
                self.version = tmp
        else:
            self.version = tmp

        # print("full=%s, epoch=%d, version=%s, revision=%s" %
        #       (self.full_version, self.epoch, self.version, self.revision))
        self.validate()

    def __repr__(self):
        return self.full_version

    def __str__(self):
        return self.full_version

    def validate(self):
        """Check a couple extra things not caught by valid_pat"""
        # https://www.debian.org/doc/debian-policy/#s-f-version
        if not self.epoch_pat.search(self.full_version) and self.version.count(":") > 0:
            raise ValueError("%s is invalid: epoch in not a number" % self.full_version)

        # see if epoch is larget than MAX_INT
        if self.epoch > 2 ** (struct.Struct("i").size * 8 - 1) - 1:
            raise ValueError("%s is invalid: epoch is too large" % self.full_version)

        if self.version == "":
            # 1:-2
            raise ValueError(
                "%s is invalid: upstream version is empty" % self.full_version
            )

        if self.revision == "0" and self.version.count("-") > 1:
            # 1-2-
            raise ValueError(
                "%s is invalid: revision version is empty" % self.full_version
            )


def _order(c):
    if c.isdigit():
        return 0
    elif c.isalpha():
        return ord(c)
    elif c == "~":
        return -1
    elif c != "":
        return ord(c) + 256
    else:
        return 0


# Compares two Debian versions.
#
# retval 0 If a and b are equal.
# retval <0 If a is smaller than b.
# retval >0 If a is greater than b.
def _verrevcomp(a, b):
    aidx = 0
    bidx = 0
    while aidx < len(a) or bidx < len(b):
        first_diff = 0
        while (aidx < len(a) and not a[aidx].isdigit()) or (
            bidx < len(b) and not b[bidx].isdigit()
        ):
            ac = 0
            if aidx < len(a):
                ac = int(_order(a[aidx]))

            bc = 0
            if bidx < len(b):
                bc = int(_order(b[bidx]))

            if ac != bc:
                return ac - bc

            aidx += 1
            bidx += 1
        while aidx < len(a) and a[aidx] == "0":
            aidx += 1
        while bidx < len(b) and b[bidx] == "0":
            bidx += 1
        while (
            aidx < len(a) and a[aidx].isdigit() and bidx < len(b) and b[bidx].isdigit()
        ):
            if first_diff == 0:
                first_diff = int(a[aidx]) - int(b[bidx])
            aidx += 1
            bidx += 1

        if aidx < len(a) and a[aidx].isdigit():
            return 1
        elif bidx < len(b) and b[bidx].isdigit():
            return -1
        elif first_diff != 0:
            return first_diff

    return 0


def compare(a, b):
    # print("compare(%s, %s)" % (a.full_version, b.full_version))
    # if epoch greater
    if a.epoch > b.epoch:
        return 1
    elif a.epoch < b.epoch:
        return -1

    # if version greater
    rc = _verrevcomp(a.version, b.version)
    if rc != 0:
        return rc

    # if revision greater
    return _verrevcomp(a.revision, b.revision)
