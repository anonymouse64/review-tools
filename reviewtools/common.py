"""common.py: common classes and functions"""
#
# Copyright (C) 2013-2017 Canonical Ltd.
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
import atexit
import codecs
import copy
from enum import Enum
import glob
import inspect
import json
import logging
import magic
import os
from pkg_resources import resource_filename
import re
import shutil
import stat
import subprocess
import sys
import syslog
import tarfile
import tempfile
import time
import types
import yaml

from reviewtools.overrides import common_external_symlink_override

REPORT_OUTPUT = "json"
RESULT_TYPES = ["info", "warn", "error"]
UNPACK_DIR = None
RAW_UNPACK_DIR = None
TMP_DIR = None
MKDTEMP_PREFIX = "review-tools-"
MKDTEMP_DIR = None
VALID_SYSCALL = r"^[a-z0-9_]{2,64}$"
# This needs to match up with snapcraft. Note, 'xz' is still the default
# compression algorithm, and support for lzo has been added, but others
# may be supported
MKSQUASHFS_DEFAULT_COMPRESSION = "xz"
MKSQUASHFS_OPTS = [
    "-noappend",
    "-comp",
    MKSQUASHFS_DEFAULT_COMPRESSION,
    "-all-root",
    "-no-xattrs",
    "-no-fragments",
]
# squashfs-tools 4.4 and higher is more strict about errors but
# -ignore-errors is supposed to be able to be used to retain the previous
# behavior. Unfortunately, the return code for creating device files is
# still non-zero, so we will check the error strings and only error out
# if there are no ignored errors.
UNSQUASHFS_IGNORED_ERRORS = [
    "because you're not superuser",  # non-root
    "because Operation not permitted",  # lxc
]
# There are quite a few kernel interfaces that can cause problems with
# long profile names. These are outlined in
# https://launchpad.net/bugs/1499544. The big issue is that the audit
# message must fit within PAGE_SIZE (at least 4096 on supported archs),
# so long names could push the audit message to be too big, which would
# result in a denial for that rule (but, only if the rule would've
# allowed it). Giving a hard-error on maxlen since we know that this
# will be a problem. The advisory length is what it is since we know
# that compound labels are sometimes logged and so a snappy system
# running an app in a snappy container or a QA testbed running apps
# under LXC
AA_PROFILE_NAME_MAXLEN = 230  # 245 minus a bit for child profiles
AA_PROFILE_NAME_ADVLEN = 100
# Store enforces this length for snap v2
STORE_PKGNAME_SNAPV2_MINLEN = 2
STORE_PKGNAME_SNAPV2_MAXLEN = 40
# Per noise: "07:33 < noise> jdstrand: yeah, i think 5GB compressed would be a
# good/reasonable limit for now
# https://forum.snapcraft.io/t/max-snap-size-and-getting-software-to-consumers/2913/2
MAX_COMPRESSED_SIZE = 5
# 90% of disk but not larger than this
MAX_UNCOMPRESSED_SIZE = 25

# cache the expensive magic calls
PKG_BIN_FILES = None

# cache gathering all the files
PKG_FILES = None

# os release map
OS_RELEASE_MAP = {
    "ubuntu": {
        "4.10": "warty",
        "5.04": "hoary",
        "5.10": "breezy",
        "6.06": "dapper",
        "6.10": "edgy",
        "7.04": "feisty",
        "7.10": "gutsy",
        "8.04": "hardy",
        "8.10": "intrepid",
        "9.04": "jaunty",
        "9.10": "karmic",
        "10.04": "lucid",
        "10.10": "maverick",
        "11.04": "natty",
        "11.10": "oneiric",
        "12.04": "precise",
        "12.10": "quantal",
        "13.04": "raring",
        "13.10": "saucy",
        "14.04": "trusty",
        "14.10": "utopic",
        "15.04": "vivid",
        "15.10": "wily",
        "16.04": "xenial",
        "16.10": "yakkety",
        "17.04": "zesty",
        "17.10": "artful",
        "18.04": "bionic",
        "18.10": "cosmic",
        "19.04": "disco",
        "19.10": "eoan",
        "20.04": "focal",
        "20.10": "groovy",
        "21.04": "hirsute",
        "21.10": "impish",
        "22.04": "jammy",
    }
}


def cleanup_unpack():
    global UNPACK_DIR
    if UNPACK_DIR is not None and os.path.isdir(UNPACK_DIR):
        recursive_rm(UNPACK_DIR)
        UNPACK_DIR = None
    global RAW_UNPACK_DIR
    if RAW_UNPACK_DIR is not None and os.path.isdir(RAW_UNPACK_DIR):
        recursive_rm(RAW_UNPACK_DIR)
        RAW_UNPACK_DIR = None
    global TMP_DIR
    if TMP_DIR is not None and os.path.isdir(TMP_DIR):
        recursive_rm(TMP_DIR)
        TMP_DIR = None

    # Also cleanup any stale review directories
    global MKDTEMP_PREFIX
    global MKDTEMP_DIR
    tmpdir = tempfile.gettempdir()
    maxage = 60 * 60 * 3  # remove stale review directories older than 3 hours
    if MKDTEMP_DIR is not None:
        tmpdir = MKDTEMP_DIR
    for d in glob.glob("%s/%s*" % (tmpdir, MKDTEMP_PREFIX)):
        if not os.path.isdir(d):
            continue
        # since we tell unsquashfs to use UNPACK_DIR, unsquashfs sets the mtime
        # to the mtime of squashfs-root in the snap after the unpack, so check
        # the ctime instead of the mtime
        if time.time() - os.path.getctime(d) > maxage:
            debug("Removing old review '%s'" % d)
            try:
                recursive_rm(os.path.join(d))
            except Exception:
                # Just log that something weird happened
                syslog.openlog(
                    ident="review-tools",
                    logoption=syslog.LOG_PID,
                    facility=syslog.LOG_USER | syslog.LOG_INFO,
                )
                syslog.syslog("Could not remove '%s'" % d)
                syslog.closelog()

    # For the testsuite
    global PKG_FILES
    PKG_FILES = None
    global PKG_BIN_FILES
    PKG_BIN_FILES = None


atexit.register(cleanup_unpack)


