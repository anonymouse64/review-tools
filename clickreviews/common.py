'''common.py: common classes and functions'''
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
import glob
import inspect
import json
import logging
import magic
import os
import re
import shutil
import stat
import subprocess
import sys
import syslog
import tempfile
import time
import types
import yaml

from clickreviews.overrides import (
    common_external_symlink_override,
)

REPORT_OUTPUT = "json"
RESULT_TYPES = ['info', 'warn', 'error']
UNPACK_DIR = None
RAW_UNPACK_DIR = None
TMP_DIR = None
MKDTEMP_PREFIX = "review-tools-"
MKDTEMP_DIR = None
VALID_SYSCALL = r'^[a-z0-9_]{2,64}$'
# This needs to match up with snapcraft
MKSQUASHFS_OPTS = ['-noappend', '-comp', 'xz', '-all-root', '-no-xattrs',
                   '-no-fragments']
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
                syslog.openlog(ident="review-tools",
                               logoption=syslog.LOG_PID,
                               facility=syslog.LOG_USER | syslog.LOG_INFO)
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
    '''This class represents Review exceptions'''
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Review(object):
    '''Common review class'''
    magic_binary_file_descriptions = [
        'application/x-executable; charset=binary',
        'application/x-sharedlib; charset=binary',
        'application/x-object; charset=binary',
        # 18.04 and higher doesn't show the charset
        'application/x-executable',
        'application/x-sharedlib',
        'application/x-object',
    ]

    def __init__(self, fn, review_type, overrides=None):
        self.pkg_filename = fn
        self._check_package_exists()

        self.review_type = review_type
        # TODO: rename as pkg_report
        self.click_report = dict()
        self.stage_report = dict()

        global RESULT_TYPES
        for r in RESULT_TYPES:
            self.click_report[r] = dict()
            self.stage_report[r] = dict()

        global MKDTEMP_DIR
        if MKDTEMP_DIR is None and 'SNAP_USER_COMMON' in os.environ and \
                os.path.exists(os.environ['SNAP_USER_COMMON']):
            MKDTEMP_DIR = os.environ['SNAP_USER_COMMON']

        global UNPACK_DIR
        if UNPACK_DIR is None:
            UNPACK_DIR = unpack_pkg(fn)
        self.unpack_dir = UNPACK_DIR

        global RAW_UNPACK_DIR
        if RAW_UNPACK_DIR is None:
            RAW_UNPACK_DIR = raw_unpack_pkg(fn)
        self.raw_unpack_dir = RAW_UNPACK_DIR

        self.is_click = False
        self.is_snap1 = False
        self.is_snap2 = False
        self.pkgfmt = {"type": "", "version": ""}

        (self.pkgfmt["type"], pkgver) = detect_package(fn, self.unpack_dir)

        if self._pkgfmt_type() == "snap":
            if pkgver < 2:
                self.is_snap1 = True
                self.pkgfmt["version"] = "15.04"
            else:
                self.is_snap2 = True
                self.pkgfmt["version"] = "16.04"
        elif self._pkgfmt_type() == "click":
            self.pkgfmt["version"] = "0.4"
            self.is_click = True
        else:
            error("Unknown package type: '%s'" % self._pkgfmt_type())

        # Get a list of all unpacked files
        self.pkg_files = []
        # self._list_all_files() sets self.pkg_files so we can mock it
        self._list_all_files()

        # Setup what is needed to get a list of all unpacked compiled binaries
        self.pkg_bin_files = []
        # self._list_all_compiled_binaries() sets self.pkg_files so we can
        # mock it
        self._list_all_compiled_binaries()

        self.overrides = overrides if overrides is not None else {}

        self.override_result_type = None

    def set_report_type(self, t):
        global REPORT_OUTPUT
        if t is not None and t in ["console", "json"]:
            REPORT_OUTPUT = t

    def _check_innerpath_executable(self, fn):
        '''Check that the provided path exists and is executable'''
        return os.access(fn, os.X_OK)

    def _extract_statinfo(self, fn):
        '''Extract statinfo from file'''
        try:
            st = os.stat(fn)
        except Exception:
            return None
        return st

    def _extract_file(self, fn):
        '''Extract file'''
        if not fn.startswith('/'):
            error("_extract_file() expects absolute path")
        rel = os.path.relpath(fn, self.unpack_dir)

        if not os.path.isfile(fn):
            error("Could not find '%s'" % rel)
        return open_file_read(fn)

    def _path_join(self, dirname, rest):
        return os.path.join(dirname, rest)

    def _get_sha512sum(self, fn):
        '''Get sha512sum of file'''
        (rc, out) = cmd(['sha512sum', fn])
        if rc != 0:
            return None
        return out.split()[0]

    def _pkgfmt_type(self):
        '''Return the package format type'''
        if "type" not in self.pkgfmt:
            return ""
        return self.pkgfmt["type"]

    def _pkgfmt_version(self):
        '''Return the package format version'''
        if "version" not in self.pkgfmt:
            return ""
        return self.pkgfmt["version"]

    def _check_package_exists(self):
        '''Check that the provided package exists'''
        if not os.path.exists(self.pkg_filename):
            error("Could not find '%s'" % self.pkg_filename)

    def _list_all_files(self):
        '''List all files included in this click package.'''
        global PKG_FILES
        if PKG_FILES is None:
            PKG_FILES = []
            for root, dirnames, filenames in os.walk(self.unpack_dir):
                for f in filenames:
                    PKG_FILES.append(os.path.join(root, f))

        self.pkg_files = PKG_FILES

    def _check_if_message_catalog(self, fn):
        '''Check if file is a message catalog (.mo file).'''
        if fn.endswith('.mo'):
            return True
        return False

    def _list_all_compiled_binaries(self):
        '''List all compiled binaries in this click package.'''
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

                if res in self.magic_binary_file_descriptions and \
                   not self._check_if_message_catalog(i) and \
                   i not in PKG_BIN_FILES:
                    PKG_BIN_FILES.append(i)

        self.pkg_bin_files = PKG_BIN_FILES

    def _get_check_name(self, name, app='', extra=''):
        name = ':'.join([self.review_type, name])
        if app:
            name += ':' + app
        if extra:
            name += ':' + extra
        return name

    def _verify_pkgversion(self, v):
        '''Verify package name'''
        if not isinstance(v, (str, int, float)):
            return False
        re_valid_version = re.compile(r'^((\d+):)?'              # epoch
                                      '([A-Za-z0-9.+:~-]+?)'     # upstream
                                      '(-([A-Za-z0-9+.~]+))?$')  # debian
        if re_valid_version.match(str(v)):
            return True
        return False

    # click_report[<result_type>][<review_name>] = <result>
    #   result_type: info, warn, error
    #   review_name: name of the check (prefixed with self.review_type)
    #   result: contents of the review
    #   link: url for more information
    #   manual_review: force manual review
    #   override_result_type: prefix results with [<result_type>] and set
    #     result_type to override_result_type
    def _add_result(self, result_type, review_name, result, link=None,
                    manual_review=False, override_result_type=None,
                    stage=False):
        '''Add result to report'''
        global RESULT_TYPES
        if stage:
            report = self.stage_report
        else:
            report = self.click_report

        if result_type not in RESULT_TYPES:
            error("Invalid result type '%s'" % result_type)

        prefix = ""
        if override_result_type is not None:
            if override_result_type not in RESULT_TYPES:
                error("Invalid override result type '%s'" %
                      override_result_type)
            prefix = "[%s] " % result_type.upper()
            result_type = override_result_type

        if review_name not in report[result_type]:
            # log info about check so it can be collected into the
            # check-names.list file
            # format should be
            # CHECK|<review_type:check_name>|<link>
            msg = 'CHECK|{}|{}'
            name = ':'.join(review_name.split(':')[:2])
            link_text = link if link is not None else ""
            logging.debug(msg.format(name, link_text))
            report[result_type][review_name] = dict()

        report[result_type][review_name].update({
            'text': "%s%s" % (prefix, result),
            'manual_review': manual_review,
        })
        if link is not None:
            report[result_type][review_name]["link"] = link

    def _apply_staged_results(self):
        '''Merge the staged report into the main report'''
        global RESULT_TYPES
        for result_type in self.stage_report:
            if result_type not in RESULT_TYPES:
                error("Invalid result type '%s'" % result_type)

            for review_name in self.stage_report[result_type]:
                if review_name not in self.click_report[result_type]:
                    self.click_report[result_type][review_name] = dict()
                for key in self.stage_report[result_type][review_name]:
                    self.click_report[result_type][review_name][key] = \
                        self.stage_report[result_type][review_name][key]
            # reset the staged report
            self.stage_report[result_type] = dict()

    # Only called by ./bin/* individually, not 'click-review'
    def do_report(self):
        '''Print report'''
        global REPORT_OUTPUT

        if REPORT_OUTPUT == "json":
            jsonmsg(self.click_report)
        else:
            import pprint
            pprint.pprint(self.click_report)

        rc = 0
        if len(self.click_report['error']):
            rc = 2
        elif len(self.click_report['warn']):
            rc = 1
        return rc

    def do_checks(self):
        '''Run all methods that start with check_'''
        methodList = [name for name, member in
                      inspect.getmembers(self, inspect.ismethod)
                      if isinstance(member, types.MethodType)]
        for methodname in methodList:
            if not methodname.startswith("check_"):
                continue
            func = getattr(self, methodname)
            func()

    def set_review_type(self, name):
        '''Set review name'''
        self.review_type = name


