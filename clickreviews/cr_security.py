'''cr_security.py: click security checks'''
#
# Copyright (C) 2013-2016 Canonical Ltd.
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

from clickreviews.common import (
    AA_PROFILE_NAME_MAXLEN,
    AA_PROFILE_NAME_ADVLEN,
)
from clickreviews.cr_common import ClickReview, error, open_file_read
import clickreviews.cr_common as cr_common
import clickreviews.apparmor_policy as apparmor_policy
import copy
import json
import os


class ClickReviewSecurity(ClickReview):
    '''This class represents click lint reviews'''
    def __init__(self, fn, overrides=None):
        peer_hooks = dict()
        my_hook = 'apparmor'
        peer_hooks[my_hook] = dict()
        # Basically, everything except frameworks
        peer_hooks[my_hook]['allowed'] = ClickReview.app_allowed_peer_hooks + \
            ClickReview.scope_allowed_peer_hooks + \
            ClickReview.service_allowed_peer_hooks + \
            ['pay-ui']
        peer_hooks[my_hook]['required'] = []

        my_hook2 = 'apparmor-profile'
        peer_hooks[my_hook2] = dict()
        # Basically, everything except frameworks
        peer_hooks[my_hook2]['allowed'] = \
            ClickReview.service_allowed_peer_hooks
        peer_hooks[my_hook2]['required'] = []

        ClickReview.__init__(self, fn, "security", peer_hooks=peer_hooks,
                             overrides=overrides)

        if not self.is_click and not self.is_snap1:
            return

        local_copy = None
        if 'SNAP' in os.environ:
            snap_fn = os.path.join(os.environ['SNAP'],
                                   'data/apparmor-easyprof-ubuntu.json')
            if os.path.exists(snap_fn):
                local_copy = snap_fn

        # If local_copy is None, then this will check the server to see if
        # we are up to date. However, if we are working within the development
        # tree, use it unconditionally.
        branch_fn = os.path.join(os.path.dirname(__file__),
                                 '../data/apparmor-easyprof-ubuntu.json')
        if local_copy is None and os.path.exists(branch_fn):
            local_copy = branch_fn

        p = apparmor_policy.ApparmorPolicy(local_copy)
        self.aa_policy = p.policy

        self.all_fields = ['abstractions',
                           'author',
                           'binary',
                           'comment',
                           'copyright',
                           'name',
                           'policy_groups',
                           'policy_vendor',
                           'policy_version',
                           'read_path',
                           'template',
                           'template_variables',
                           'write_path']
        self.ignored_fields = ['author',
                               'comment',
                               'copyright',
                               'name']
        self.required_fields = ['policy_version']
        self.redflag_fields = ['abstractions',
                               'binary',
                               'read_path',
                               'template_variables',
                               'write_path']
        self.allowed_webapp_policy_groups = ['accounts',
                                             'audio',
                                             'camera',
                                             'connectivity',
                                             'content_exchange',
                                             'content_exchange_source',
                                             'keep-display-on',
                                             'location',
                                             'microphone',
                                             'networking',
                                             'video',
                                             'webview']

        self.allowed_push_helper_policy_groups = ['push-notification-client']
        self.allowed_network_scope_policy_groups = ['accounts', 'networking']
        self.required_ubuntu_account_plugin_policy_groups = ['accounts',
                                                             'networking']
        self.allowed_ubuntu_account_plugin_policy_groups = \
            self.required_ubuntu_account_plugin_policy_groups + \
            ['audio', 'webview']

        self.redflag_templates = ['unconfined']
        # TODO: how to deal with other vendors
        self.extraneous_ubuntu_templates = ['ubuntu-sdk',
                                            'default']

        # framework policy is based on major framework version. In 13.10, there
        # was only 'ubuntu-sdk-13.10', but in 14.04, there will be several,
        # like 'ubuntu-sdk-14.04-html5', 'ubuntu-sdk-14.04-platform', etc
        # TODO: in 15.10 we will be using the policy version will match the
        # release framework, so we can simplify these checks
        self.major_framework_policy = {
            'ubuntu-sdk-13.10': {
                'policy_version': 1.0,
            },
            'ubuntu-sdk-14.04': {
                'policy_version': 1.1,
            },
            'ubuntu-sdk-14.10': {
                'policy_version': 1.2,
            },
            'ubuntu-sdk-15.04': {
                'policy_version': 1.3,
            },
            'ubuntu-core-15.04': {
                'policy_vendor': 'ubuntu-core',
                'policy_version': 15.04,
            },
        }
        framework_overrides = self.overrides.get('framework', {})
        self._override_framework_policies(framework_overrides)

        # snappy
        self.sec_skipped_types = ['oem',
                                  'os',
                                  'kernel']  # these don't need security items

        self.security_manifests = dict()
        self.security_apps = []
        self.security_profiles = dict()
        self.security_apps_profiles = []

        if self.manifest is None and self.is_snap1:
            for exe_t in ['services', 'binaries']:
                if exe_t not in self.pkg_yaml:
                    continue
                for item in self.pkg_yaml[exe_t]:
                    if 'name' not in item:
                        continue
                    app = "%s/%s" % (exe_t, item['name'])

                    if 'security-policy' in item:
                        if 'apparmor' not in item['security-policy']:
                            continue
                        rel_fn = item['security-policy']['apparmor']
                        self.security_profiles[rel_fn] = \
                            self._extract_security_profile(app)
                        self.security_apps_profiles.append(app)
                        continue

                    # Fake a security manifest for code reuse
                    # FIXME: this needs to be updated when we have 'target'
                    m = dict()
                    m['policy_vendor'] = "ubuntu-core"
                    m['policy_version'] = self._pkgfmt_version()
                    if 'security-template' in item:
                        m['template'] = item['security-template']
                    else:
                        m['template'] = 'default'

                    if 'caps' in item:
                        m['policy_groups'] = item['caps']
                    elif self._pkgfmt_version() == "15.04":
                        m['policy_groups'] = ['networking']
                    else:
                        m['policy_groups'] = ['network-client']

                    self.security_manifests[app] = m
                    self.security_apps.append(app)
        else:
            self.security_manifests = dict()
            self.security_apps = []
            for app in self.manifest['hooks']:
                if 'apparmor' not in self.manifest['hooks'][app]:
                    #  msg("Skipped missing apparmor hook for '%s'" % app)
                    continue
                if not isinstance(self.manifest['hooks'][app]['apparmor'], str):
                    error("manifest malformed: hooks/%s/apparmor is not str" % app)
                rel_fn = self.manifest['hooks'][app]['apparmor']
                self.security_manifests[rel_fn] = \
                    self._extract_security_manifest(app)
                self.security_apps.append(app)

            for app in self.manifest['hooks']:
                if 'apparmor-profile' not in self.manifest['hooks'][app]:
                    #  msg("Skipped missing apparmor hook for '%s'" % app)
                    continue
                if not isinstance(self.manifest['hooks'][app]['apparmor-profile'],
                                  str):
                    error("manifest malformed: hooks/%s/apparmor-profile is not "
                          "str" % app)
                rel_fn = self.manifest['hooks'][app]['apparmor-profile']
                self.security_profiles[rel_fn] = \
                    self._extract_security_profile(app)
                self.security_apps_profiles.append(app)

    def _override_framework_policies(self, overrides):
        # override major framework policies
        self.major_framework_policy.update(overrides)

        # override apparmor policies
        for name, data in overrides.items():
            vendor = data.get('policy_vendor')
            version = str(data.get('policy_version'))

            if vendor not in self.aa_policy:
                self.aa_policy[vendor] = {}

            if version not in self.aa_policy[vendor]:
                # just ensure the version is defined
                # TODO: add support to override templates and policy groups
                self.aa_policy[vendor][version] = {}

    def _extract_security_manifest(self, app):
        '''Extract security manifest and verify it has the expected
           structure'''
        d = self.manifest['hooks'][app]['apparmor']
        fn = os.path.join(self.unpack_dir, d)
        rel_fn = self.manifest['hooks'][app]['apparmor']

        try:
            m = json.load(cr_common.open_file_read(fn))
        except Exception:
            error("Could not load '%s'. Is it properly formatted?" % rel_fn)
        mp = json.dumps(m, sort_keys=True, indent=2, separators=(',', ': '))
        if not isinstance(m, dict):
            error("'%s' malformed:\n%s" % (rel_fn, mp))
        for k in sorted(m):
            if k not in self.all_fields:
                error("'%s' malformed: unsupported field '%s':\n%s" % (rel_fn,
                                                                       k, mp))
            if k in ['abstractions', 'policy_groups', 'read_path',
                     'write_path']:
                if not isinstance(m[k], list):
                    error("'%s' malformed: '%s' is not list:\n%s" % (rel_fn,
                                                                     k, mp))
            elif k == 'template_variables':
                if not isinstance(m[k], dict):
                    error("'%s' malformed: '%s' is not dict:\n%s" % (rel_fn,
                                                                     k, mp))
            elif k == "policy_version":
                # python and Qt don't agree on the JSON output of floats that
                # are integers (ie, 1.0 vs 1). LP: #1214618
                if not isinstance(m[k], float) and not isinstance(m[k], int):
                    error("'%s' malformed: '%s' is not a JSON number:\n%s" %
                          (rel_fn, k, mp))
                if isinstance(m[k], int):
                    m[k] = float(m[k])
            else:
                if not isinstance(m[k], str):
                    error("'%s' malformed: '%s' is not str:\n%s" % (rel_fn,
                                                                    k, mp))
        return m

    def _get_security_manifest(self, app):
        '''Get the security manifest for app'''
        if app not in self.manifest['hooks']:
            error("Could not find '%s' in click manifest" % app)
        elif 'apparmor' not in self.manifest['hooks'][app]:
            error("Could not find apparmor hook for '%s' in click manifest" %
                  app)
        f = self.manifest['hooks'][app]['apparmor']
        m = self.security_manifests[f]

        return (f, m)

    def _extract_security_profile(self, app):
        '''Extract security profile'''
        rel_fn = self.manifest['hooks'][app]['apparmor-profile']

        fn = os.path.join(self.unpack_dir, rel_fn)
        if not os.path.exists(fn):
            error("Could not find '%s'" % rel_fn)

        fh = open_file_read(fn)
        contents = ""
        for line in fh.readlines():
            contents += line
        fh.close()

        # We could try to run this through apparmor_parser, but that is going
        # to be system dependent (eg, a profile may reference features on a
        # new parser and fail here on the local parser)

        return contents

    def _get_security_profile(self, app):
        '''Get the security profile for app'''
        if app not in self.manifest['hooks']:
            error("Could not find '%s' in click manifest" % app)
        elif 'apparmor-profile' not in self.manifest['hooks'][app]:
            error("Could not find apparmor-profile hook for '%s' in click "
                  "manifest" % app)
        f = self.manifest['hooks'][app]['apparmor-profile']

        p = self.security_profiles[f]
        return (f, p)

    def _get_highest_policy_version(self, vendor):
        '''Determine highest policy version for the vendor'''
        if vendor not in self.aa_policy:
            error("Could not find vendor '%s'" % vendor, do_exit=False)
            return None

        return float(sorted(self.aa_policy[vendor].keys())[-1])

    def check_policy_vendor(self):
        '''Check policy_vendor'''
        if not self.is_click and not self.is_snap1:
            return

        for app in sorted(self.security_apps):
            (f, m) = self._get_security_manifest(app)
            t = 'info'
            n = self._get_check_name('policy_vendor', extra=f)
            s = "OK"
            if 'policy_vendor' in m and \
               m['policy_vendor'] not in self.aa_policy:
                t = 'error'
                s = "policy_vendor '%s' not found" % m['policy_vendor']
            self._add_result(t, n, s)

            t = 'info'
            n = self._get_check_name('policy_vendor_matches_framework', extra=f)
            s = "OK"
            if 'policy_vendor' in m:  # policy_vendor is optional
                found_major = False
                for name, data in self.major_framework_policy.items():
                    framework = self.manifest['framework']
                    # snappy compat manifest supports comma-separated list
                    # for framework
                    if self.is_snap1 and ',' in framework:
                        # For now, we know the release framework is appended.
                        # TODO: fix for multiple frameworks
                        framework = framework.split(',')[-1]
                    if not framework.startswith(name):
                        continue
                    elif 'policy_vendor' not in data:
                        # when not specified, default to 'ubuntu'
                        data['policy_vendor'] = "ubuntu"
                    found_major = True
                    if m['policy_vendor'] != data['policy_vendor']:
                        t = 'error'
                        s = '%s != %s (%s)' % (str(m['policy_vendor']),
                                               data['policy_vendor'],
                                               framework)
                if not found_major:
                    t = 'error'
                    s = "Invalid framework '%s'" % framework
            self._add_result(t, n, s)

    def check_policy_version(self):
        '''Check policy version'''
        if not self.is_click and not self.is_snap1:
            return

        for app in sorted(self.security_apps):
            (f, m) = self._get_security_manifest(app)

            n = self._get_check_name('policy_version_exists', extra=f)
            if 'policy_version' not in m:
                self._add_result('error', n,
                                 'could not find policy_version in manifest')
                continue

            t = 'info'
            s = "OK"
            vendor = "ubuntu"
            if 'policy_vendor' in m:
                vendor = m['policy_vendor']
            version = str(m['policy_version'])
            if vendor not in self.aa_policy or \
               not self._has_policy_version(vendor, version):
                t = 'error'
                s = 'could not find policy for %s/%s' % (vendor, version)
            self._add_result(t, n, s)

            highest = self._get_highest_policy_version(vendor)
            t = 'info'
            n = self._get_check_name(
                'policy_version_is_highest',
                extra='(%s, %s)' % (str(highest), f))
            s = "OK"
            link = None
            if float(m['policy_version']) != highest:
                t = 'info'
                link = 'http://askubuntu.com/q/562116/94326'
                s = '%s != %s' % (str(m['policy_version']), str(highest))
            self._add_result(t, n, s, link)

            t = 'info'
            n = self._get_check_name('policy_version_matches_framework', extra=f)
            s = "OK"
            found_major = False
            for name, data in self.major_framework_policy.items():
                framework = self.manifest['framework']
                # snappy compat manifest supports comma-separated list
                # for framework
                if self.is_snap1 and ',' in framework:
                    # For now, we know the release framework is appended.
                    # TODO: fix for multiple frameworks
                    framework = framework.split(',')[-1]
                if not framework.startswith(name):
                    continue
                found_major = True
                if m['policy_version'] != data['policy_version']:
                    t = 'error'
                    link = 'http://askubuntu.com/q/686347'
                    s = '%s != %s (%s)' % (str(m['policy_version']),
                                           data['policy_version'],
                                           framework)
            if not found_major:
                t = 'error'
                s = "Invalid framework '%s'" % framework
            self._add_result(t, n, s, link)

    def check_template(self):
        '''Check template'''
        if not self.is_click and not self.is_snap1:
            return

        for app in sorted(self.security_apps):
            (f, m) = self._get_security_manifest(app)

            t = 'info'
            n = self._get_check_name('template_with_policy_version', extra=f)
            s = "OK"
            if 'policy_version' not in m:
                self._add_result('error', n,
                                 'could not find policy_version in manifest')
                continue
            self._add_result(t, n, s)

            t = 'info'
            n = self._get_check_name('template_valid', extra=f)
            s = "OK"
            link = 'http://askubuntu.com/q/671403'
            manual_review = False
            if 'template' not in m:
                # If template not specified, we just use the default
                self._add_result(t, n, 'OK (none specified)')
                continue
            elif m['template'] in self.redflag_templates:
                t = 'error'
                s = "(NEEDS REVIEW) '%s' not allowed" % m['template']
                manual_review = True
            elif ('policy_vendor' not in m or m['policy_vendor'] == 'ubuntu') \
                    and m['template'] in self.extraneous_ubuntu_templates:
                t = 'warn'
                s = "No need to specify '%s' template" % m['template']
            self._add_result(t, n, s, link, manual_review=manual_review)

            t = 'info'
            n = self._get_check_name('template_exists', extra=f)
            s = "OK"
            vendor = "ubuntu"
            if 'policy_vendor' in m:
                vendor = m['policy_vendor']
            version = str(m['policy_version'])

            templates = self._get_templates(vendor, version)
            if len(templates) < 1:
                t = 'error'
                s = 'could not find templates'
                self._add_result(t, n, s)
                continue
            self._add_result(t, n, s)

            found = False
            if m['template'] in self._get_templates(vendor, version):
                found = True
            elif self.is_snap1:
                frameworks = []
                if 'framework' in self.pkg_yaml:
                    frameworks = [x.strip() for x in
                                  self.pkg_yaml['framework'].split(',')]
                elif 'frameworks' in self.pkg_yaml:
                    frameworks = self.pkg_yaml['frameworks']
                elif 'type' in self.pkg_yaml and \
                     self.pkg_yaml['type'] == 'framework':
                    # frameworks may reference their own policy groups
                    frameworks.append(self.pkg_yaml['name'])

                for f in frameworks:
                    if m['template'].startswith("%s_" % f):
                        found = True
                        break

            if not found:
                t = 'error'
                s = "specified unsupported template '%s'" % m['template']

            self._add_result(t, n, s)

    def check_policy_groups_webapps(self):
        '''Check policy_groups for webapps'''
        if not self.is_click and not self.is_snap1:
            return

        for app in sorted(self.security_apps):
            (f, m) = self._get_security_manifest(app)
            t = 'info'
            n = self._get_check_name('policy_groups_webapp', extra=f)
            s = "OK"
            webapp_template = "ubuntu-webapp"
            if 'template' not in m or m['template'] != webapp_template:
                # self._add_result(t, n, s)
                continue
            if 'policy_groups' not in m or \
               'networking' not in m['policy_groups']:
                self._add_result('error', n,
                                 "required group 'networking' not found")
                continue
            bad = []
            for p in m['policy_groups']:
                if p not in self.allowed_webapp_policy_groups:
                    bad.append(p)
            if len(bad) > 0:
                t = 'error'
                s = "found unusual policy groups: %s" % ", ".join(bad)
            self._add_result(t, n, s)

            t = 'info'
            n = self._get_check_name('policy_groups_webapp_webview', extra=f)
            s = "OK"
            if self.manifest['framework'] == "ubuntu-sdk-13.10":
                s = "SKIPPED (webview not available in 13.10)"
            elif 'webview' not in m['policy_groups']:
                t = 'warn'
                s = "'webview' not specified. Webapp may not function"

            self._add_result(t, n, s)

    def check_policy_groups_push_helpers(self):
        '''Check policy groups for push-helpers'''
        if not self.is_click and not self.is_snap1:
            return

        for app in sorted(self.security_apps):
            (f, m) = self._get_security_manifest(app)
            t = 'info'
            n = self._get_check_name('policy_groups_push_helper', extra=f)
            s = "OK"

            if 'template' not in m or m['template'] != 'ubuntu-push-helper':
                continue

            if 'policy_groups' not in m or \
               'push-notification-client' not in m['policy_groups']:
                self._add_result('error', n,
                                 "required group 'push-notification-client' "
                                 "not found")
                continue
            bad = []
            for p in m['policy_groups']:
                if p not in self.allowed_push_helper_policy_groups:
                    bad.append(p)
                elif p == "networking" or p == "network-client":
                    # The above covers this, but let's be very explicit and
                    # never allow networking with push-helpers
                    bad.append(p)
            if len(bad) > 0:
                t = 'error'
                s = "found unusual policy groups: %s" % ", ".join(bad)
            self._add_result(t, n, s)

    def check_policy_groups_scopes(self):
        '''Check policy_groups for scopes'''
        if not self.is_click and not self.is_snap1:
            return

        for app in sorted(self.security_apps):
            (f, m) = self._get_security_manifest(app)
            t = 'info'
            n = self._get_check_name('policy_groups_scopes', extra=f)
            s = "OK"