#
# Utility classes
#
class ReviewException(Exception):
    """This class represents Review exceptions"""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ReviewBase(object):
    """Base review class"""

    def __init__(self, review_type, overrides=None):
        self.review_type = review_type
        # TODO: rename as pkg_report
        self.review_report = dict()
        self.stage_report = dict()

        global RESULT_TYPES
        for r in RESULT_TYPES:
            self.review_report[r] = dict()
            self.stage_report[r] = dict()

        self.overrides = overrides if overrides is not None else {}

        self.override_result_type = None

    def set_report_type(self, t):
        global REPORT_OUTPUT
        if t is not None and t in ["console", "json"]:
            REPORT_OUTPUT = t

    def _get_check_name(self, name, app="", extra=""):
        name = ":".join([self.review_type, name])
        if app:
            name += ":" + app
        if extra:
            name += ":" + extra
        return name

    # review_report[<result_type>][<review_name>] = <result>
    #   result_type: info, warn, error
    #   review_name: name of the check (prefixed with self.review_type)
    #   result: contents of the review
    #   link: url for more information
    #   manual_review: force manual review
    #   override_result_type: prefix results with [<result_type>] and set
    #     result_type to override_result_type
    def _add_result(
        self,
        result_type,
        review_name,
        result,
        link=None,
        manual_review=False,
        override_result_type=None,
        stage=False,
    ):
        """Add result to report"""
        global RESULT_TYPES
        if stage:
            report = self.stage_report
        else:
            report = self.review_report

        if result_type not in RESULT_TYPES:
            error("Invalid result type '%s'" % result_type)

        prefix = ""
        if override_result_type is not None:
            if override_result_type not in RESULT_TYPES:
                error("Invalid override result type '%s'" % override_result_type)
            prefix = "[%s] " % result_type.upper()
            result_type = override_result_type

        if review_name not in report[result_type]:
            # log info about check so it can be collected into the
            # check-names.list file
            # format should be
            # CHECK|<review_type:check_name>|<link>
            msg = "CHECK|{}|{}"
            name = ":".join(review_name.split(":")[:2])
            link_text = link if link is not None else ""
            logging.debug(msg.format(name, link_text))
            report[result_type][review_name] = dict()

        report[result_type][review_name].update(
            {"text": "%s%s" % (prefix, result), "manual_review": manual_review}
        )
        if link is not None:
            report[result_type][review_name]["link"] = link

    def _apply_staged_results(self):
        """Merge the staged report into the main report"""
        global RESULT_TYPES
        for result_type in self.stage_report:
            if result_type not in RESULT_TYPES:
                error("Invalid result type '%s'" % result_type)

            for review_name in self.stage_report[result_type]:
                if review_name not in self.review_report[result_type]:
                    self.review_report[result_type][review_name] = dict()
                for key in self.stage_report[result_type][review_name]:
                    self.review_report[result_type][review_name][
                        key
                    ] = self.stage_report[result_type][review_name][key]
            # reset the staged report
            self.stage_report[result_type] = dict()

    # Only called by ./bin/* individually, not 'snap-review'
    def do_report(self):
        """Print report"""
        global REPORT_OUTPUT

        if REPORT_OUTPUT == "json":
            jsonmsg(self.review_report)
        else:
            import pprint

            pprint.pprint(self.review_report)

        rc = 0
        if len(self.review_report["error"]):
            rc = 2
        elif len(self.review_report["warn"]):
            rc = 1
        return rc

    def do_checks(self):
        """Run all methods that start with check_"""
        methodList = [
            name
            for name, member in inspect.getmembers(self, inspect.ismethod)
            if isinstance(member, types.MethodType)
        ]
        for methodname in methodList:
            if not methodname.startswith("check_"):
                continue
            func = getattr(self, methodname)
            func()

    def set_review_type(self, name):
        """Set review name"""
        self.review_type = name


class Review(ReviewBase):
    """Common review class"""

    magic_binary_file_descriptions = [
        "application/x-executable; charset=binary",
        "application/x-sharedlib; charset=binary",
        "application/x-object; charset=binary",
        # 18.04 and higher doesn't show the charset
        "application/x-executable",
        "application/x-sharedlib",
        "application/x-object",
        "application/x-pie-executable",
    ]

    def __init__(self, fn, review_type, overrides=None):
        ReviewBase.__init__(self, review_type, overrides)

        self.pkg_filename = fn
        self._check_package_exists()

        global MKDTEMP_DIR
        if (
            MKDTEMP_DIR is None
            and "SNAP_USER_COMMON" in os.environ
            and os.path.exists(os.environ["SNAP_USER_COMMON"])
        ):
            MKDTEMP_DIR = os.environ["SNAP_USER_COMMON"]

        global UNPACK_DIR
        if UNPACK_DIR is None:
            UNPACK_DIR = unpack_pkg(fn)
        self.unpack_dir = UNPACK_DIR

        # unpack_pkg() now only supports snap v2, so just hardcode these
        self.is_snap2 = True
        self.pkgfmt = {"type": "snap", "version": "16.04"}

        global RAW_UNPACK_DIR
        if RAW_UNPACK_DIR is None:
            RAW_UNPACK_DIR = raw_unpack_pkg(fn)
        self.raw_unpack_dir = RAW_UNPACK_DIR

        # Get a list of all unpacked files
        self.pkg_files = []
        # self._list_all_files() sets self.pkg_files so we can mock it
        self._list_all_files()

        # Setup what is needed to get a list of all unpacked compiled binaries
        self.pkg_bin_files = []
        # self._list_all_compiled_binaries() sets self.pkg_files so we can
        # mock it
        self._list_all_compiled_binaries()

    def _check_innerpath_executable(self, fn):
        """Check that the provided path exists and is executable"""
        return os.access(fn, os.X_OK)

    def _extract_statinfo(self, fn):
        """Extract statinfo from file"""
        try:
            st = os.stat(fn)
        except Exception:
            return None
        return st

    def _extract_file(self, fn):
        """Extract file"""
        if not fn.startswith("/"):
            error("_extract_file() expects absolute path")
        rel = os.path.relpath(fn, self.unpack_dir)

        if not os.path.isfile(fn):
            error("Could not find '%s'" % rel)
        return open_file_read(fn)

    def _path_join(self, dirname, rest):
        return os.path.join(dirname, rest)

    def _get_sha512sum(self, fn):
        """Get sha512sum of file"""
        (rc, out) = cmd(["sha512sum", fn])
        if rc != 0:
            return None
        return out.split()[0]

    def _pkgfmt_type(self):
        """Return the package format type"""
        if "type" not in self.pkgfmt:
            return ""
        return self.pkgfmt["type"]

    def _pkgfmt_version(self):
        """Return the package format version"""
        if "version" not in self.pkgfmt:
            return ""
        return self.pkgfmt["version"]

    def _check_package_exists(self):
        """Check that the provided package exists"""
        if not os.path.exists(self.pkg_filename):
            error("Could not find '%s'" % self.pkg_filename)

    def _list_all_files(self):
        """List all files included in this package."""
        global PKG_FILES
        if PKG_FILES is None:
            PKG_FILES = []
            for root, dirnames, filenames in os.walk(self.unpack_dir):
                for f in filenames:
                    PKG_FILES.append(os.path.join(root, f))

        self.pkg_files = PKG_FILES

    def _check_if_message_catalog(self, fn):
        """Check if file is a message catalog (.mo file)."""
        if fn.endswith(".mo"):
            return True
        return False

    def _list_all_compiled_binaries(self):
        """List all compiled binaries in this package."""
        global PKG_BIN_FILES
        if PKG_BIN_FILES is None:
            self.mime = magic.open(magic.MAGIC_MIME)
            self.mime.load()
            PKG_BIN_FILES = []
            for i in self.pkg_files:
                try:
                    res = self.mime.file(i)
                except Exception:  # pragma: nocover
                    # workaround for zesty python3-magic
                    debug("could not detemine mime type of '%s'" % i)
                    continue

                if (
                    res in self.magic_binary_file_descriptions
                    and not self._check_if_message_catalog(i)
                    and i not in PKG_BIN_FILES
                ):
                    PKG_BIN_FILES.append(i)

        self.pkg_bin_files = PKG_BIN_FILES

    def _verify_pkgversion(self, v):
        """Verify package name"""
        if not isinstance(v, (str, int, float)):
            return False
        re_valid_version = re.compile(
            r"^((\d+):)?"  # epoch
            "([A-Za-z0-9.+:~-]+?)"  # upstream
            "(-([A-Za-z0-9+.~]+))?$"
        )  # debian
        if re_valid_version.match(str(v)):
            return True
        return False