#
# Utility functions
#

def error(out, exit_code=1, do_exit=True):
    '''Print error message and exit'''
    global REPORT_OUTPUT
    global RESULT_TYPES

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
            report[family]['error'][name] = dict()
            report[family]['error'][name]['text'] = out
            report[family]['error'][name]['manual_review'] = True

            jsonmsg(report)
        else:
            print("ERROR: %s" % (out), file=sys.stderr)
    except IOError:
        pass

    if do_exit:
        sys.exit(exit_code)


def warn(out):
    '''Print warning message'''
    try:
        print("WARN: %s" % (out), file=sys.stderr)
    except IOError:
        pass


def msg(out, output=sys.stdout):
    '''Print message'''
    try:
        print("%s" % (out), file=output)
    except IOError:
        pass


def debug(out):
    '''Print debug message'''
    if 'SNAP_DEBUG' in os.environ:
        try:
            print("DEBUG: %s" % (out), file=sys.stderr)
        except IOError:
            pass


def jsonmsg(out):
    '''Format out as json'''
    msg(json.dumps(out,
                   sort_keys=True,
                   indent=2,
                   separators=(',', ': ')))


def cmd(command):
    '''Try to execute the given command.'''
    debug(" ".join(command))
    try:
        sp = subprocess.Popen(command, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
    except OSError as ex:
        return [127, str(ex)]

    if sys.version_info[0] >= 3:
        out = sp.communicate()[0].decode('ascii', 'ignore')
    else:
        out = sp.communicate()[0]

    return [sp.returncode, out]


def cmd_pipe(command1, command2):
    '''Try to pipe command1 into command2.'''
    try:
        sp1 = subprocess.Popen(command1, stdout=subprocess.PIPE)
        sp2 = subprocess.Popen(command2, stdin=sp1.stdout)
    except OSError as ex:
        return [127, str(ex)]

    if sys.version_info[0] >= 3:
        out = sp2.communicate()[0].decode('ascii', 'ignore')
    else:
        out = sp2.communicate()[0]

    return [sp2.returncode, out]


def _unpack_cmd(cmd_args, d, dest):
    '''Low level unpack helper'''
    curdir = os.getcwd()
    os.chdir(d)

    (rc, out) = cmd(cmd_args)
    os.chdir(curdir)

    if rc != 0:
        if os.path.isdir(d):
            recursive_rm(d)
        error("unpacking failed with '%d':\n%s" % (rc, out))

    if dest is None:
        dest = d
    else:
        shutil.move(d, dest)

    return dest


def _calculate_snap_unsquashfs_uncompressed_size(snap_pkg):
    '''Calculate size of the uncompressed snap'''
    (rc, out) = cmd(['unsquashfs', '-lls', snap_pkg])
    if rc != 0:
        error("unsquashfs -lls '%s' failed: %s" % (snap_pkg, out))

    size = 0
    for line in out.splitlines():
        if not line.startswith('-'):  # skip non-regular files
            continue
        try:
            size += int(line.split()[2])
        except ValueError:  # skip non-numbers
            continue

    return size


def _unpack_snap_squashfs(snap_pkg, dest, item=None):
    '''Unpack a squashfs based snap package to dest'''
    size = _calculate_snap_unsquashfs_uncompressed_size(snap_pkg)

    max = MAX_UNCOMPRESSED_SIZE * 1024 * 1024 * 1024

    st = os.statvfs(snap_pkg)
    avail = st.f_bsize * st.f_bavail * .9  # 90% of available space
    if size > max:
        error("uncompressed snap is too large (%dM > %dM)" %
              (size / 1024 / 1024, max / 1024 / 1024))
    elif size > avail * .9:
        error("uncompressed snap is too large for available space (%dM > %dM)"
              % (size / 1024 / 1024, avail / 1024 / 1024))

    global MKDTEMP_PREFIX
    global MKDTEMP_DIR
    d = tempfile.mkdtemp(prefix=MKDTEMP_PREFIX, dir=MKDTEMP_DIR)
    cmd = ['unsquashfs', '-f', '-d', d, os.path.abspath(snap_pkg)]
    if item is not None:
        cmd.append(item)
    return _unpack_cmd(cmd, d, dest)


def _unpack_click_deb(pkg, dest):
    global MKDTEMP_PREFIX
    global MKDTEMP_DIR
    d = tempfile.mkdtemp(prefix=MKDTEMP_PREFIX, dir=MKDTEMP_DIR)
    return _unpack_cmd(['dpkg-deb', '-R',
                        os.path.abspath(pkg), d], d, dest)


def unpack_pkg(fn, dest=None, item=None):
    '''Unpack package'''
    if not os.path.isfile(fn):
        error("Could not find '%s'" % fn)
    pkg = fn
    if not pkg.startswith('/'):
        pkg = os.path.abspath(pkg)

    if dest is not None and os.path.exists(dest):
        error("'%s' exists. Aborting." % dest)

    # Limit the maximimum size of the package
    size = os.stat(pkg)[stat.ST_SIZE]
    max = MAX_COMPRESSED_SIZE * 1024 * 1024 * 1024
    if size > max:
        error("compressed file is too large (%dM > %dM)" %
              (size / 1024 / 1024, max / 1024 / 1024))

    # check if its a squashfs based snap
    if is_squashfs(pkg):
        return _unpack_snap_squashfs(fn, dest, item)

    return _unpack_click_deb(fn, dest)


def is_squashfs(filename):
    '''Return true if the given filename as a squashfs header'''
    with open(filename, 'rb') as f:
        header = f.read(10)
    return header.startswith(b"hsqs")


def raw_unpack_pkg(fn, dest=None):
    '''Unpack raw package'''
    if not os.path.isfile(fn):
        error("Could not find '%s'" % fn)
    pkg = fn
    if not pkg.startswith('/'):
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
    (rc, out) = cmd(['ar', 'x', pkg])
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
    '''Create/reuse a temporary directory that is automatically cleaned up'''
    global TMP_DIR
    global MKDTEMP_PREFIX
    global MKDTEMP_DIR
    if TMP_DIR is None:
        TMP_DIR = tempfile.mkdtemp(prefix=MKDTEMP_PREFIX, dir=MKDTEMP_DIR)
    return TMP_DIR


def open_file_read(path):
    '''Open specified file read-only'''
    try:
        orig = codecs.open(path, 'r', "UTF-8")
    except Exception:
        raise

    return orig


def open_file_write(path):
    '''Open specified file read-write'''
    try:
        orig = codecs.open(path, 'w', "UTF-8")
    except Exception:
        raise

    return orig


def recursive_rm(dirPath, contents_only=False, top=True):
    '''recursively remove directory'''
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


def detect_package(fn, dir):
    '''Detect what type of package this is'''
    pkgtype = None
    pkgver = None

    if not os.path.isfile(fn):
        error("Could not find '%s'" % fn)

    if dir is None:
        error("Invalid unpack directory 'None'")

    unpack_dir = dir
    if not os.path.isdir(unpack_dir):
        error("Could not find '%s'" % unpack_dir)

    pkg = fn
    if not pkg.startswith('/'):
        pkg = os.path.abspath(pkg)

    # check if its a squashfs based snap
    if is_squashfs(pkg):
        # 16.04+ squashfs snaps
        pkgtype = "snap"
        pkgver = 2
    elif os.path.exists(os.path.join(unpack_dir, "meta/package.yaml")):
        # 15.04 ar-based snaps
        pkgtype = "snap"
        pkgver = 1
    else:
        pkgtype = "click"
        pkgver = 1

    if dir is None and os.path.isdir(unpack_dir):
        recursive_rm(unpack_dir)

    return (pkgtype, pkgver)


def find_external_symlinks(unpack_dir, pkg_files, pkgname):
    '''Check if symlinks in the package go out to the system.'''
    common = '(-[0-9.]+)?\.so(\.[0-9.]+)?'
    libc6_libs = ['ld-*.so',
                  'libanl',
                  'libBrokenLocale',
                  'libc',
                  'libcidn',
                  'libcrypt',
                  'libdl',
                  'libmemusage',
                  'libm',
                  'libmvec',
                  'libnsl',
                  'libnss_compat',
                  'libnss_dns',
                  'libnss_files',
                  'libnss_hesiod',
                  'libnss_nisplus',
                  'libnss_nis',
                  'libpcprofile',
                  'libpthread',
                  'libresolv',
                  'librt',
                  'libSegFault',
                  'libthread_db',
                  'libutil',
                  ]
    libc6_pats = []
    for lib in libc6_libs:
        libc6_pats.append(re.compile(r'%s%s' % (lib, common)))
    libc6_pats.append(re.compile(r'ld-*.so$'))
    libc6_pats.append(re.compile(r'ld-linux-.*.so\.[0-9.]+$'))
    libc6_pats.append(re.compile(r'ld64.so\.[0-9.]+$'))  # ppc64el

    def _in_patterns(pats, f):
        for pat in pats:
            if pat.search(f):
                return True
        return False

    def _is_external(link, pats, pkgname):
        rp = os.path.realpath(link)

        if rp.startswith('/') and len(rp) > 1 and \
                pkgname in common_external_symlink_override:
            if rp.startswith(unpack_dir + "/"):
                rel = os.path.relpath(rp, unpack_dir)
            else:
                rel = rp[1:]
            if rel in common_external_symlink_override[pkgname]:
                return False

        if not rp.startswith(unpack_dir + "/") and \
                not rp.startswith(os.path.join("/snap", pkgname) + "/") and \
                not rp.startswith(
                    os.path.join("/var/snap", pkgname) + "/") and \
                not _in_patterns(pats, os.path.basename(link)):
            return True
        return False

    external_symlinks = list(filter(lambda link:
                             _is_external(link, libc6_pats, pkgname),
                             pkg_files))

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


def check_results(testobj, report,
                  expected_counts={'info': 1, 'warn': 0, 'error': 0},
                  expected=None):
    if expected is not None:
        for t in expected.keys():
            for r in expected[t]:
                testobj.assertTrue(r in report[t],
                                   "Could not find '%s' (%s) in:\n%s" %
                                   (r, t, json.dumps(report, indent=2)))
                for k in expected[t][r]:
                    testobj.assertTrue(k in report[t][r],
                                       "Could not find '%s' (%s) in:\n%s" %
                                       (k, r, json.dumps(report, indent=2)))
                testobj.assertEqual(expected[t][r][k], report[t][r][k])
    else:
        for k in expected_counts.keys():
            if expected_counts[k] is None:
                continue
            testobj.assertEqual(len(report[k]), expected_counts[k],
                                "(%s not equal)\n%s" %
                                (k, json.dumps(report, indent=2)))


def read_file_as_json_dict(fn):
    '''Read in filename as json dict'''
    # XXX: consider reading in as stream
    debug("Loading: %s" % fn)
    raw = {}
    fd = open_file_read(fn)
    try:
        raw = json.load(fd)
    except Exception:
        raise
        error("Could not load %s. Is it properly formatted?" % fn)

    return raw


def get_snap_manifest(fn):
    if 'SNAP_USER_COMMON' in os.environ and \
            os.path.exists(os.environ['SNAP_USER_COMMON']):
        MKDTEMP_DIR = os.environ['SNAP_USER_COMMON']
    else:
        MKDTEMP_DIR = tempfile.gettempdir()

    man = "snap/manifest.yaml"
    # unpack_pkg() fails if this exists, so this is safe
    dir = tempfile.mktemp(prefix=MKDTEMP_PREFIX, dir=MKDTEMP_DIR)
    unpack_pkg(fn, dir, man)

    man_fn = os.path.join(dir, man)
    if not os.path.isfile(man_fn):
        recursive_rm(dir)
        error("%s not in %s" % (man, fn))

    fd = open_file_read(man_fn)
    try:
        man_yaml = yaml.safe_load(fd)
    except Exception:
        recursive_rm(dir)
        error("Could not load snap/manifest.yaml. Is it properly "
              "formatted?")

    recursive_rm(dir)

    return man_yaml


# TODO: make this a class
def _add_error(name, errors, msg):
    if name not in errors:
        errors[name] = []
    errors[name].append(msg)