# jdstrand, 2014-06-05: ubuntu-scope-local-content is no longer available
#            scope_templates = ['ubuntu-scope-network',
#                               'ubuntu-scope-local-content']
            scope_templates = ['ubuntu-scope-network']
            if 'template' not in m or m['template'] not in scope_templates:
                continue

            if 'policy_groups' not in m:
                continue

            bad = []
            for p in m['policy_groups']:
                if m['template'] == 'ubuntu-scope-network':
                    # networking scopes should have extremely limited access
                    if p not in self.allowed_network_scope_policy_groups:
                        bad.append(p)
# jdstrand, 2014-06-05: ubuntu-scope-local-content is no longer available
#                elif m['template'] == 'ubuntu-scope-local-content':
#                    if p == 'networking':
#                        bad.append(p)

            if len(bad) > 0:
                t = 'error'
                s = "found inappropriate policy groups: %s" % ", ".join(bad)
            self._add_result(t, n, s)

    def check_policy_groups_ubuntu_account_plugin(self):
        '''Check policy_groups for ubuntu-account-plugin template'''
        if not self.is_click and not self.is_snap1:
            return

        for app in sorted(self.security_apps):
            (f, m) = self._get_security_manifest(app)

            if 'template' not in m or m['template'] != 'ubuntu-account-plugin':
                continue

            t = 'info'
            n = self._get_check_name(
                'required_policy_groups_ubuntu_account_plugin', extra=f)
            s = "OK"
            if 'policy_groups' not in m:
                self._add_result('error', n,
                                 "required policy groups not found")
                continue

            missing = []
            for p in self.required_ubuntu_account_plugin_policy_groups:
                if p not in m['policy_groups']:
                    missing.append(p)
            if len(missing) > 0:
                t = 'error'
                s = "missing required policy groups: %s" % ", ".join(missing)
            self._add_result(t, n, s)

            t = 'info'
            n = self._get_check_name(
                'policy_groups_ubuntu_account_plugin', extra=f)
            s = "OK"
            bad = []
            for p in m['policy_groups']:
                if p not in self.allowed_ubuntu_account_plugin_policy_groups:
                    bad.append(p)
            if len(bad) > 0:
                t = 'error'
                s = "found unusual policy groups: %s" % ", ".join(bad)
            self._add_result(t, n, s)

    def check_policy_groups(self):
        '''Check policy_groups'''
        if not self.is_click and not self.is_snap1:
            return

        for app in sorted(self.security_apps):
            (f, m) = self._get_security_manifest(app)

            t = 'info'
            n = self._get_check_name('policy_groups_exists', app=app, extra=f)
            if 'policy_groups' not in m:
                # If template not specified, we just use the default
                self._add_result('info', n, 'no policy groups specified')
                continue
            elif 'policy_version' not in m:
                self._add_result('error', n,
                                 'could not find policy_version in manifest')
                continue

            s = "OK"
            vendor = "ubuntu"
            if 'policy_vendor' in m:
                vendor = m['policy_vendor']
            version = str(m['policy_version'])

            policy_groups = self._get_policy_groups(version=version, vendor=vendor)
            if len(policy_groups) < 1:
                t = 'error'
                s = 'could not find policy groups'
                self._add_result(t, n, s)
                continue
            self._add_result(t, n, s)

            # Check for duplicates
            t = 'info'
            n = self._get_check_name('policy_groups_duplicates', app=app, extra=f)
            s = 'OK'
            tmp = []
            for p in m['policy_groups']:
                if m['policy_groups'].count(p) > 1 and p not in tmp:
                    tmp.append(p)
                if len(tmp) > 0:
                    tmp.sort()
                    t = 'error'
                    s = 'duplicate policy groups found: %s' % ", ".join(tmp)
            self._add_result(t, n, s)

            frameworks = []
            if self.is_snap1:
                if 'framework' in self.pkg_yaml:
                    frameworks = [x.strip() for x in
                                  self.pkg_yaml['framework'].split(',')]
                elif 'frameworks' in self.pkg_yaml:
                    frameworks = self.pkg_yaml['frameworks']
                elif 'type' in self.pkg_yaml and \
                     self.pkg_yaml['type'] == 'framework':
                    # frameworks may reference their own policy groups
                    frameworks.append(self.pkg_yaml['name'])

            # If we got here, we can see if valid policy groups were specified
            for i in m['policy_groups']:
                t = 'info'
                n = self._get_check_name('policy_groups_valid', app=app, extra=i)
                s = 'OK'

                # SDK will leave and empty policy group, report but don't
                # deny
                if i == "":
                    t = 'error'
                    s = 'found empty policy group'
                    self._add_result(t, n, s)
                    continue

                found = False
                framework_found = False
                for j in policy_groups:
                    if i == os.path.basename(j):
                        found = True
                        break
                    else:
                        for f in frameworks:
                            if i.startswith("%s_" % f):
                                framework_found = True
                                break
                        if framework_found:
                            found = True
                            break

                if not found:
                    t = 'error'
                    s = "unsupported policy_group '%s'" % i
                self._add_result(t, n, s)

                if found:
                    t = 'info'
                    n = self._get_check_name(
                        'policy_groups_safe', app=app, extra=i)
                    s = 'OK'
                    link = None
                    manual_review = False

                    if framework_found:
                        aa_type = 'framework'
                    else:
                        aa_type = self._get_policy_group_type(vendor, version,
                                                              i)
                    if i == "debug":
                        # IMPORTANT: do not change this string without
                        # coordination from the SDK team (LP: #1415487)
                        t = 'error'
                        s = "(REJECT) %s policy group " % aa_type + \
                            "'%s': not for production use" % (i)
                    elif aa_type == "reserved":
                        t = 'error'
                        s = "(NEEDS REVIEW) %s policy group " % aa_type + \
                            "'%s': vetted applications only" % (i)
                        if i == "debug":
                            link = 'http://askubuntu.com/a/562123/94326'
                        manual_review = True
                    elif aa_type == 'framework':
                        s = "OK (matches '%s' framework)" % i.split('_')[0]
                    elif aa_type != "common":
                        t = 'error'
                        s = "policy group '%s' has " % i + \
                            "unknown type '%s'" % (aa_type)
                    self._add_result(t, n, s, link, manual_review=manual_review)

    def check_ignored(self):
        '''Check ignored fields'''
        if not self.is_click and not self.is_snap1:
            return

        for app in sorted(self.security_apps):
            (f, m) = self._get_security_manifest(app)

            t = 'info'
            n = self._get_check_name('ignored_fields', extra=f)
            s = "OK"
            found = []
            for i in self.ignored_fields:
                if i in m:
                    found.append(i)

            if len(found) > 0:
                t = 'warn'
                s = "found ignored fields: %s" % ", ".join(found)
            self._add_result(t, n, s)

    def check_redflag(self):
        '''Check redflag fields'''
        if not self.is_click and not self.is_snap1:
            return

        for app in sorted(self.security_apps):
            (f, m) = self._get_security_manifest(app)

            t = 'info'
            n = self._get_check_name('redflag_fields', extra=f)
            s = "OK"
            found = []
            for i in self.redflag_fields:
                if i in m:
                    if i == 'policy_vendor' and \
                       m[i] in ['ubuntu', 'ubuntu-snappy']:
                        continue
                    found.append(i)

            if len(found) > 0:
                t = 'error'
                s = "found redflagged fields (needs human review): %s" % \
                    ", ".join(found)
            self._add_result(t, n, s)

    def check_required(self):
        '''Check required fields'''
        if not self.is_click and not self.is_snap1:
            return

        for app in sorted(self.security_apps):
            (f, m) = self._get_security_manifest(app)

            t = 'info'
            n = self._get_check_name('required_fields', extra=f)
            s = "OK"
            not_found = []
            for i in self.required_fields:
                if i not in m:
                    not_found.append(i)

            if len(not_found) > 0:
                t = 'error'
                s = "missing required fields: %s" % ", ".join(not_found)
            self._add_result(t, n, s)

    def check_apparmor_profile(self):
        '''Check apparmor-profile'''
        if not self.is_click and not self.is_snap1:
            return

        for app in sorted(self.security_apps_profiles):
            (f, p) = self._get_security_profile(app)

            searches = ['###VAR###',
                        '###PROFILEATTACH###',
                        '@{CLICK_DIR}',
                        '@{APP_PKGNAME}',
                        '@{APP_VERSION}',
                        ]

            for v in searches:
                t = 'info'
                n = self._get_check_name(
                    'apparmor_profile', extra='%s (%s)' % (v, f))
                s = "OK"
                if v not in p:
                    if v.startswith('@') and \
                            ("# Unrestricted AppArmor policy" in p or
                             "# This profile offers no protection" in p):
                        self._add_result('info', n,
                                         "SKIPPED for '%s' (boilerplate)" % v)
                    else:
                        self._add_result('warn', n,
                                         "could not find '%s' in profile" % v)
                    continue
                self._add_result(t, n, s)

    # This will be really nice to get rid of when the click compat manifest
    # is gone
    def _compare_security_yamls(self, yaml, click_m):
        '''Compare two security yamls'''
        def find_match(name, key, value, my_dict):
            if 'name' in my_dict and my_dict['name'] == name and \
               key in my_dict and my_dict[key] == value:
                return True
            return False

        for first in [yaml, click_m]:
            if first == yaml:
                second = click_m
                second_m = "click-manifest"
                first_m = "package.yaml"
            else:
                second = yaml
                first_m = "click-manifest"
                second_m = "package.yaml"

            for exe_t in ['binaries', 'services']:
                t = 'info'
                n = self._get_check_name('yaml_%s' % exe_t)
                s = 'OK'
                if exe_t in first and exe_t not in second:
                    t = 'error'
                    s = "%s missing '%s'" % (second_m, exe_t)
                elif exe_t not in first and exe_t in second:
                    t = 'error'
                    s = "%s has extra '%s'" % (second_m, exe_t)
                self._add_result(t, n, s)

                if t == 'error':
                    continue
                elif exe_t not in first and exe_t not in second:
                    continue

                t = 'info'
                n = self._get_check_name('yaml_%s_entries' % exe_t)
                s = 'OK'
                if len(first[exe_t]) < len(second[exe_t]):
                    t = 'error'
                    s = "%s has extra '%s' entries" % (second_m, exe_t)
                self._add_result(t, n, s)

                for fapp in first[exe_t]:
                    t = 'info'
                    n = self._get_check_name(
                        'yaml_%s' % exe_t, app=fapp['name'])
                    s = 'OK'
                    sapp = None
                    for tmp in second[exe_t]:
                        if tmp['name'] == fapp['name']:
                            sapp = tmp
                    if sapp is None:
                        t = 'error'
                        s = "%s missing '%s'" % (second_m, fapp['name'])
                        self._add_result(t, n, s)
                        continue
                    elif first == yaml and "security-override" in fapp or \
                            second == yaml and "security-override" in sapp:
                        # no reason to check security-override since apparmor
                        # hook entry will point to this file
                        continue
                    elif first == yaml and "security-policy" in fapp or \
                            second == yaml and "security-policy" in sapp:
                        # no reason to check security-policy since apparmor
                        # profile hook is used instead
                        continue
                    elif 'caps' not in fapp and 'caps' not in sapp and \
                            second == yaml and 'security-template' not in sapp:
                        # no caps in yaml, policy_groups is empty in click
                        # manifest, unless security-template is in yaml
                        t = 'error'
                        s = "'policy_groups' not found in click manifest " + \
                            "(should default to ['network-client'])"
                        self._add_result(t, n, s)
                        continue
                    self._add_result(t, n, s)

                    for key in ['security-template', 'caps']:
                        t = 'info'
                        n = self._get_check_name(
                            'yaml_%s' % exe_t, extra=second_m)
                        s = 'OK'

                        if key not in fapp:
                            continue

                        if key == 'caps':
                            fapp['caps'] = set(fapp['caps'])
                            if 'caps' in sapp:
                                sapp['caps'] = set(sapp['caps'])

                        if not find_match(fapp['name'], key, fapp[key], sapp):
                            # handle snappy defaults for security-template
                            # and caps
                            if key == 'security-template' and \
                               second == yaml and key not in sapp and \
                               key in fapp and fapp[key] == 'default':
                                # if yaml missing security-template, click may
                                # specify 'default'
                                self._add_result(t, n, s)
                                continue
                            elif key == 'caps' and second == yaml and \
                                    'security-template' in sapp and \
                                    key not in sapp and \
                                    (key not in fapp or key in fapp and
                                     fapp[key] == set([])):
                                # when security-template is specified, then
                                # caps won't default to 'networking' when
                                # missing, so click manifest can omit or be []
                                self._add_result(t, n, s)
                                continue
                            elif key == 'caps' and second == yaml and \
                                    'security-template' not in sapp and \
                                    key not in sapp and key in fapp and \
                                    (fapp[key] == set(['networking']) or
                                     fapp[key] == set(['network-client'])):
                                # no caps in yaml, policy_groups is networking
                                # in click manifest when security-template not
                                # specified in yaml
                                self._add_result(t, n, s)
                                continue
                            elif key == 'caps' and second == click_m and \
                                    key not in sapp and key in fapp and \
                                    fapp[key] == set([]):
                                # no caps in click manifest, caps is [] in yaml
                                self._add_result(t, n, s)
                                continue
                            t = 'error'
                            s = "%s has different '%s' for '%s'" % \
                                (second_m, key, fapp['name']) + \
                                " - '%s:%s' vs '%s:%s'" % (first_m, fapp,
                                                           second_m, sapp)
                        self._add_result(t, n, s)

    def _convert_click_security_to_yaml(self):
        '''Convert click manifest to yaml'''
        converted = dict()

        # The click compat manifest does not have a 1 to 1 mapping to
        # package.yaml (ie, can't differentiate between services and
        # binaries) so look the appname up in the package.yaml to know
        # if it is a service or binary
        yaml_services = []
        if 'services' in self.pkg_yaml:
            yaml_services = [e['name'] for e in self.pkg_yaml['services']
                             if 'name' in e]
        yaml_binaries = []
        if 'binaries' in self.pkg_yaml:
            for e in self.pkg_yaml['binaries']:
                if 'exec' in e:
                    yaml_binaries.append(e['name'])
                else:
                    yaml_binaries.append(e['name'].split('/')[-1])

        for app in sorted(self.security_apps):
            if app == 'snappy-config':
                # the apparmor policy for snappy-config is autogenerated and
                # not represented in the yaml
                continue

            if app in yaml_services:
                key = 'services'
            elif app in yaml_binaries:
                key = 'binaries'
            else:
                t = 'error'
                n = self._get_check_name('yaml_and_click', app=app)
                s = "'%s' in click manifest missing from package.yaml" % app
                self._add_result(t, n, s)
                continue

            if key not in converted:
                converted[key] = []
            tmp = dict()
            tmp['name'] = app

            (f, m) = self._get_security_manifest(app)
            if 'template' in m:
                tmp['security-template'] = m['template']

            if 'policy_groups' in m:
                tmp['caps'] = m['policy_groups']

            converted[key].append(copy.deepcopy(tmp))

        for app in sorted(self.security_apps_profiles):
            if app in yaml_services:
                key = 'services'
            elif app in yaml_binaries:
                key = 'binaries'
            else:
                t = 'error'
                n = self._get_check_name('yaml_and_click', app=app)
                s = "'%s' in click manifest missing from package.yaml" % app
                self._add_result(t, n, s)
                continue

            if key not in converted:
                converted[key] = []
            tmp = dict()
            tmp['name'] = app

            (f, p) = self._get_security_profile(app)
            tmp['security-policy'] = {'apparmor': f}

            converted[key].append(copy.deepcopy(tmp))

        return copy.deepcopy(converted)

    def check_security_yaml_and_click(self):
        '''Verify click and security yaml are in sync (not including
           override)
        '''
        if not self.is_click and not self.is_snap1:
            return

        if self.is_click or self.pkg_yaml['type'] in self.sec_skipped_types:
            return

        # setup a small dict that is a subset of self.pkg_yaml
        yml = dict()
        for exe_t in ['binaries', 'services']:
            if exe_t not in self.pkg_yaml:
                continue
            yml[exe_t] = copy.deepcopy(self.pkg_yaml[exe_t])
            for item in yml[exe_t]:
                # account for binaries doing different things with 'name/exec'
                if exe_t == 'binaries' and 'exec' not in item and \
                   '/' in item['name']:
                    item['name'] = os.path.basename(item['name'])

        converted = self._convert_click_security_to_yaml()

        # don't compare the security yaml and the click if the yaml isn't
        # formatted right. This avoids confusing errors for the user
        error = False
        for exe_t in yml.keys():
            for item in yml[exe_t]:
                if 'security-template' in item and \
                        not isinstance(item['security-template'], str):
                    error = True
                    continue
                elif 'caps' in item and not isinstance(item['caps'], list):
                    error = True
                    continue
        if error:
            t = 'info'
            n = self._get_check_name('yaml_and_click')
            s = "SKIPPED (yaml errors)"
            self._add_result(t, n, s)
            return

        self._compare_security_yamls(yml, converted)

    def check_security_yaml_override_and_click(self):
        '''Verify click and security yaml override are in sync'''
        if not self.is_click and not self.is_snap1:
            return

        if self.is_click or self.pkg_yaml['type'] in self.sec_skipped_types:
            return

        for exe_t in ['services', 'binaries']:
            if exe_t not in self.pkg_yaml:
                continue

            for item in self.pkg_yaml[exe_t]:
                if 'name' not in item:
                    t = 'error'
                    n = self._get_check_name('yaml_override_click_name')
                    s = "package.yaml malformed. Could not find 'name' " + \
                        "for entry in '%s'" % item
                    self._add_result(t, n, s)
                    continue

                app = item['name']
                t = 'info'
                n = self._get_check_name('yaml_override_click', app=app)
                s = "OK"
                if 'security-override' not in item:
                    s = "OK (skipping unspecified override)"
                elif 'apparmor' not in item['security-override']:
                    t = 'error'
                    s = "'apparmor' not specified in 'security-override' " + \
                        "for '%s'" % app
                elif item['security-override']['apparmor'] not in \
                        self.security_manifests:
                    t = 'error'
                    s = "'%s' not found in click manifest for '%s'" % \
                        (item['security-override']['apparmor'], app)
                # NOTE: we skip 'seccomp' because there isn't currently a
                # click hook for it
                self._add_result(t, n, s)

    def check_security_yaml_override(self):
        '''Verify security yaml override'''
        if not self.is_click and not self.is_snap1:
            return

        if not self.is_snap1:
            return

        for exe_t in ['services', 'binaries']:
            if exe_t not in self.pkg_yaml:
                continue

            for item in self.pkg_yaml[exe_t]:
                if 'name' not in item:
                    t = 'error'
                    n = self._get_check_name('yaml_override_name')
                    s = "package.yaml malformed. Could not find 'name' " + \
                        "for entry in '%s'" % item
                    self._add_result(t, n, s)
                    continue

                app = item['name']
                t = 'info'
                n = self._get_check_name('yaml_override_format', app=app)
                s = "OK"
                if 'security-override' not in item:
                    s = "OK (skipping unspecified override)"
                else:
                    if 'apparmor' not in item['security-override']:
                        t = 'error'
                        s = "'apparmor' not specified in 'security-override' " + \
                            "for '%s'" % app
                    elif 'seccomp' not in item['security-override']:
                        t = 'error'
                        s = "'seccomp' not specified in 'security-override' " + \
                            "for '%s'" % app

                self._add_result(t, n, s)

    def check_security_yaml_policy(self):
        '''Verify security yaml policy'''
        if not self.is_click and not self.is_snap1:
            return

        if not self.is_snap1:
            return

        for exe_t in ['services', 'binaries']:
            if exe_t not in self.pkg_yaml:
                continue

            for item in self.pkg_yaml[exe_t]:
                if 'name' not in item:
                    t = 'error'
                    n = self._get_check_name('yaml_policy_name')
                    s = "package.yaml malformed. Could not find 'name' " + \
                        "for entry in '%s'" % item
                    self._add_result(t, n, s)
                    continue

                app = item['name']
                t = 'info'
                n = self._get_check_name('yaml_policy_format', app=app)
                s = "OK"
                if 'security-policy' not in item:
                    s = "OK (skipping unspecified policy)"
                elif 'apparmor' not in item['security-policy']:
                    t = 'error'
                    s = "'apparmor' not specified in 'security-policy' " + \
                        "for '%s'" % app
                elif 'seccomp' not in item['security-policy']:
                    t = 'error'
                    s = "'seccomp' not specified in 'security-policy' for " + \
                        "'%s'" % app
                self._add_result(t, n, s)

                if 'security-policy' in item:
                    t = 'error'
                    n = self._get_check_name('yaml_policy_present')
                    s = "(NEEDS REVIEW) 'security-policy' not allowed"
                    link = 'https://developer.ubuntu.com/en/snappy/guides/security-policy/'
                    m = True
                    self._add_result(t, n, s, link=link, manual_review=m)

    def check_security_yaml_combinations(self):
        '''Verify security yaml uses valid combinations'''
        if not self.is_click and not self.is_snap1:
            return

        if not self.is_snap1 or self.pkg_yaml['type'] in self.sec_skipped_types:
            return

        for exe_t in ['services', 'binaries']:
            if exe_t not in self.pkg_yaml:
                continue
            for item in self.pkg_yaml[exe_t]:
                if 'name' not in item:
                    t = 'error'
                    n = self._get_check_name('yaml_combinations_name')
                    s = "package.yaml malformed. Could not find 'name' " + \
                        "for entry in '%s'" % item
                    self._add_result(t, n, s)
                    continue

                app = item['name']

                t = 'info'
                n = self._get_check_name('yaml_combinations', app=app)
                s = "OK"
                if "security-policy" in item:
                    for i in ['security-override', 'security-template',
                              'caps']:
                        if i in item:
                            t = 'error'
                            s = "Found '%s' with 'security-policy'" % (i)
                            break
                elif "security-override" in item:
                    for i in ['security-policy', 'security-template', 'caps']:
                        if i in item:
                            t = 'error'
                            s = "Found '%s' with 'security-override'" % (i)
                            break
                self._add_result(t, n, s)

    def check_security_template(self):
        '''Check snap security-template'''
        if not self.is_click and not self.is_snap1:
            return

        if not self.is_snap1 or self.pkg_yaml['type'] in self.sec_skipped_types:
            return

        for exe_t in ['services', 'binaries']:
            if exe_t not in self.pkg_yaml:
                continue
            for item in self.pkg_yaml[exe_t]:
                if 'security-template' not in item:
                    tmpl = ""
                else:
                    tmpl = item['security-template']

                if 'name' not in item:
                    t = 'error'
                    n = self._get_check_name('yaml_security-template_name')
                    s = "package.yaml malformed. Could not find 'name' " + \
                        "for entry in '%s'" % item
                    self._add_result(t, n, s)
                    continue

                # Handle bin/exec concept with bianries
                app = os.path.basename(item['name'])

                t = 'info'
                n = self._get_check_name('yaml_security-template', app=app)
                s = "OK"
                if not isinstance(tmpl, str):
                    t = 'error'
                    s = "'%s/%s' malformed: '%s' is not str" % (exe_t, app,
                                                                tmpl)
                    self._add_result(t, n, s)
                    continue
                self._add_result(t, n, s)

                if self.is_snap1:
                    t = 'info'
                    n = self._get_check_name('yaml_security-template_in_manifest', app=app)
                    s = "OK"
                    if app not in self.manifest['hooks']:
                        t = 'error'
                        s = "'%s' not found in click manifest" % app
                        self._add_result(t, n, s)
                        continue
                    elif 'apparmor' not in self.manifest['hooks'][app] and \
                         'apparmor-profile' not in self.manifest['hooks'][app]:
                        t = 'error'
                        s = "'apparmor' not found in click manifest for '%s'" % app
                        self._add_result(t, n, s)
                        continue

        # TODO: error if not 'common' or is 'unconfined'

    def check_security_caps(self):
        '''Check snap caps'''
        if not self.is_click and not self.is_snap1:
            return

        if not self.is_snap1 or self.pkg_yaml['type'] in self.sec_skipped_types:
            return

        for exe_t in ['services', 'binaries']:
            if exe_t not in self.pkg_yaml:
                continue
            for item in self.pkg_yaml[exe_t]:
                if 'caps' not in item:
                    tmpl = []
                else:
                    tmpl = item['caps']

                if 'name' not in item:
                    t = 'error'
                    n = self._get_check_name('yaml_caps_name')
                    s = "package.yaml malformed. Could not find 'name' " + \
                        "for entry in '%s'" % item
                    self._add_result(t, n, s)
                    continue

                # Handle bin/exec concept with bianries
                app = os.path.basename(item['name'])

                t = 'info'
                n = self._get_check_name('yaml_caps', app=app)
                s = "OK"
                if not isinstance(tmpl, list):
                    t = 'error'
                    s = "'%s/%s' malformed: '%s' is not list" % (exe_t, app,
                                                                 tmpl)
                    self._add_result(t, n, s)
                    continue
                self._add_result(t, n, s)

                if self.is_snap1:
                    t = 'info'
                    n = self._get_check_name('yaml_caps_in_manifest', app=app)
                    s = "OK"
                    if app not in self.manifest['hooks']:
                        t = 'error'
                        s = "'%s' not found in click manifest" % app
                        self._add_result(t, n, s)
                        continue
                    elif 'apparmor' not in self.manifest['hooks'][app] and \
                         'apparmor-profile' not in self.manifest['hooks'][app]:
                        t = 'error'
                        s = "'apparmor' not found in click manifest for '%s'" % app
                        self._add_result(t, n, s)
                        continue

        # TODO: error if not 'common'

    def check_template_online_accounts_provider(self):
        '''Check template for online accounts account-provider'''
        if not self.is_click and not self.is_snap1:
            return

        for app in sorted(self.security_apps):
            (f, m) = self._get_security_manifest(app)
            t = 'info'
            n = self._get_check_name('template_account_provider', extra=f)
            s = "OK"
            if 'account-provider' not in self.manifest['hooks'][app]:
                continue
            if 'template' not in m or m['template'] != "ubuntu-account-plugin":
                t = 'error'
                s = "template is not 'ubuntu-account-plugin'"
            self._add_result(t, n, s)

    def check_template_online_accounts_qml_plugin(self):
        '''Check template for online accounts account-qml-plugin'''
        if not self.is_click and not self.is_snap1:
            return

        for app in sorted(self.security_apps):
            (f, m) = self._get_security_manifest(app)
            t = 'info'
            n = self._get_check_name('template_account_qml_plugin', extra=f)
            s = "OK"
            if 'account-qml-plugin' not in self.manifest['hooks'][app]:
                continue
            if 'template' not in m or m['template'] != "ubuntu-account-plugin":
                t = 'error'
                s = "template is not 'ubuntu-account-plugin'"
            self._add_result(t, n, s)

    def check_apparmor_profile_name_length(self):
        '''Check AppArmor profile name length'''
        if not self.is_click and not self.is_snap1:
            return

        maxlen = AA_PROFILE_NAME_MAXLEN
        advlen = AA_PROFILE_NAME_ADVLEN

        for app in sorted(self.security_apps):
            (f, m) = self._get_security_manifest(app)
            t = 'info'
            n = self._get_check_name('profile_name_length', extra=f)
            s = "OK"
            profile = "%s_%s_%s" % (self.click_pkgname, app,
                                    self.click_version)
            if len(profile) > maxlen:
                t = 'error'
                s = ("'%s' too long (exceeds %d characters). Please shorten "
                     "'%s', '%s' and/or '%s'" % (profile, maxlen,
                                                 self.click_pkgname, app,
                                                 self.click_version))
            elif len(profile) > advlen:
                t = 'warn'
                s = ("'%s' is long (exceeds %d characters) and thus could be "
                     "problematic in certain environments. Please consider "
                     "shortening '%s', '%s' and/or '%s'" % (profile, advlen,
                                                            self.click_pkgname,
                                                            app,
                                                            self.click_version)
                     )
            self._add_result(t, n, s)