#
# Utility functions
#


def error(out, exit_code=1, do_exit=True, output_type=None):
    """Print error message and exit"""
    global REPORT_OUTPUT
    global RESULT_TYPES

    if output_type is not None:
        Review.set_report_type(None, output_type)

    try:
        if REPORT_OUTPUT == "json":
            # mock up expected json format:
            #  {
            #    "test-family": {
            #      "error": {
            #        "test-name": {
            #          "manual_review": ...,
            #          "text": ...
            #        }
            #      },
            #      "info": {},
            #      "warn": {}
            #    }
            #  }
            family = "runtime-errors"
            name = "msg"

            report = dict()
            report[family] = dict()
            for r in RESULT_TYPES:
                report[family][r] = dict()
            report[family]["error"][name] = dict()
            report[family]["error"][name]["text"] = out
            report[family]["error"][name]["manual_review"] = True

            jsonmsg(report)
        else:
            print("ERROR: %s" % (out), file=sys.stderr)
    except IOError:
        pass

    if do_exit:
        sys.exit(exit_code)


def warn(out):
    """Print warning message"""
    try:
        print("WARN: %s" % (out), file=sys.stderr)
    except IOError:
        pass


def msg(out, output=sys.stdout):
    """Print message"""
    try:
        print("%s" % (out), file=output)
    except IOError:
        pass


def debug(out):
    """Print debug message"""
    if "SNAP_DEBUG" in os.environ:
        try:
            print("DEBUG: %s" % (out), file=sys.stderr)
        except IOError:
            pass


def jsonmsg(out):
    """Format out as json"""
    msg(json.dumps(out, sort_keys=True, indent=2, separators=(",", ": ")))


def cmd(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT):
    """Try to execute the given command."""
    debug(" ".join(command))
    try:
        sp = subprocess.Popen(command, stdout=stdout, stderr=stderr)
    except OSError as ex:
        return [127, str(ex)]

    if sys.version_info[0] >= 3:
        out = sp.communicate()[0].decode("ascii", "ignore")
    else:
        out = sp.communicate()[0]

    return [sp.returncode, out]


def cmd_pipe(command1, command2):
    """Try to pipe command1 into command2."""
    try:
        sp1 = subprocess.Popen(command1, stdout=subprocess.PIPE)
        sp2 = subprocess.Popen(command2, stdin=sp1.stdout)
    except OSError as ex:
        return [127, str(ex)]

    if sys.version_info[0] >= 3:
        out = sp2.communicate()[0].decode("ascii", "ignore")
    else:
        out = sp2.communicate()[0]

    return [sp2.returncode, out]


def set_lang(lang, lc_all):
    origLANG = None
    origLC_ALL = None
    if "LANG" in os.environ:
        origLANG = os.environ["LANG"]
    if "LC_ALL" in os.environ:
        origLC_ALL = os.environ["LC_ALL"]
    os.environ["LANG"] = "C.UTF-8"
    os.environ["LC_ALL"] = "C.UTF-8"

    return (origLANG, origLC_ALL)


def restore_lang(origLANG, origLC_ALL):
    if origLANG is None:
        del os.environ["LANG"]
    else:
        os.environ["LANG"] = origLANG
    if origLC_ALL is None:
        del os.environ["LC_ALL"]
    else:
        os.environ["LC_ALL"] = origLC_ALL


def cmdIgnoreErrorStrings(command, ignoreErrorStrings):
    """Try to run command but only error if no ignored error strings"""
    # Make sure we get untranslated strings
    (origLANG, origLC_ALL) = set_lang("C.UTF-8", "C.UTF-8")

    # run the command
    (rc, out) = cmd(command)

    # reset/unset
    restore_lang(origLANG, origLC_ALL)

    if rc != 0:
        redacted = ""
        for line in out.splitlines():
            # XXX: we lose empty lines in error output
            if line == "":
                continue

            ignored = False
            for s in ignoreErrorStrings:
                if s in line:
                    ignored = True
                    break
            if ignored:
                continue
            redacted += "%s\n" % line

        if redacted == "":
            rc = 0
        out = redacted

    return [rc, out]


def _unpack_cmd(cmd_args, d, dest):
    """Low level unpack helper"""
    curdir = os.getcwd()
    os.chdir(d)

    (rc, out) = cmdIgnoreErrorStrings(cmd_args, UNSQUASHFS_IGNORED_ERRORS)

    os.chdir(curdir)

    if rc != 0:
        if os.path.isdir(d):
            recursive_rm(d)
        error("unpacking failed with '%d':\n%s" % (rc, out))

    if dest is None:
        dest = d
    else:
        # Recursively move unpacked content to original dir, keeping
        # permissions
        move_dir_content(d, dest)

    return dest


# The original directory might have restrictive permissions, so save
# them off, chmod the dir, do the move and reapply
def move_dir_content(d, dest):
    """Move content between dirs, keeping original dir permissions"""
    st_mode = os.stat(d).st_mode
    os.chmod(d, 0o0755)
    shutil.move(d, dest)
    os.chmod(dest, st_mode & 0o7777)


def unsquashfs_lln(snap_pkg):
    """Return unsquashfs -lln output"""
    return cmd(["unsquashfs", "-lln", snap_pkg])


