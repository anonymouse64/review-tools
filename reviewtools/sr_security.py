'''sr_security.py: snap security checks'''
#
# Copyright (C) 2013-2018 Canonical Ltd.
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

from reviewtools.sr_common import (
    SnapReview,
)
from reviewtools.common import (
    cmd,
    create_tempdir,
    open_file_write,
    ReviewException,
    AA_PROFILE_NAME_MAXLEN,
    AA_PROFILE_NAME_ADVLEN,
    MKSQUASHFS_OPTS,
)
from reviewtools.overrides import (
    sec_browser_support_overrides,
    sec_iface_ref_overrides,
    sec_mode_overrides,
    sec_resquashfs_overrides,
)
import os
import re
import shutil


class SnapReviewSecurity(SnapReview):
    '''This class represents snap security reviews'''
    def __init__(self, fn, overrides=None):
        SnapReview.__init__(self, fn, "security-snap-v2", overrides=overrides)

    def _unsquashfs_lls(self, snap_pkg):
        '''Run unsquashfs -lls on a snap package'''
        return cmd(['unsquashfs', '-lls', snap_pkg])

    def check_security_plugs_browser_support_with_daemon(self):
        '''Check security plugs - browser-support not used with daemon'''
        def _plugref_is_interface(ref, iface):
            if ref == iface:
                return True
            elif 'plugs' in self.snap_yaml and \
                    ref in self.snap_yaml['plugs'] and \
                    'interface' in self.snap_yaml['plugs'][ref] and \
                    self.snap_yaml['plugs'][ref]['interface'] == iface:
                return True
            return False

        if 'apps' not in self.snap_yaml:
            return

        found_app_plugs = False
        for app in self.snap_yaml['apps']:
            if 'plugs' in self.snap_yaml['apps'][app]:
                found_app_plugs = True
                break

        if not found_app_plugs and 'plugs' not in self.snap_yaml:
            return

        for app in self.snap_yaml['apps']:
            if found_app_plugs and 'plugs' not in self.snap_yaml['apps'][app]:
                continue
            elif 'plugs' in self.snap_yaml['apps'][app]:
                plugs = self.snap_yaml['apps'][app]['plugs']
            else:
                plugs = self.snap_yaml['plugs']

            if 'daemon' not in self.snap_yaml['apps'][app]:
                continue

            for plug_ref in plugs:
                if _plugref_is_interface(plug_ref, "browser-support"):
                    if self.snap_yaml['name'] in \
                            sec_browser_support_overrides:
                        t = 'info'
                        s = "OK (allowing 'daemon' with 'browser-support')"
                    else:
                        t = 'warn'
                        s = "(NEEDS REVIEW) 'daemon' should not be used " + \
                            "with 'browser-support'"
                    n = self._get_check_name('daemon_with_browser-support',
                                             app=app)
                    self._add_result(t, n, s, manual_review=True)

    def check_apparmor_profile_name_length(self):
        '''Check AppArmor profile name length'''
        if 'apps' not in self.snap_yaml:
            return

        maxlen = AA_PROFILE_NAME_MAXLEN
        advlen = AA_PROFILE_NAME_ADVLEN

        for app in self.snap_yaml['apps']:
            t = 'info'
            n = self._get_check_name('profile_name_length', app=app)
            s = "OK"
            profile = "snap.%s.%s" % (self.snap_yaml['name'], app)
            if len(profile) > maxlen:
                t = 'error'
                s = ("'%s' too long (exceeds %d characters). Please shorten "
                     "'%s' and/or '%s'" % (profile, maxlen,
                                           self.snap_yaml['name'], app))
            elif len(profile) > advlen:
                t = 'warn'
                s = ("'%s' is long (exceeds %d characters) and thus could be "
                     "problematic in certain environments. Please consider "
                     "shortening '%s' and/or '%s'" % (profile, advlen,
                                                      self.snap_yaml['name'],
                                                      app))
            self._add_result(t, n, s)

    def _debug_resquashfs(self, tmpdir, orig, resq):
        '''Provide debugging information on snap and repacked snap'''
        debug_output = ""
        orig_lls_fn = os.path.join(tmpdir, os.path.basename(orig) + '.lls')
        resq_lls_fn = os.path.join(tmpdir, os.path.basename(resq) + '.lls')

        error = False
        for fn in [orig, resq]:
            cmdline = ['unsquashfs', '-fstime', fn]
            (rc, out) = cmd(cmdline)
            if rc != 0:
                debug_output += "'%s' failed" % " ".join(cmdline)
                error = True
                continue
            debug_output += "squash fstime for %s: %s" % (os.path.basename(fn),
                                                          out)

            cmdline = ['unsquashfs', '-lls', fn]
            (rc, out) = cmd(cmdline)
            if rc != 0:
                debug_output += "'%s' failed" % " ".join(cmdline)
                error = True
                continue
            debug_output += "unsquashfs -lls %s:\n%s" % (os.path.basename(fn),
                                                         out)

            lls_fn = orig_lls_fn
            if fn == resq:
                lls_fn = resq_lls_fn
            with open_file_write(lls_fn) as f:
                f.write(out)

        if not error:
            cmdline = ['diff', '-au', orig_lls_fn, resq_lls_fn]
            (rc, out) = cmd(cmdline)
            debug_output += "%s:\n%s" % (" ".join(cmdline), out)

        return debug_output

    def check_squashfs_resquash(self):
        '''Check resquash of squashfs'''
        fn = os.path.abspath(self.pkg_filename)

        # Verify squashfs has no fragments. If it does, it will not resquash
        # properly (LP: #1576763). This stat output for fragments has been
        # stable for at least the last 7 years, so just parse it. If it changes
        # we can consider examing the superblock directly.
        oldlang = ""
        if 'LANG' in os.environ:
            oldlang = os.environ['LANG']
        (rc, out) = cmd(['unsquashfs', '-s', fn])
        os.environ['LANG'] = oldlang
        if rc != 0:
            t = 'error'
            n = self._get_check_name('squashfs_stat')
            s = 'could not stat squashfs'
            self._add_result(t, n, s)
            return

        if '\nNumber of fragments 0\n' not in out and \
                ('SNAP_ENFORCE_RESQUASHFS' not in os.environ or
                 ('SNAP_ENFORCE_RESQUASHFS' in os.environ and
                  os.environ['SNAP_ENFORCE_RESQUASHFS'] != "0")):
            link = 'https://forum.snapcraft.io/t/automated-reviews-and-snapcraft-2-38/4982/17'
            t = 'error'
            n = self._get_check_name('squashfs_fragments')
            s = "The squashfs was built without '-no-fragments'. Please " + \
                "ensure the snap is created with either 'snapcraft pack " + \
                "<DIR>' (using snapcraft >= 2.38) or 'mksquashfs <dir> " + \
                "<snap> %s'" % " ".join(MKSQUASHFS_OPTS) + ". If using electron-builder, " \
                "please upgrade to latest stable (>= 20.14.7). See %s " \
                "for details." % link

            if self.snap_yaml['name'] in sec_resquashfs_overrides:
                t = 'info'
                s = "OK (check not enforced for this snap): %s" % s

            self._add_result(t, n, s)
            return

        # Verify squashfs supports the -fstime option, if not, warn (which
        # blocks in store)
        (rc, out) = cmd(['unsquashfs', '-fstime', fn])
        if rc != 0:
            t = 'warn'
            n = self._get_check_name('squashfs_supports_fstime')
            s = 'could not determine fstime of squashfs'
            self._add_result(t, n, s)
            return
        fstime = out.strip()

        if 'SNAP_ENFORCE_RESQUASHFS' in os.environ and \
                os.environ['SNAP_ENFORCE_RESQUASHFS'] == "0":
            t = 'info'
            n = self._get_check_name('squashfs_repack_checksum')
            s = "OK (check not enforced)"
            self._add_result(t, n, s)
            return

        tmpdir = create_tempdir()  # this is autocleaned
        tmp_unpack = os.path.join(tmpdir, 'squashfs-root')
        tmp_repack = os.path.join(tmpdir, 'repack.snap')
        fakeroot_env = os.path.join(tmpdir, 'fakeroot.env')

        # Don't use -all-root since the snap might have other users in it
        # NOTE: adding -no-xattrs here causes resquashfs to fail (unsquashfs
        # and mksquash use -xattrs by default. By specifying -no-xattrs to
        # unsquashfs/mksquashfs, we enforce not supportinging them since the
        # checksums will always be different because the original squash would
        # have them but the repack would not). If we ever decide to support
        # xattrs in snaps, would have to see why thre requash fails with
        # -xattrs.
        mksquashfs_ignore_opts = ['-all-root']

        curdir = os.getcwd()
        os.chdir(tmpdir)
        # ensure we don't alter the permissions from the unsquashfs
        old_umask = os.umask(000)

        fakeroot_cmd = []
        if 'SNAP_FAKEROOT_RESQUASHFS' in os.environ:
            # We could use -l $SNAP/usr/lib/... --faked $SNAP/usr/bin/faked if
            # os.environ['SNAP'] is set, but instead we let the snap packaging
            # make fakeroot work correctly and keep this simple.
            fakeroot_cmd = ['fakeroot', '--unknown-is-real']

            if shutil.which(fakeroot_cmd[0]) is None:  # pragma: nocover
                t = 'error'
                n = self._get_check_name('has_fakeroot')
                s = "Could not find 'fakeroot' command"
                self._add_result(t, n, s)
                return

        try:
            fakeroot_args = []
            mksquash_opts = MKSQUASHFS_OPTS
            if 'SNAP_FAKEROOT_RESQUASHFS' in os.environ:
                # run unsquashfs under fakeroot, saving the session to be
                # reused by mksquashfs and thus preserving
                # uids/gids/devices/etc
                fakeroot_args = ['-s', fakeroot_env]

                mksquash_opts = []
                for i in MKSQUASHFS_OPTS:
                    if i not in mksquashfs_ignore_opts:
                        mksquash_opts.append(i)

            cmdline = fakeroot_cmd + fakeroot_args + \
                ['unsquashfs', '-d', tmp_unpack, fn]

            (rc, out) = cmd(cmdline)
            if rc != 0:
                raise ReviewException("could not unsquash '%s': %s" %
                                      (os.path.basename(fn), out))

            fakeroot_args = []
            if 'SNAP_FAKEROOT_RESQUASHFS' in os.environ:
                fakeroot_args = ['-i', fakeroot_env]

            cmdline = fakeroot_cmd + fakeroot_args + \
                ['mksquashfs', tmp_unpack, tmp_repack, '-fstime', fstime] + \
                mksquash_opts

            (rc, out) = cmd(cmdline)
            if rc != 0:
                raise ReviewException("could not mksquashfs '%s': %s" %
                                      (os.path.relpath(tmp_unpack, tmpdir),
                                       out))
        except ReviewException as e:
            t = 'error'
            n = self._get_check_name('squashfs_resquash')
            self._add_result(t, n, str(e))
            return
        finally:
            os.umask(old_umask)
            os.chdir(curdir)

        # Now calculate the hashes
        t = 'info'
        n = self._get_check_name('squashfs_repack_checksum')
        s = "OK"
        link = None

        (rc, out) = cmd(['sha512sum', fn])
        if rc != 0:
            t = 'error'
            s = "could not determine checksum of '%s'" % os.path.basename(fn)
            self._add_result(t, n, s)
            return
        orig_sum = out.split()[0]

        (rc, out) = cmd(['sha512sum', tmp_repack])
        if rc != 0:
            t = 'error'
            s = "could not determine checksum of '%s'" % \
                os.path.relpath(tmp_repack, tmpdir)
            self._add_result(t, n, s)
            return
        repack_sum = out.split()[0]

        if orig_sum != repack_sum:
            if 'SNAP_DEBUG_RESQUASHFS' in os.environ:
                print(self._debug_resquashfs(tmpdir, fn, tmp_repack))

                if os.environ['SNAP_DEBUG_RESQUASHFS'] == "2":
                    import subprocess
                    print("\nIn debug shell. tmpdir=%s, orig=%s, repack=%s" %
                          (tmpdir, fn, tmp_repack))
                    subprocess.call(['bash'])

            if 'type' in self.snap_yaml and \
                    (self.snap_yaml['type'] == 'base' or
                     self.snap_yaml['type'] == 'os'):
                mksquash_opts = []
                for i in MKSQUASHFS_OPTS:
                    if i not in mksquashfs_ignore_opts:
                        mksquash_opts.append(i)
            else:
                mksquash_opts = MKSQUASHFS_OPTS

            link = 'https://forum.snapcraft.io/t/automated-reviews-and-snapcraft-2-38/4982/17'
            t = 'error'
            s = "checksums do not match. Please ensure the snap is " + \
                "created with either 'snapcraft pack <DIR>' (using " + \
                "snapcraft >= 2.38) or 'mksquashfs <dir> <snap> %s'" % \
                " ".join(mksquash_opts) + ". If using electron-builder, " \
                "please upgrade to latest stable (>= 20.14.7). See %s " \
                "for details." % link

            pkgname = self.snap_yaml['name']
            if pkgname in sec_resquashfs_overrides:
                t = 'info'
                s = "OK (check not enforced for this snap): %s" % s

            # FIXME: fakeroot sporadically fails and saves the wrong
            # uid/gid/mode into its save file, thus causing the mksquashfs to
            # create the wrong file/perms/ownership. We want to not ignore this
            # error when using fakeroot. We need fakeroot or something like it
            # for unsquashfs to create devices, perms and ownership as
            # non-root, but only base and os snaps are allowed to have devices
            # and not use -all-root. Certain app snaps may also have
            # sec_mode_overrides for setuid/setgid files. Therefore, when not
            # using fakeroot, only enforce resquash for non-os/base snaps
            # and other snaps without sec_mode_overrides that specify
            # setuid/setgid. Eventually we'll fix fakeroot or do something else
            # so we can use this for all snaps, with or without -all-root.
            if 'SNAP_FAKEROOT_RESQUASHFS' not in os.environ:
                if self.snap_yaml['type'] in ['base', 'os']:
                    t = 'info'
                    s = "OK (check not enforced for base and os snaps)"
                    link = None
                elif pkgname in sec_mode_overrides:
                    has_sugid_override = False
                    setugid_pat = re.compile(r'[sS]')
                    for k in sec_mode_overrides[pkgname]:
                        if setugid_pat.search(sec_mode_overrides[pkgname][k]):
                            has_sugid_override = True
                            break
                    if has_sugid_override:
                        t = 'info'
                        s = "OK (check not enforced for app snaps with " + \
                            "setuid/setgid overrides)"
                        link = None

        self._add_result(t, n, s, link)

    def check_squashfs_files(self):
        '''Check squashfs files'''
        def _check_allowed_perms(mode, allowed):
            for p in mode[1:]:
                if p not in allowed:
                    return False
            return True

        pkgname = self.snap_yaml['name']

        snap_type = 'app'
        if 'type' in self.snap_yaml:
            snap_type = self.snap_yaml['type']

        fn = os.path.abspath(self.pkg_filename)

        (rc, out) = self._unsquashfs_lls(fn)
        if rc != 0:
            t = 'error'
            n = self._get_check_name('squashfs_files_unsquash')
            s = 'unsquashfs -lls <snap> failed'
            self._add_result(t, n, s)
            return

        in_header = True
        malformed = []
        errors = []

        fname_pat = re.compile(r'.* (squashfs-root)')
        date_pat = re.compile(r'^\d\d\d\d-\d\d-\d\d$')
        time_pat = re.compile(r'^\d\d:\d\d$')
        mknod_pat_full = re.compile(r'.,.')
        readdir_pat = re.compile(r'^r.xr.xr.x')
        count = 0

        for line in out.splitlines():
            count += 1
            if in_header:
                if len(line) < 1:
                    in_header = False
                continue

            tmp = line.split()
            if len(tmp) < 6:
                malformed.append("wrong number of fields in '%s'" % line)
                continue

            fname = fname_pat.sub('.', line)
            fname_full = fname_pat.sub('\\1', line)
            ftype = tmp[0][0]

            # Also see 'info ls', but we list only the Linux ones
            ftype = line[0]
            if ftype not in ['b', 'c', 'd', 'l', 'p', 's', '-']:
                errors.append("unknown type '%s' for entry '%s'" % (ftype,
                                                                    fname))
                continue

            # verify mode
            mode = tmp[0][1:]
            if len(mode) != 9:
                malformed.append("mode '%s' malformed for '%s'" % (mode,
                                                                   fname))
                continue

            # https://forum.snapcraft.io/t/incorrect-permissions-in-meta-snap-yaml/1161/8
            if fname_full in ['squashfs-root', 'squashfs-root/meta']:
                if not readdir_pat.search(mode):
                    errors.append("unable to read or access files in '%s' "
                                  "due to mode '%s'" % (fname_full, mode))
                    continue

            if ftype == 'd' or ftype == '-':
                perms = ['r', 'w', 'x', '-']
                if ftype == 'd':  # allow sticky directories for stage-packages
                    perms.append('t')
                if not _check_allowed_perms(mode, perms):
                    if pkgname not in sec_mode_overrides or \
                        fname not in sec_mode_overrides[pkgname] or \
                            sec_mode_overrides[pkgname][fname] != mode:
                        errors.append("unusual mode '%s' for entry '%s'" %
                                      (mode, fname))
                        continue
                # No point checking for world-writable, the squashfs is
                # readonly
                # if mode[-2] != '-':
                #     errors.append("'%s' is world-writable" % fn)
                #     continue
            elif ftype == 'l':
                if mode != 'rwxrwxrwx':
                    errors.append("unusual mode '%s' for symlink '%s'" %
                                  (mode, fname))
                    continue
            else:
                if snap_type != 'base' and snap_type != 'os':
                    errors.append("file type '%s' not allowed (%s)" % (ftype,
                                                                       fname))
                    continue

            # verify user and group
            if '/' not in tmp[1]:
                malformed.append("user/group '%s' malformed for '%s'" %
                                 (tmp[1], fname))
                continue
            (user, group) = tmp[1].split('/')
            # we enforce 'root/root'
            if snap_type != 'base' and snap_type != 'os' and \
                    (user != 'root' or group != 'root'):
                errors.append("unusual user/group '%s' for '%s'" % (tmp[1],
                                                                    fname))
                continue

            date_idx = 3
            time_idx = 4
            if ftype == 'b' or ftype == 'c':
                # Account for unsquashfs -lls doing:
                # crw-rw-rw- root/root             1,  8 2016-08-09 ...
                # crw-rw---- root/root            10,141 2016-08-09 ...

                if mknod_pat_full.search(tmp[2]):
                    (major, minor) = tmp[2].split(',')
                else:
                    date_idx = 4
                    time_idx = 5
                    major = tmp[2][:-1]
                    minor = tmp[3]

                try:
                    int(major)
                except Exception:
                    malformed.append("major '%s' malformed for '%s'" %
                                     (major, fname))
                try:
                    int(minor)
                except Exception:
                    malformed.append("minor '%s' malformed for '%s'" %
                                     (minor, fname))
            else:
                size = tmp[2]
                try:
                    int(size)
                except Exception:
                    malformed.append("size '%s' malformed for '%s'" % (size,
                                                                       fname))
                    continue

            date = tmp[date_idx]
            if not date_pat.search(date):
                malformed.append("date '%s' malformed for '%s'" % (date,
                                                                   fname))
                continue

            time = tmp[time_idx]
            if not time_pat.search(time):
                malformed.append("time '%s' malformed for '%s'" % (time,
                                                                   fname))
                continue

        if count < 4:
            t = 'error'
            n = self._get_check_name('squashfs_files_malformed output')
            s = "unsquashfs -lls ouput too short"
            self._add_result(t, n, s)

        if len(malformed) > 0:
            t = 'error'
            n = self._get_check_name('squashfs_files_malformed_line')
            s = "malformed lines in unsquashfs output: '%s'" % ", ".join(malformed)
            self._add_result(t, n, s)

        t = 'info'
        n = self._get_check_name('squashfs_files')
        s = 'OK'
        if len(errors) > 0:
            t = 'error'
            s = "found errors in file output: %s" % ", ".join(errors)
        self._add_result(t, n, s)

    def _allowed_iface_reference(self, side, interface):
        if side not in self.snap_yaml:
            return

        # no overrides to check
        if interface not in sec_iface_ref_overrides:
            return

        refname = None
        for ref in self.snap_yaml[side]:
            if ref == interface:
                refname = ref
            elif 'interface' in self.snap_yaml[side][ref] and \
                    self.snap_yaml[side][ref]['interface'] == interface:
                refname = ref
            if refname is None:
                continue  # nothing to check

            t = 'info'
            n = self._get_check_name('interface-reference', app=refname,
                                     extra=interface)
            s = 'OK'
            if self.snap_yaml['name'] not in sec_iface_ref_overrides[interface]:
                t = 'warn'
                s = "override not found for '%s/%s'. " % (side, refname) + \
                    "Use of the %s interface is reserved for " % interface + \
                    "vetted publishers. If your snap legitimately " + \
                    "requires this access, please make a request in " + \
                    "the forum using the 'store-requests' category (" + \
                    "https://forum.snapcraft.io/c/store-requests), or if " + \
                    "you would prefer to keep this private, the 'sensitive' " + \
                    "category."
                self._add_result(t, n, s)
            elif refname not in \
                    sec_iface_ref_overrides[interface][self.snap_yaml['name']]:
                t = 'error'
                s = "interface reference '%s' not allowed. " % refname + \
                    "Please use one of: %s" % ", ".join(
                        sec_iface_ref_overrides[interface][self.snap_yaml['name']])
            self._add_result(t, n, s)

    def check_personal_files_iface_reference(self):
        '''Check personal-files interface references'''
        self._allowed_iface_reference('plugs', 'personal-files')

    def check_system_files_iface_reference(self):
        '''Check system-files interface references'''
        self._allowed_iface_reference('plugs', 'system-files')
