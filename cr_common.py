'''common.py: common classes and functions'''
#
# Copyright (C) 2013 Canonical Ltd.
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
import codecs
from debian.deb822 import Deb822
import inspect
import json
import os
import pprint
import shutil
import subprocess
import sys
import tempfile
import types

DEBUGGING = False


#
# Utility classes
#
class ClickReviewException(Exception):
    '''This class represents ClickReview exceptions'''
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ClickReview(object):
    '''This class represents click reviews'''
    def __init__(self, fn, review_type):
        if not os.path.exists(fn):
            error("Could not find '%s'" % fn)
        self.click_package = fn

        if not self.click_package.endswith(".click"):
            error("filename does not end with '.click'")

        self.review_type = review_type
        self.click_report = dict()

        self.result_types = ['info', 'warn', 'error']
        for r in self.result_types:
            self.click_report[r] = dict()

        self.click_report_output = "json"

        self.unpack_dir = unpack_click(fn)

        # Get some basic information from the control file
        fh = open_file_read(os.path.join(self.unpack_dir, "DEBIAN/control"))
        tmp = list(Deb822.iter_paragraphs(fh.readlines()))
        fh.close()
        if len(tmp) != 1:
            error("malformed control file: too many paragraphs")
        control = tmp[0]
        self.click_pkgname = control['Package']
        self.click_version = control['Version']
        self.click_arch = control['Architecture']

        # Parse and store the manifest
        m = os.path.join(self.unpack_dir, "DEBIAN/manifest")
        if not os.path.isfile(m):
            error("Could not find manifest file")
        try:
            self.manifest = json.load(open_file_read(m))
        except Exception:
            error("Could not load manifest file. Is it properly formatted?")
        self._verify_manifest_structure(self.manifest)

    def _verify_manifest_structure(self, manifest):
        '''Verify manifest has the expected structure'''
        # lp:click doc/file-format.rst
        mp = pprint.pformat(manifest)
        if not isinstance(manifest, dict):
            error("manifest malformed:\n%s" % manifest)

        required = ["name", "version", "framework"]        # click required
        for f in required:
            if f not in manifest:
                error("could not find required '%s' in manifest:\n%s" % (f,
                                                                         mp))
            elif not isinstance(manifest[f], str):
                error("manifest malformed: '%s' is not str:\n%s" % (f, mp))

        optional = ["title", "description", "maintainer"]  # appstore optional
                                                           # fields here
        for f in optional:
            if f in manifest and not isinstance(manifest[f], str):
                error("manifest malformed: '%s' is not str:\n%s" % (f, mp))

        # Not required by click, but required by appstore. 'hooks' is assumed
        # to be present in other checks
        if 'hooks' not in manifest:
            error("could not find required 'hooks' in manifest:\n%s" % mp)
        if not isinstance(manifest['hooks'], dict):
            error("manifest malformed: 'hooks' is not dict:\n%s" % mp)
        # 'hooks' is assumed to be present and non-empty in other checks
        if len(manifest['hooks']) < 1:
            error("manifest malformed: 'hooks' is empty:\n%s" % mp)
        for app in manifest['hooks']:
            if not isinstance(manifest['hooks'][app], dict):
                error("manifest malformed: hooks/%s is not dict:\n%s" % (app,
                                                                         mp))
            # let cr_lint.py handle required hooks
            if len(manifest['hooks'][app]) < 1:
                error("manifest malformed: hooks/%s is empty:\n%s" % (app, mp))

        for k in sorted(manifest):
            if k not in required + optional + ['hooks']:
                # click supports local extensions via 'x-...', ignore those
                # here but report in lint
                if k.startswith('x-'):
                    continue
                error("manifest malformed: unsupported field '%s':\n%s" % (k,
                                                                           mp))

    def __del__(self):
        '''Cleanup'''
        if hasattr(self, 'unpack_dir') and os.path.isdir(self.unpack_dir):
            recursive_rm(self.unpack_dir)

    def set_review_type(self, name):
        '''Set review name'''
        self.review_type = name

    #
    # click_report[<result_type>][<review_name>] = <review>
    #   result_type: info, warn, error
    #   review_name: name of the check (prefixed with self.review_type)
    #   review: contents of the review
    def _add_result(self, result_type, review_name, result):
        '''Add result to report'''
        if result_type not in self.result_types:
            error("Invalid result type '%s'" % result_type)

        name = "%s_%s" % (self.review_type, review_name)
        if name not in self.click_report[result_type]:
            self.click_report[result_type][name] = dict()

        self.click_report[result_type][name] = result

    def do_report(self):
        '''Print report'''
        if self.click_report_output == "console":
            # TODO: format better
            import pprint
            pprint.pprint(self.click_report)
        elif self.click_report_output == "json":
            import json
            msg(json.dumps(self.click_report,
                           sort_keys=True,
                           indent=2,
                           separators=(',', ': ')))

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


#
# Utility functions
#
def error(out, exit_code=1, do_exit=True):
    '''Print error message and exit'''
    try:
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
    global DEBUGGING
    if DEBUGGING:
        try:
            print("DEBUG: %s" % (out), file=sys.stderr)
        except IOError:
            pass


def cmd(command):
    '''Try to execute the given command.'''
    debug(command)
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


def unpack_click(fn, dest=None):
    '''Unpack click package'''
    if not os.path.isfile(fn):
        error("Could not find '%s'" % fn)
    click_pkg = fn
    if not click_pkg.startswith('/'):
        click_pkg = os.path.absname(click_pkg)

    if dest is not None and os.path.exists(dest):
        error("'%s' exists. Aborting." % dest)

    d = tempfile.mkdtemp(prefix='clickreview-')

    curdir = os.getcwd()
    os.chdir(d)
    (rc, out) = cmd(['dpkg-deb', '-R', click_pkg, d])
    os.chdir(curdir)

    if rc != 0:
        if os.path.isdir(d):
            recursive_rm(d)
        error("dpkg-deb -R failed with '%d':\n%s" % (rc, out))

    if dest is None:
        dest = d
    else:
        shutil.move(d, dest)

    return dest


def open_file_read(path):
    '''Open specified file read-only'''
    try:
        orig = codecs.open(path, 'r', "UTF-8")
    except Exception:
        raise

    return orig


def recursive_rm(dirPath, contents_only=False):
    '''recursively remove directory'''
    names = os.listdir(dirPath)
    for name in names:
        path = os.path.join(dirPath, name)
        if os.path.islink(path) or not os.path.isdir(path):
            os.unlink(path)
        else:
            recursive_rm(path)
    if contents_only is False:
        os.rmdir(dirPath)