unsquashfs_lln_regex = {
    "fname_pat": re.compile(r"^.+? (squashfs-root)"),
    # based on squashfs-tools/unsquashfs.c
    "mode_pat": re.compile(r"^[rw-]{2}[xsS-][rw-]{2}[xsS-][rw-]{2}[xtT-]$"),
    "date_pat": re.compile(r"^\d\d\d\d-\d\d-\d\d$"),
    "time_pat": re.compile(r"^\d\d:\d\d$"),
    # based on squashfs-tools/unsquashfs.c
    "ftype_pat": re.compile(r"^[bcdlps-]$"),
    "mknod_pat_full": re.compile(r".,."),
    "owner_pat": re.compile(r"^[0-9]+/[0-9]+$"),
}


# do not change the order
class StatLLN(Enum):
    FILETYPE = 1  # file type
    MODE = 2  # expressed as ls output, eg, rwx-r-xr-x
    OWNER = 3  # uid/gid
    UID = 4  # uid
    GID = 5  # gid
    SIZE = 6  # size of the entry
    MAJOR = 7  # device major
    MINOR = 8  # device minor
    DATE = 9  # date
    TIME = 10  # time
    FILENAME = 11  # filename without leading squashfs-root
    FULLNAME = 12  # full filename


def unsquashfs_lln_parse_line(line):
    """Parse a line of unsquashfs -lln output"""
    item = {}  # XXX: make object to ease with comparisons, etc

    if "\x00" in line:
        raise ReviewException("entry may not contain NUL characters: %s" % line)

    tmp = line.split()
    if len(tmp) < 6:
        raise ReviewException("wrong number of fields in '%s'" % line)

    date_idx = 3
    ftype = line[0]
    if ftype == "b" or ftype == "c":
        # Account for unsquashfs -lln doing:
        # crw-rw-rw- 0/0             1,  8 2016-08-09 ...
        # crw-rw---- 0/0            10,141 2016-08-09 ...
        if not unsquashfs_lln_regex["mknod_pat_full"].search(tmp[2]):
            date_idx = 4
    time_idx = date_idx + 1
    fname_idx = time_idx + 1

    # make sure filename is in the right place
    if not tmp[fname_idx].startswith("squashfs-root"):
        raise ReviewException("could not determine filename: %s" % line)

    # embedded NULs handled above
    fname = unsquashfs_lln_regex["fname_pat"].sub(".", line)
    item[StatLLN.FILENAME] = fname

    fname_full = unsquashfs_lln_regex["fname_pat"].sub("\\1", line)
    item[StatLLN.FULLNAME] = fname_full

    # Also see 'info ls', but we list only the Linux ones
    if not unsquashfs_lln_regex["ftype_pat"].search(ftype):
        raise ReviewException("unknown type '%s' for entry '%s'" % (ftype, fname))
    item[StatLLN.FILETYPE] = ftype

    # verify mode
    mode = tmp[0][1:]
    if not unsquashfs_lln_regex["mode_pat"].search(mode):
        raise ReviewException("mode '%s' malformed for '%s'" % (mode, fname))
    item[StatLLN.MODE] = mode

    # verify ownership
    owner = tmp[1]
    if not unsquashfs_lln_regex["owner_pat"].search(owner):
        raise ReviewException("uid/gid '%s' malformed for '%s'" % (owner, fname))
    item[StatLLN.OWNER] = owner
    item[StatLLN.UID], item[StatLLN.GID] = owner.split("/")

    if ftype == "b" or ftype == "c":
        # Account for unsquashfs -lln doing:
        # crw-rw-rw- 0/0             1,  8 2016-08-09 ...
        # crw-rw---- 0/0            10,141 2016-08-09 ...

        if unsquashfs_lln_regex["mknod_pat_full"].search(tmp[2]):
            (major, minor) = tmp[2].split(",")
        else:
            major = tmp[2][:-1]
            minor = tmp[3]

        try:
            int(major)
        except Exception:
            raise ReviewException("major '%s' malformed for '%s'" % (major, fname))
        item[StatLLN.MAJOR] = major
        try:
            int(minor)
        except Exception:
            raise ReviewException("minor '%s' malformed for '%s'" % (minor, fname))
        item[StatLLN.MINOR] = minor
    else:
        size = tmp[2]
        try:
            int(size)
        except Exception:
            raise ReviewException("size '%s' malformed for '%s'" % (size, fname))
        item[StatLLN.SIZE] = size

    date = tmp[date_idx]
    if not unsquashfs_lln_regex["date_pat"].search(date):
        raise ReviewException("date '%s' malformed for '%s'" % (date, fname))
    item[StatLLN.DATE] = date

    time = tmp[time_idx]
    if not unsquashfs_lln_regex["time_pat"].search(time):
        raise ReviewException("time '%s' malformed for '%s'" % (time, fname))
    item[StatLLN.TIME] = time

    return copy.copy(item)


def unsquashfs_lln_parse(lln_out):
    """Parse unsquashfs -lln output"""
    hdr = []
    entries = []

    count = 0
    header_re = re.compile(
        "^(Parallel unsquashfs: Using .* processor.*|[0-9]+ inodes .* to write)$"
    )
    seen_header = False
    errors = []
    for line in lln_out.splitlines():
        count += 1
        if not seen_header:
            if len(line) < 1 or header_re.match(line):
                hdr.append(line)
                continue
            else:
                seen_header = True

        item = None
        try:
            item = unsquashfs_lln_parse_line(line)
            entries.append((line, item))
        except ReviewException as e:
            errors.append(str(e))
            entries.append((line, None))

    if len(errors) > 0:
        raise ReviewException(
            "malformed lines in unsquashfs output: '%s'" % ", ".join(errors)
        )

    return hdr, entries


def _calculate_snap_unsquashfs_uncompressed_size(snap_pkg):
    """Calculate size of the uncompressed snap"""
    (rc, out) = cmd(["unsquashfs", "-lln", snap_pkg])
    if rc != 0:
        error("unsquashfs -lln '%s' failed: %s" % (snap_pkg, out))

    size = 0
    for line in out.splitlines():
        if not line.startswith("-"):  # skip non-regular files
            continue
        try:
            size += int(line.split()[2])
        except ValueError:  # skip non-numbers
            continue

    return size


def _calculate_rock_untar_uncompressed_size(rock_pkg):
    """Calculate size of the uncompressed tar"""
    size = 0
    with tarfile.open(rock_pkg) as tar:
        for tarinfo in tar:
            size += tarinfo.size

    return size


def unsquashfs_supports_ignore_errors():
    """Detect if unsquashfs supports the -ignore-errors option"""
    (rc, out) = cmd(["unsquashfs", "-help"])
    # unsquashfs -help returns non-zero, so just search for the option
    return "-ig[nore-errors]" in out


def _unpack_snap_squashfs(snap_pkg, dest, items=[]):
    """Unpack a squashfs based snap package to dest"""
    size = _calculate_snap_unsquashfs_uncompressed_size(snap_pkg)

    snap_max_size = MAX_UNCOMPRESSED_SIZE * 1024 * 1024 * 1024
    valid_size, error_msg = is_pkg_uncompressed_size_valid(
        snap_max_size, size, snap_pkg
    )
    if valid_size:
        global MKDTEMP_PREFIX
        global MKDTEMP_DIR
        d = tempfile.mkdtemp(prefix=MKDTEMP_PREFIX, dir=MKDTEMP_DIR)
        cmd = ["unsquashfs", "-no-progress", "-f", "-d", d]

        # If unsquashfs supports it, pass "-ignore-errors -quiet"
        if unsquashfs_supports_ignore_errors():
            cmd.append("-ignore-errors")
            cmd.append("-quiet")

        cmd.append(os.path.abspath(snap_pkg))

        if len(items) != 0:
            cmd += items
        return _unpack_cmd(cmd, d, dest)
    else:
        error(error_msg)


def is_pkg_uncompressed_size_valid(pkg_max_size, size, pkg):
    st = os.statvfs(pkg)
    avail = st.f_bsize * st.f_bavail * 0.9  # 90% of available space
    if size > pkg_max_size:
        return (
            False,
            "uncompressed %s is too large (%dM > %dM)"
            % (pkg, size / 1024 / 1024, pkg_max_size / 1024 / 1024),
        )
    elif size > avail * 0.9:
        return (
            False,
            "uncompressed %s is too large for available space (%dM > %dM)"
            % (pkg, size / 1024 / 1024, avail / 1024 / 1024),
        )
    else:
        return True, ""


def _unpack_rock_tar(rock_pkg, dest):
    """Unpack a tar based rock package to dest"""
    size = _calculate_rock_untar_uncompressed_size(rock_pkg)

    # Assuming MAX_UNCOMPRESSED_SIZE for rocks is same as snaps
    # MAX_UNCOMPRESSED_SIZE
    rock_max_size = MAX_UNCOMPRESSED_SIZE * 1024 * 1024 * 1024

    valid_size, error_msg = is_pkg_uncompressed_size_valid(
        rock_max_size, size, rock_pkg
    )
    if valid_size:
        global MKDTEMP_PREFIX
        global MKDTEMP_DIR
        d = tempfile.mkdtemp(prefix=MKDTEMP_PREFIX, dir=MKDTEMP_DIR)

        try:
            with tarfile.open(rock_pkg) as tar:
                # Inspecting members before extracting, since it is possible that
                # files are created outside of path, e.g. members that have
                # absolute filenames starting with "/" or filenames with two dots
                # ".."
                # https://docs.python.org/3/library/tarfile.html#tarfile.TarFile.extractall
                for name in tar.getnames():
                    if name.startswith("..") or name.startswith("/"):
                        error(
                            "Bad path %s while extracting archive at %s"
                            % (name, rock_pkg)
                        )

                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(tar, path=d)
        except Exception as e:
            error("Unexpected exception while unpacking rock %s" % e)
            if os.path.isdir(d):
                recursive_rm(d)

        if dest is None:
            dest = d
        else:
            # Recursively move extracted content to original dir,
            # keeping permissions
            move_dir_content(d, dest)

        return dest
    else:
        error(error_msg)


def unpack_pkg(fn, dest=None, items=[]):
    """Unpack package"""
    pkg = check_fn(fn)
    check_dir(dest)

    # Limit the maximimum size of the package
    check_max_pkg_size(pkg)

    # check if its a squashfs based snap
    if is_squashfs(pkg):
        return _unpack_snap_squashfs(fn, dest, items)

    error("Unsupported package format (not squashfs)")


def check_dir(dest):
    if dest is not None and os.path.exists(dest):
        error("'%s' exists. Aborting." % dest)


def check_fn(fn):
    if not os.path.isfile(fn):
        error("Could not find '%s'" % fn)
    pkg = fn
    if not pkg.startswith("/"):
        pkg = os.path.abspath(pkg)
    return pkg


def check_max_pkg_size(pkg):
    size = os.stat(pkg)[stat.ST_SIZE]
    max = MAX_COMPRESSED_SIZE * 1024 * 1024 * 1024
    if size > max:
        error(
            "compressed file is too large (%dM > %dM)"
            % (size / 1024 / 1024, max / 1024 / 1024)
        )


def is_squashfs(filename):
    """Return true if the given filename as a squashfs header"""
    with open(filename, "rb") as f:
        header = f.read(10)
    return header.startswith(b"hsqs")


def unpack_rock(fn, dest=None):
    """Unpack rock"""
    pkg = check_fn(fn)
    check_dir(dest)

    # Limit the maximimum size of the package
    check_max_pkg_size(pkg)

    # check if its a tar based rock
    if tarfile.is_tarfile(pkg):
        return _unpack_rock_tar(fn, dest)

    error("Unsupported package format (not tar)")


def raw_unpack_pkg(fn, dest=None):
    """Unpack raw package"""
    if not os.path.isfile(fn):
        error("Could not find '%s'" % fn)
    pkg = fn
    if not pkg.startswith("/"):
        pkg = os.path.abspath(pkg)
    # nothing to do for squashfs images
    if is_squashfs(pkg):
        return ""

    if dest is not None and os.path.exists(dest):
        error("'%s' exists. Aborting." % dest)

    global MKDTEMP_PREFIX
    global MKDTEMP_DIR
    d = tempfile.mkdtemp(prefix=MKDTEMP_PREFIX, dir=MKDTEMP_DIR)

    curdir = os.getcwd()
    os.chdir(d)
    (rc, out) = cmd(["ar", "x", pkg])
    os.chdir(curdir)

    if rc != 0:
        if os.path.isdir(d):
            recursive_rm(d)
        error("'ar x' failed with '%d':\n%s" % (rc, out))

    if dest is None:
        dest = d
    else:
        shutil.move(d, dest)

    return dest


def create_tempdir():
    """Create/reuse a temporary directory that is automatically cleaned up"""
    global TMP_DIR
    global MKDTEMP_PREFIX
    global MKDTEMP_DIR
    if TMP_DIR is None:
        TMP_DIR = tempfile.mkdtemp(prefix=MKDTEMP_PREFIX, dir=MKDTEMP_DIR)
    return TMP_DIR


def open_file_read(path):
    """Open specified file read-only"""
    try:
        orig = codecs.open(path, "r", "UTF-8")
    except Exception:
        raise

    return orig


def open_file_write(path):
    """Open specified file read-write"""
    try:
        orig = codecs.open(path, "w", "UTF-8")
    except Exception:
        raise

    return orig


def recursive_rm(dirPath, contents_only=False, top=True):
    """recursively remove directory"""
    if top:
        os.chmod(dirPath, 0o0755)  # ensure the top dir is always removable

    try:
        names = os.listdir(dirPath)
    except PermissionError:
        # If directory has weird permissions (eg, 000), just try to remove the
        # directory if we can. If it is non-empty, we'll legitimately fail
        # here. This allows us to remove empty directories with weird
        # permissions.
        os.rmdir(dirPath)
        return

    for name in names:
        path = os.path.join(dirPath, name)
        if os.path.islink(path) or not os.path.isdir(path):
            os.unlink(path)
        else:
            try:
                recursive_rm(path, top=False)
            except PermissionError:
                os.chmod(path, 0o0755)  # LP: #1712476
                recursive_rm(path, top=False)

    if contents_only is False:
        os.rmdir(dirPath)


def run_check(cls):
    if len(sys.argv) < 2:
        error("Must give path to package")

    # extract args
    fn = sys.argv[1]
    if len(sys.argv) > 2:
        overrides = json.loads(sys.argv[2])
    else:
        overrides = None

    review = cls(fn, overrides=overrides)
    review.do_checks()
    rc = review.do_report()
    sys.exit(rc)


def find_external_symlinks(unpack_dir, pkg_files, pkgname, prefix_ok=None):
    """Check if symlinks in the package go out to the system."""
    common = r"(-[0-9.]+)?\.so(\.[0-9.]+)?"
    libc6_libs = [
        "ld-*.so",
        "libanl",
        "libBrokenLocale",
        "libc",
        "libcidn",
        "libcrypt",
        "libdl",
        "libmemusage",
        "libm",
        "libmvec",
        "libnsl",
        "libnss_compat",
        "libnss_dns",
        "libnss_files",
        "libnss_hesiod",
        "libnss_nisplus",
        "libnss_nis",
        "libpcprofile",
        "libpthread",
        "libresolv",
        "librt",
        "libSegFault",
        "libthread_db",
        "libutil",
    ]
    libc6_pats = []
    for lib in libc6_libs:
        libc6_pats.append(re.compile(r"%s%s" % (lib, common)))
    libc6_pats.append(re.compile(r"ld-*.so$"))
    libc6_pats.append(re.compile(r"ld-linux-.*.so\.[0-9.]+$"))
    libc6_pats.append(re.compile(r"ld64.so\.[0-9.]+$"))  # ppc64el

    # snapcraft 4.0 updated the python plugin to treat the python in the snap's
    # runtime as essentially another virtual environment. To achieve this,
    # snapcraft sets up symlinks to outside of the snap for python.
    snapcraft_pats = [re.compile(r"^/usr/bin/python3(\.[0-9]*)?$")]

    def _in_patterns(pats, f):
        for pat in pats:
            if pat.search(f):
                return True
        return False

    def _is_external(link, linkname_pats, abs_pats, pkgname, prefix_ok=None):
        if not os.path.islink(link):
            return False

        # Perform a realpath so we can check if the file is in the unpack
        # dir (which indicates it is inside the snap)
        rp = os.path.realpath(link)

        # Perform a 'readlink' so we can check the path of the unresolved
        # target against specific target patterns
        rl = os.readlink(link)

        if (
            rp.startswith("/")
            and len(rp) > 1
            and pkgname in common_external_symlink_override
        ):
            if rp.startswith(unpack_dir + "/"):
                rel = os.path.relpath(rp, unpack_dir)
            else:
                rel = rp[1:]
            if rel in common_external_symlink_override[pkgname]:
                return False

        if prefix_ok is not None and rp.startswith(prefix_ok):
            return False

        # Allowed external:
        # - realpath: <unpackdir>/...
        # - realpath: /snap/<snapname>/...
        # - realpath: /var/snap/<snapname>/...
        # - realpath matches a particular name (linkname_pats):
        #   /.../libnsl-2.31.so
        # - readlink (target) is an absolute path and matches an absolute path
        #   (abs_pats): /usr/bin/python3
        # - readlink (target) is a relative path and realpath matches an
        #   absolute path (abs_paths): python3 -> /usr/bin/python3
        #
        # Disallowed (external)
        # - realpath: /snap/<other snap>/...
        # - realpath: /var/snap/<other snap>/...
        # - realpath: /.../not-matching-link-name
        # - realpath: /not-matching-absolute-path

        # Check if the realpath is pointing to something outside the snap. Note
        # that os.path.realpath resolves all symlinks, so:
        #
        #   /<unpackdir>/foo -> /does-exist     - realpath is '/does-exist'
        #   /<unpackdir>/foo -> /does-not-exist - realpath is '/does-not-exist'
        #
        # In either case, both point outside the snap so the realpath is ok as
        # a first pass. Since 'unpack_dir' is a temporary directory, it should
        # not be possible for a snap to do:
        #
        #   /<unpackdir>/foo -> /link/pointing/to/<unpackdir>/bar
        #
        # since /link/pointing/to/<unpackdir>/bar is not controllable by the
        # snap (even if it could, this check is not a security check and is
        # instead a warning that something could go wrong at runtime).
        if (
            not rp.startswith(unpack_dir + "/")
            and not rp.startswith(os.path.join("/snap", pkgname) + "/")
            and not rp.startswith(os.path.join("/var/snap", pkgname) + "/")
            and not _in_patterns(linkname_pats, os.path.basename(link))
        ):
            # If the target link is absolute, check the target link against
            # allowed abs paths.
            if rl.startswith("/") and _in_patterns(abs_pats, rl):
                return False

            # If the target link is relative, check the realpath against
            # allowed abs paths
            if not rl.startswith("/") and _in_patterns(abs_pats, rp):
                return False

            return True
        return False

    external_symlinks = list(
        filter(
            lambda link: _is_external(
                link, libc6_pats, snapcraft_pats, pkgname, prefix_ok
            ),
            pkg_files,
        )
    )

    return [os.path.relpath(i, unpack_dir) for i in external_symlinks]


# check_results(report, expected_counts, expected)
# Verify exact counts of types
#   expected_counts={'info': 1, 'warn': 0, 'error': 0}
#   self.check_results(report, expected_counts)
# Verify counts of warn and error types
#   expected_counts={'info': None, 'warn': 0, 'error': 0}
#   self.check_results(report, expected_counts)
# Verify exact messages:
#   expected = dict()
#   expected['info'] = dict()
#   expected['warn'] = dict()
#   expected['warn']['skeleton_baz'] = "TODO"
#   expected['error'] = dict()
#   self.check_results(r, expected=expected)


def check_results(
    testobj, report, expected_counts={"info": 1, "warn": 0, "error": 0}, expected=None
):
    if expected is not None:
        for t in expected.keys():
            for r in expected[t]:
                testobj.assertTrue(
                    r in report[t],
                    "Could not find '%s' (%s) in:\n%s"
                    % (r, t, json.dumps(report, indent=2)),
                )
                for k in expected[t][r]:
                    testobj.assertTrue(
                        k in report[t][r],
                        "Could not find '%s' (%s) in:\n%s"
                        % (k, r, json.dumps(report, indent=2)),
                    )
                testobj.assertEqual(expected[t][r][k], report[t][r][k])
    else:
        for k in expected_counts.keys():
            if expected_counts[k] is None:
                continue
            testobj.assertEqual(
                len(report[k]),
                expected_counts[k],
                "(%s not equal)\n%s" % (k, json.dumps(report, indent=2)),
            )


def read_file_as_json_dict(fn):
    """Read in filename as json dict"""
    # XXX: consider reading in as stream
    debug("Loading: %s" % fn)
    raw = {}
    with open_file_read(fn) as fd:
        try:
            raw = json.load(fd)
        except Exception:
            raise

    return raw


def get_snap_manifest(fn):
    if "SNAP_USER_COMMON" in os.environ and os.path.exists(
        os.environ["SNAP_USER_COMMON"]
    ):
        MKDTEMP_DIR = os.environ["SNAP_USER_COMMON"]
    else:
        MKDTEMP_DIR = tempfile.gettempdir()

    man = "snap/manifest.yaml"
    os_dpkg = "usr/share/snappy/dpkg.list"
    snap_dpkg = "snap/dpkg.list"
    # unpack_pkg() fails if this exists, so this is safe
    dir = tempfile.mktemp(prefix=MKDTEMP_PREFIX, dir=MKDTEMP_DIR)
    unpack_pkg(fn, dir, [man, os_dpkg, snap_dpkg])

    man_fn = os.path.join(dir, man)
    if not os.path.isfile(man_fn):
        recursive_rm(dir)
        error("%s not in %s" % (man, fn))

    with open_file_read(man_fn) as fd:
        try:
            man_yaml = yaml.safe_load(fd)
        except Exception:
            recursive_rm(dir)
            error("Could not load %s. Is it properly formatted?" % man)

    os_dpkg_fn = os.path.join(dir, os_dpkg)
    snap_dpkg_fn = os.path.join(dir, snap_dpkg)
    dpkg_list = None
    if os.path.isfile(os_dpkg_fn):
        with open_file_read(os_dpkg_fn) as fd:
            try:
                dpkg_list = fd.readlines()
            except Exception:
                recursive_rm(dir)
                error("Could not load %s. Is it properly formatted?" % os_dpkg)
    elif os.path.isfile(snap_dpkg_fn):
        with open_file_read(snap_dpkg_fn) as fd:
            try:
                dpkg_list = fd.readlines()
            except Exception:
                recursive_rm(dir)
                error("Could not load %s. Is it properly formatted?" % snap_dpkg)

    recursive_rm(dir)

    return (man_yaml, dpkg_list)


def get_rock_manifest(fn):
    if "SNAP_USER_COMMON" in os.environ and os.path.exists(
        os.environ["SNAP_USER_COMMON"]
    ):
        MKDTEMP_DIR = os.environ["SNAP_USER_COMMON"]
    else:
        MKDTEMP_DIR = tempfile.gettempdir()
    unpack_tmp_dir = tempfile.mktemp(prefix=MKDTEMP_PREFIX, dir=MKDTEMP_DIR)

    man_fn = "/usr/share/rocks/dpkg.query"
    unpack_rock(fn, unpack_tmp_dir)

    # since ROCK manifest is not available yet, we build a manifest using the
    # information available in /usr/share/rocks/dpkg.query present inside the
    # rock
    man_yaml = build_manifest_from_rock_tar(man_fn, unpack_tmp_dir)
    recursive_rm(unpack_tmp_dir)

    return man_yaml


def list_dir(path, dirs_only=False):
    """ List directory items """
    results = list(map(lambda x: os.path.join(path, x), os.listdir(path)))
    if dirs_only:
        return [_ for _ in results if os.path.isdir(_)]
    return results


def get_layer_dpkg(tarfile_path):
    """ Look for the prescence of the dpkg_query file inside the layer tar """
    dpkg_query = ""
    with tarfile.open(tarfile_path, "r") as tarfile_fh:
        dpkg_query_path = next(
            iter(
                fn
                for fn in tarfile_fh.getnames()
                if os.path.basename(fn) == "dpkg.query"
            ),
            None,
        )
        if dpkg_query_path is not None:
            with tarfile_fh.extractfile(dpkg_query_path) as dpkg_query_fh:
                dpkg_query = dpkg_query_fh.readlines()
    return dpkg_query


# since rock manifest is not available yet, we build it using the interim
# rock manifest (/usr/share/rocks/dpkg.query).
# https://bugs.launchpad.net/ubuntu-docker-images/+bug/1905052
# $ (echo "# os-release" && cat /etc/os-release && echo "# dpkg-query" &&
# dpkg-query -f '${db:Status-Abbrev},${binary:Package},${Version},
# ${source:Package},${Source:Version}\n' -W) > /usr/share/rocks/dpkg.query
def build_manifest_from_rock_tar(man_fn, unpack_tmp_dir):
    dpkg_query = None
    dpkg_query = extract_dpkg_query_file_from_rock(dpkg_query, unpack_tmp_dir)

    if not dpkg_query:
        recursive_rm(unpack_tmp_dir)
        error("%s not in %s" % (man_fn, unpack_tmp_dir))

    return build_man_from_dpkg_query_file_content(dpkg_query)


def _key_in_dpkg_query(key_name, line):
    return line.startswith(key_name)


def _get_dpkg_query_line_value(line):
    _, _, val = line.partition("=")
    return val.strip('"')


def build_man_from_dpkg_query_file_content(dpkg_query):
    man_yaml = {"manifest-version": "1", "stage-packages": []}
    for line in dpkg_query:
        line = line.decode().strip()
        # os-release-id is obtained from ID key. e.g.: ID=ubuntu
        # since we have ID and ID_LIKE, we need the equals symbol to check
        if _key_in_dpkg_query("ID=", line):
            os_release_id = _get_dpkg_query_line_value(line)
            if os_release_id:
                man_yaml["os-release-id"] = os_release_id
        # os-release-version-id is obtained from VERSION_ID key. e.g.:
        # VERSION_ID="20.04"
        elif _key_in_dpkg_query("VERSION_ID=", line):
            os_release_version_id = _get_dpkg_query_line_value(line)
            if os_release_version_id:
                man_yaml["os-release-version-id"] = os_release_version_id
        # stage-packages are obtained from dpkg-query section
        # e.g.: ii ,adduser,3.118ubuntu2,adduser,3.118ubuntu2
        elif _key_in_dpkg_query("ii ", line):
            tmp = line.split(",")
            if len(tmp) == 5:
                man_yaml["stage-packages"].append(
                    "%s=%s,%s=%s" % (tmp[1], tmp[2], tmp[3], tmp[4].rstrip())
                )
    return man_yaml


# An uncompress rock contains a directory per layer, each one containing a
# tar archive including the layer contents. Since we don't know in which
# layer the dpkg.file is present, we iterate all until we find it.
# Also, since a rock main directory contains other files rather than each
# layer directory, we only consider items of os.listdir(dir) as layers if
# are directories
def extract_dpkg_query_file_from_rock(dpkg_query, unpack_tmp_dir):
    """ Extracts the dpkg_query file content from a given rock """
    for layer_dir in list_dir(unpack_tmp_dir, dirs_only=True):
        # Each rock layer is yet another tar archive, and we can
        # inspect the content without extracting all.
        layers_tar_files = [
            layer_file
            for layer_file in list_dir(layer_dir)
            if tarfile.is_tarfile(layer_file)
        ]

        if not layers_tar_files:
            continue

        if len(layers_tar_files) > 1:
            raise ReviewException(
                "Unexpected number of layer tar archives inside layer directory: %d"
                % len(layers_tar_files)
            )
        try:
            for layer in layers_tar_files:
                dpkg_query = get_layer_dpkg(layer)
                if dpkg_query:
                    return dpkg_query
        except Exception as e:
            error("Could not extract manifest %s" % e)
            recursive_rm(unpack_tmp_dir)

    return dpkg_query


def get_os_codename(os, ver):
    if os not in OS_RELEASE_MAP:
        raise ValueError("Could not find '%s' in OS_RELEASE_MAP" % os)

    if ver not in OS_RELEASE_MAP[os]:
        raise ValueError("Could not find '%s' in OS_RELEASE_MAP[%s]" % (ver, os))

    return OS_RELEASE_MAP[os][ver]


def read_snapd_base_declaration():
    """Read snapd base declaration"""
    # prefer local copy if it exists, otherwise, use one shipped in the
    # package
    bd_fn = "./reviewtools/data/snapd-base-declaration.yaml"
    if not os.path.exists(bd_fn):
        bd_fn = resource_filename(__name__, "data/snapd-base-declaration.yaml")
        if not os.path.exists(bd_fn):
            error("could not find '%s'" % bd_fn)
    fd = open_file_read(bd_fn)
    contents = fd.read()
    fd.close()

    bd_yaml = yaml.safe_load(contents)
    # FIXME: don't hardcode series
    series = "16"
    return series, bd_yaml[series]


# TODO: make this a class
def _add_error(name, errors, msg):
    if name not in errors:
        errors[name] = []
    errors[name].append(msg)


def assign_type_to_dict_values(d, assignments):
    """For each toplevel key in d, if val is None, use empty value from
       assignments
    """
    for key in assignments:
        if key in d and d[key] is None:
            d[key] = assignments[key]


# --state-input/--state-output format version. Layout:
#   Version 1:
#     {
#       "format": 1,
#       "<review_type>": {...}
#     }
#
#     where <review_type> is self.review_type (as setup by __init__(...)
#
STATE_FORMAT_VERSION = 1


def init_override_state_input():
    """Initialize the state input"""
    return {"format": STATE_FORMAT_VERSION}


def verify_override_state(st):
    """Verify state as specified by st"""
    # XXX for now, just do it this way. Eventually as we understand the
    # stored state, perhaps by schema

    if not isinstance(st, dict):
        raise ValueError("state object is not a dict")

    if "format" not in st:
        raise ValueError("missing required 'format' key")

    f = st["format"]
    if not isinstance(f, int) or f < 1 or f > STATE_FORMAT_VERSION:
        raise ValueError(
            "'format' should be a positive JSON integer <= %d" % STATE_FORMAT_VERSION
        )


def initialize_environment_variables():
    if "SNAP_USER_COMMON" not in os.environ:
        os.environ["SNAP_USER_COMMON"] = (
            "%s/snap/review-tools/common" % os.environ["HOME"]
        )
        debug(
            "SNAP_USER_COMMON not set. Defaulting to %s"
            % os.environ["SNAP_USER_COMMON"]
        )
        if not os.path.exists(os.environ["SNAP_USER_COMMON"]):
            error(
                "SNAP_USER_COMMON not set and %s does not exist"
                % os.environ["SNAP_USER_COMMON"]
            )


def get_debug_info_from_environment():
    had_debug = None
    if "SNAP_DEBUG" in os.environ:
        had_debug = os.environ["SNAP_DEBUG"]
    return had_debug


def fetch_usn_db(args):
    usndb = "database.json"
    if "SNAP" in os.environ:
        fetchdb = "%s/bin/fetch-db" % os.path.abspath(os.environ["SNAP"])
    else:
        fetchdb = "review-tools.fetch-usn-db"
    curdir = os.getcwd()
    os.chdir(os.environ["SNAP_USER_COMMON"])
    # download the usndb
    update_interval = 60 * 60 * 24  # one day
    if not args.no_fetch and (
        not os.path.exists("./" + usndb)
        or time.time() - os.path.getmtime("./" + usndb) >= update_interval
    ):
        rc, out = cmd([fetchdb, "%s.bz2" % usndb])
        if rc != 0:
            error(out)
    else:
        debug("Reusing %s" % usndb)
    os.chdir(curdir)
    return usndb


def verify_type(m, d, prefix=""):
    for f in d:
        if f in m:
            needed_type = type(d[f])
            if not isinstance(m[f], needed_type):
                t = "error"
                s = "'%s%s' is '%s', not '%s'" % (
                    prefix,
                    f,
                    type(m[f]).__name__,
                    needed_type.__name__,
                )
                return (False, t, s)
    return (True, "info", "OK")


def is_rock_valid(pkg):
    if not os.path.isfile(pkg):
        return False, "Skipping '%s', not a regular file." % pkg

    # This initial implementation assumes tar as the rock archive format.
    if not tarfile.is_tarfile(pkg):
        return (
            False,
            "Skipping '%s', not a tar archive. You can run 'docker image save"
            "--output rock_name-X.Y-series.tar ROCK_NAME' to get a rock in a "
            "tar archive format",
        )
    else:
        return True, ""
