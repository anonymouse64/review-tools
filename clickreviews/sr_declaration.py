'''sr_declaration.py: click declaration'''
#
# Copyright (C) 2014-2018 Canonical Ltd.
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
from clickreviews.sr_common import SnapReview, SnapReviewException
from clickreviews.overrides import iface_attributes_noflag
import copy
import re

# Specification:
# https://docs.google.com/document/d/1QkglVjSzHC65lPthXV3ZlQcqPpKxuGEBL-FMuGP6ogs/edit#


class SnapDeclarationException(SnapReviewException):
    '''This class represents SnapDeclaration exceptions'''


class SnapReviewDeclaration(SnapReview):
    '''This class represents click lint reviews'''
    def __init__(self, fn, overrides=None):
        SnapReview.__init__(self, fn, "declaration-snap-v2",
                            overrides=overrides)

        if not self.is_snap2:
            return

        self._verify_declaration(self.base_declaration, base=True)

        self.on_store = None
        if overrides is not None and 'snap_on_store' in overrides:
            if not isinstance(overrides['snap_on_store'], str):
                raise ValueError("'--on-store' should be a str")
            self.on_store = overrides['snap_on_store']

        self.on_brand = None
        if overrides is not None and 'snap_on_brand' in overrides:
            if not isinstance(overrides['snap_on_brand'], str):
                raise ValueError("'--on-brand' should be a str")
            self.on_brand = overrides['snap_on_brand']

        self.snap_declaration = None
        if overrides is not None and ('snap_decl_plugs' in overrides or
                                      'snap_decl_slots' in overrides):
            self.snap_declaration = {}
            self.snap_declaration = {'plugs': {}, 'slots': {}}
            if 'snap_decl_plugs' in overrides:
                self.snap_declaration['plugs'] = overrides['snap_decl_plugs']
            if 'snap_decl_slots' in overrides:
                self.snap_declaration['slots'] = overrides['snap_decl_slots']

            self._verify_declaration(self.snap_declaration, base=False)

    def is_bool(self, item):
        if isinstance(item, int) and (item is True or item is False):
            return True
        return False

    def str2bool(self, s):
        if s == "true" or s == "True":
            return True
        if s == "false" or s == "False":
            return False
        return s

    def _verify_declaration(self, decl, base=False):
        '''Verify declaration'''
        def malformed(name, s, base=False):
            pre = ""
            if base:
                pre = "base "
            err = "%sdeclaration malformed (%s)" % (pre, s)
            if base:
                raise SnapDeclarationException(err)
            self._add_result('error', name, err)

        def verify_constraint(cstr, decl, key, iface, index, allowed,
                              has_alternates):
            found_errors = False
            if self.is_bool(cstr):
                if not base:
                    self._add_result('info', n, s)
                return False
            elif not isinstance(cstr, dict):
                malformed(n, "%s not True, False or dict" %
                          constraint, base)
                return False

            for cstr_key in cstr:
                if cstr_key not in allowed:
                    name = self._get_check_name('valid_%s' % key, app=iface,
                                                extra="%s_%s" % (constraint,
                                                                 cstr_key))
                    malformed(name, "unknown constraint key '%s'" % cstr_key,
                              base)
                    found_errors = True

            if found_errors:
                return False

            cstr_bools = ["on-classic"]
            cstr_lists = ["plug-snap-type",
                          "slot-snap-type",
                          "plug-publisher-id"
                          "slot-publisher-id",
                          "plug-snap-id",
                          "slot-snap-id",
                          "on-store",
                          "on-brand",
                          ]
            cstr_dicts = ["plug-attributes", "slot-attributes"]
            for cstr_key in cstr:
                badn = self._get_check_name('valid_%s' % key, app=iface,
                                            extra="%s_%s" % (constraint,
                                                             cstr_key))
                if cstr_key in cstr_bools:
                    # snap declarations from the store express bools as
                    # strings
                    if isinstance(cstr[cstr_key], str):
                        cstr[cstr_key] = \
                            self.str2bool(cstr[cstr_key])
                        if has_alternates:
                            decl[key][iface][constraint][index][cstr_key] = \
                                self.str2bool(decl[key][iface][constraint][index][cstr_key])
                    if not self.is_bool(cstr[cstr_key]):
                        malformed(badn, "'%s' not True or False" % cstr_key,
                                  base)
                        found_errors = True
                elif cstr_key in cstr_lists:
                    if not isinstance(cstr[cstr_key], list):
                        malformed(badn, "'%s' not a list" % cstr_key, base)
                        found_errors = True
                    else:
                        for entry in cstr[cstr_key]:
                            if not isinstance(entry, str):
                                malformed(badn, "'%s' in '%s' not a string" %
                                          (entry, cstr_key), base)
                                found_errors = True
                elif cstr_key in cstr_dicts:
                    if not isinstance(cstr[cstr_key], dict):
                        malformed(badn, "'%s' not a dict" % cstr_key, base)
                        found_errors = True
                    else:
                        for attrib in cstr[cstr_key]:
                            bn = self._get_check_name('valid_%s' % key,
                                                      app=iface,
                                                      extra="%s_%s" %
                                                      (constraint, cstr_key))
                            if iface not in self.interfaces_attribs:
                                malformed(bn, "unknown attribute '%s'" %
                                          attrib,
                                          base)
                                found_errors = True
                                continue

                            found_iface_attr = False
                            for tmp in self.interfaces_attribs[iface]:
                                known, side = tmp.split('/')
                                if attrib != known:
                                    continue
                                spec_side = side[:-1]

                                if cstr_key.startswith(spec_side):
                                    found_iface_attr = True

                                # snap declarations from the store express
                                # bools as strings
                                if isinstance(cstr[cstr_key][attrib], str):
                                    cstr[cstr_key][attrib] = \
                                        self.str2bool(cstr[cstr_key][attrib])
                                    if has_alternates:
                                        decl[key][iface][constraint][index][cstr_key][attrib] = \
                                            self.str2bool(decl[key][iface][constraint][index][cstr_key][attrib])

                                attr_type = cstr[cstr_key][attrib]

                                # FIXME with rewrite
                                if not isinstance(attr_type,
                                                  type(self.interfaces_attribs[iface][tmp])):
                                    malformed(bn,
                                              "wrong type '%s' for attribute '%s'"
                                              % (attr_type, attrib),
                                              base)
                                    found_errors = True
                                    break

                            if not found_iface_attr:
                                malformed(bn,
                                          "attribute '%s' wrong for '%ss'" %
                                          (attrib, cstr_key[:4]),
                                          base)
                                found_errors = True

                if not found_errors and \
                        cstr_key == "plug-publisher-id" or \
                        cstr_key == "slot-publisher-id":
                    for pubid in cstr[cstr_key]:
                        if not pub_pat.search(pubid):
                            malformed(n, "invalid format for publisher id '%s'"
                                      % pubid)
                            found_errors = True
                            break
                        if pubid.startswith('$'):
                            if cstr_key == "plug-publisher-id" and \
                                    pubid != "$SLOT_PUBLISHER_ID":
                                malformed(n,
                                          "invalid publisher id '%s'" % pubid)
                                found_errors = True
                                break
                            elif cstr_key == "slot-publisher-id" and \
                                    pubid != "$PLUG_PUBLISHER_ID":
                                malformed(n,
                                          "invalid publisher id '%s'" % pubid)
                                found_errors = True
                                break
                elif not found_errors and \
                        cstr_key == "plug-snap-id" or \
                        cstr_key == "slot-snap-id":
                    for id in cstr[cstr_key]:
                        if not id_pat.search(id):
                            malformed(n,
                                      "invalid format for snap id '%s'" % id)
                            found_errors = True
                            break
                elif not found_errors and \
                        cstr_key == "plug-snap-type" or \
                        cstr_key == "slot-snap-type":
                    for snap_type in cstr[cstr_key]:
                        if snap_type not in self.valid_snap_types:
                            malformed(n, "invalid snap type '%s'" % snap_type)
                            found_errors = True
                            break

            return not found_errors
            # end verify_constraint()

        # from snapd.git/assers/ifacedecls.go
        id_pat = re.compile(r'^[a-z0-9A-Z]{32}$')
        pub_pat = re.compile(r'^(?:[a-z0-9A-Z]{32}|[-a-z0-9]{2,28}|\$[A-Z][A-Z0-9_]*)$')

        if not isinstance(decl, dict):
            malformed(self._get_check_name('valid_dict'), "not a dict", base)
            return
        elif len(decl) == 0:
            malformed(self._get_check_name('valid_dict'), "empty", base)
            return

        for key in decl:
            if key not in ["plugs", "slots"]:
                malformed(self._get_check_name('valid_key'),
                          "unknown key '%s'" % key, base)
                return

            if not isinstance(decl[key], dict):
                malformed(self._get_check_name('valid_dict', app=key),
                          "not a dict", base)
                return

            for iface in decl[key]:
                # snap declarations from the store express bools as strings
                if isinstance(decl[key][iface], str):
                    decl[key][iface] = self.str2bool(decl[key][iface])
                # iface may be bool or dict
                if self.is_bool(decl[key][iface]):
                    n = self._get_check_name('valid_%s_bool' % key, app=iface)
                    self._add_result('info', n, 'OK')
                    continue
                elif not isinstance(decl[key][iface], dict):
                    malformed(self._get_check_name('valid_%s_dict' % key,
                                                   app=iface),
                              "interface not True, False or dict", base)
                    continue

                for constraint in decl[key][iface]:
                    # snap declarations from the store express bools as strings
                    if isinstance(decl[key][iface][constraint], str):
                        decl[key][iface][constraint] = \
                            self.str2bool(decl[key][iface][constraint])

                    t = 'info'
                    n = self._get_check_name('valid_%s' % key, app=iface,
                                             extra=constraint)
                    s = "OK"
                    cstr = decl[key][iface][constraint]

                    allowed_ctrs = ["allow-installation",
                                    "deny-installation",
                                    "allow-connection",
                                    "allow-auto-connection",
                                    "deny-connection",
                                    "deny-auto-connection"
                                    ]
                    if constraint not in allowed_ctrs:
                        malformed(n, "unknown constraint '%s'" % constraint,
                                  base)
                        continue

                    allowed = []
                    if constraint.endswith("-installation"):
                        allowed = ["on-classic", "on-store", "on-brand"]
                        if key == "plugs":
                            allowed.append("plug-snap-type")
                            allowed.append("plug-attributes")
                        elif key == "slots":
                            allowed.append("slot-snap-type")
                            allowed.append("slot-attributes")
                    else:
                        allowed = ["plug-attributes", "slot-attributes",
                                   "on-classic", "on-store", "on-brand"]
                        if key == "plugs":
                            allowed.append("slot-publisher-id")
                            allowed.append("slot-snap-id")
                            allowed.append("slot-snap-type")
                        elif key == "slots":
                            allowed.append("plug-publisher-id")
                            allowed.append("plug-snap-id")
                            allowed.append("plug-snap-type")

                    # constraint may be bool or dict or lists of bools and
                    # dicts
                    alternates = []
                    if isinstance(cstr, list):
                        alternates = cstr
                    else:
                        alternates.append(cstr)

                    found_errors = False
                    index = 0
                    for alt in alternates:
                        if not verify_constraint(alt, decl, key, iface, index,
                                                 allowed,
                                                 (len(alternates) > 1)):
                            found_errors = True
                        index += 1

                    if not base and not found_errors:
                        self._add_result(t, n, s)

    def _match(self, against, val):
        '''Ordering matters since 'against' is treated as a regex if str'''
        if type(against) != type(val):
            return False

        if type(val) not in [str, list, dict, bool]:
            raise SnapDeclarationException("unknown type '%s'" % val)

        matched = False

        if isinstance(val, str):
            if re.search(r'^(%s)$' % against, val):
                matched = True
        elif isinstance(val, list):
            # TODO: nested matches for lists
            matched = (sorted(against) == sorted(val))
        else:  # bools and dicts (TODO: nested matches for dicts)
            matched = (against == val)

        return matched

    def _search(self, d, key, val=None, subkey=None, subval=None, subval_inverted=False):
        '''Search dictionary 'd' for matching values. Returns true when
           - val == d[key]
           - subval in d[key][subkey]
           - subval dictionary has any matches in d[key][subkey] dict
           - subval_inverted == True and subval has any non-matches in
             d[key][subkey] dict

           When 'key' must be in 'd' and when 'subkey' is not None, it must be
           in d[key] (we want to raise an Exception here for when _search() is
           used with only exact matches).
        '''
        found = False

        if val is not None and val == d[key]:
            found = True
        elif isinstance(d[key], dict) and subkey is not None and \
                subval is not None:
            if self.is_bool(d[key][subkey]):
                found = d[key][subkey] == subval
                if subval_inverted:
                    found = not found
            elif isinstance(d[key][subkey], list):
                if subval_inverted:
                    if subval not in d[key][subkey]:
                        found = True
                elif subval in d[key][subkey]:
                    found = True
            elif isinstance(d[key][subkey], dict) and isinstance(subval, dict):
                d_keys = set(d[key][subkey].keys())
                subval_keys = set(subval.keys())
                int_keys = d_keys.intersection(subval_keys)
                matches = 0
                for subsubkey in int_keys:
                    if self._match(d[key][subkey][subsubkey],
                                   subval[subsubkey]) or \
                            d[key][subkey][subsubkey] in \
                            iface_attributes_noflag:
                        found = True
                        matches += 1

                if subval_inverted:
                    # return true when something didn't match
                    if matches != len(int_keys):
                        found = True
                    else:
                        found = False

        return found

    def _get_decl(self, base, snap, side, interface, dtype):
        '''If the snap declaration has something to say about the declaration
           override type (dtype), then use it instead of the base declaration
           iff the store/brand passed to us matches the store/brand in the snap
           declaration.
        '''
        decl = copy.deepcopy(base)  # avoid any side-effects
        base_decl = True
        decl_type = "base"

        if snap is not None and side in snap and interface in snap[side]:
            for k in snap[side][interface]:
                if k.endswith(dtype):
                    # only apply the scoped constraint from the snap
                    # declaration if it is properly scoped to the store/brand
                    #
                    # NOTE: currently if --on-store/--on-brand is specified to
                    # the review-tools but the constraint here is not scoped
                    # (doesn't contain on-store/on-brand: []) then we treat it
                    # as if --on-store/--on-brand was not specified. If store
                    # behavior changes, this code might have to change.
                    if isinstance(snap[side][interface][k], dict):
                        if 'on-store' in snap[side][interface][k] and \
                                'on-brand' in snap[side][interface][k] and not \
                                (self.on_store in snap[side][interface][k]['on-store'] and
                                 self.on_brand in snap[side][interface][k]['on-brand']):
                            # when both on-store and on-brand are in the snap
                            # declaration, if either doesn't match, then ignore
                            # the declaration since it isn't scoped to both
                            continue
                        elif 'on-store' in snap[side][interface][k] and \
                                self.on_store not in snap[side][interface][k]['on-store']:
                            # when on-store is in the snap declaration, if it
                            # doesn't match, then ignore the declaration since
                            # it isn't scoped to the store.
                            continue
                        elif 'on-brand' in snap[side][interface][k] and \
                                self.on_brand not in snap[side][interface][k]['on-brand']:
                            # when on-brand is in the snap declaration, if it
                            # doesn't match, then ignore the declaration since
                            # it isn't scoped to the brand.
                            continue

                    # Otherwise, use the snap declaration
                    decl = copy.deepcopy(snap)  # avoid any side-effects
                    base_decl = False
                    decl_type = "snap"
                    break

        return (decl, base_decl, decl_type)

    def _get_all_combinations(self, interface):
        '''Return list of all base and snap declaration combinations where
           each base/snap declaration pair represents a particular combination
           of alternate constraints. Also return if there are alternate
           constraints anywhere.

           For simple declarations, this will return the interface of the
           base declaration and if a snap declaration is specified, the
           interface of the snap declaration (ie, a single base/snap
           declaration pair).

           For complex declarations with alternate constrainst, this will
           return a list of pairs such that for each of base and snap
           declarations, we'll expand like so (showing on the base declaration
           for simplicity):

               base = {
                   'slots': {
                       'interface': {
                           'foo': '1',
                           'bar': ['2', '3'],
                           'baz': '4',
                           'norf': ['5', '6'],
                       }
                   },
                   'plugs': {
                       'interface': {
                           'qux': '7',
                           'quux': ['8', '9'],
                       }
                   }
               }

            then the list of 'base declarations' to check against is:

                decls['base'] = [
                    {'slots': {
                        'interface': {
                            'foo': '1',
                            'bar': '2',
                            'baz': '4',
                            'norf': '5',
                        },
                    },
                    {'slots': {
                        'interface': {
                            'foo': '1',
                            'bar': '2',
                            'baz': '4',
                            'norf': '6',
                        }
                    },
                    {'slots': {
                        'interface': {
                            'foo': '1',
                            'bar': '3',
                            'baz': '4',
                            'norf': '5',
                        }
                    },
                    {'slots': {
                        'interface': {
                            'foo': '1',
                            'bar': '3',
                            'baz': '4',
                            'norf': '6',
                        }
                    },
                    {'plugs': {
                        'interface': {
                            'qux': '7',
                            'quux': '8',
                        }
                    },
                    {'plugs': {
                        'interface': {
                            'qux': '7',
                            'quux': '9',
                        }
                    },
                ]

            If the plugs side is defined for this interface, it will appear
            next to the slot as with a regular declaration. If the snap
            declaration is defined, it will be stored in decls['snap'] in the
            same way as the base declaration.

            In this manner, each one of the base declarations can be evaluated
            and compared to any defined snap declarations.
        '''
        def expand(d, side, interface, keys, templates):
            if len(keys) == 0:
                return templates

            updated = []
            key = keys[-1]
            for i in d[side][interface][key]:
                for t in templates:
                    tmp = {side: {interface: {}}}
                    # copy existing keys
                    for template_key in t[side][interface]:
                        tmp[side][interface][template_key] = \
                            t[side][interface][template_key]
                    tmp[side][interface][key] = i
                    updated.append(tmp)

            return expand(d, side, interface, keys[:-1], updated)

        decls = {'base': [], 'snap': []}

        has_alternates = False
        for dtype in ["base", "snap"]:
            if dtype == "base":
                d = self.base_declaration
            else:
                d = self.snap_declaration

            tmp = {}
            for side in ["plugs", "slots"]:
                if dtype == "snap" and d is None:
                    continue
                if side not in d or interface not in d[side]:
                    continue

                to_expand = []
                template = {side: {interface: {}}}
                for cstr in d[side][interface]:
                    if isinstance(d[side][interface][cstr], list):
                        to_expand.append(cstr)
                    else:
                        template[side][interface][cstr] = \
                            d[side][interface][cstr]

                tmp[side] = []
                tmp[side] += expand(d, side, interface, to_expand, [template])

                if len(to_expand) > 0:
                    has_alternates = True

            # Now that we have all the slots combinations and all the plugs
            # combinations, create combinations of those
            if "plugs" in tmp and "slots" in tmp:
                for p in tmp["plugs"]:
                    for s in tmp["slots"]:
                        decls[dtype].append({'plugs': p['plugs'],
                                             'slots': s['slots']})
            elif "plugs" in tmp:
                decls[dtype] = tmp["plugs"]
            elif "slots" in tmp:
                decls[dtype] = tmp["slots"]

        # We need at least one declaration per list, even if it is None
        if len(decls['snap']) == 0:
            decls['snap'].append(None)

        return (decls, has_alternates)

    def _verify_iface_by_declaration(self, base, snap, name, iface, interface, attribs, side, oside):
        # 'checked' is used to see if a particular check is made (eg, if
        # 'deny-connection' for this interface was performed).
        #
        # 'denied' is used to track if something checked prompted manual review
        #
        # _verify_iface_by_declaration() will return if something prompted
        # manual review (denied > 0) and if this is an exact match (ie, if
        # checked == denied).
        checked = 0
        denied = 0

        def err(key, subkey=None, dtype="base", attrs=None):
            s = "human review required due to '%s' constraint " % key
            if subkey is not None:
                s += "for '%s' " % subkey
            s += "from %s declaration" % dtype

            if attrs is not None:
                if 'allow-sandbox' in attrs and attrs['allow-sandbox']:
                    s += ". If using a chromium webview, you can disable " + \
                         "the internal sandbox (eg, use --no-sandbox) and " + \
                         "remove the 'allow-sandbox' attribute instead. " + \
                         "For Oxide webviews, export OXIDE_NO_SANDBOX=1 " + \
                         "to disable its internal sandbox. Similarly for " + \
                         "QtWebEngine, use QTWEBENGINE_DISABLE_SANDBOX=1."

            return s

        # top-level allow/deny-installation/connection
        # Note: auto-connection is only for snapd, so don't include it here
        for i in ['installation', 'connection']:
            for j in ['deny', 'allow']:
                decl_key = "%s-%s" % (j, i)
                # flag if deny-* is true or allow-* is false
                (decl, base_decl, decl_type) = self._get_decl(base, snap, side,
                                                              interface, i)
                if side in decl and interface in decl[side] and \
                        decl_key in decl[side][interface] and \
                        not isinstance(decl[side][interface][decl_key], dict):
                    checked += 1
                    if self._search(decl[side][interface], decl_key,
                                    j == 'deny'):
                        self._add_result('error',
                                         self._get_check_name("%s_%s" %
                                                              (side, decl_key),
                                                              app=iface,
                                                              extra=interface),
                                         err(decl_key, dtype=decl_type),
                                         manual_review=True,
                                         stage=True)
                        denied += 1

                        # if manual review after 'deny', don't look at allow
                        break

        # deny/allow-installation snap-type
        snap_type = 'app'
        if 'type' in self.snap_yaml:
            snap_type = self.snap_yaml['type']
            if snap_type == 'os':
                snap_type = 'core'
        decl_subkey = '%s-snap-type' % side[:-1]
        for j in ['deny', 'allow']:
            (decl, base_decl, decl_type) = self._get_decl(base, snap, side,
                                                          interface,
                                                          'installation')
            decl_key = "%s-installation" % j
            # flag if deny-*/snap-type matches or allow-*/snap-type doesn't
            if side in decl and interface in decl[side] and \
                    decl_key in decl[side][interface] and \
                    isinstance(decl[side][interface][decl_key], dict) and \
                    decl_subkey in decl[side][interface][decl_key]:
                checked += 1
                if self._search(decl[side][interface], decl_key,
                                subkey=decl_subkey, subval=snap_type,
                                subval_inverted=(j == 'allow')):
                    self._add_result('error',
                                     self._get_check_name("%s_%s" %
                                                          (side, decl_key),
                                                          app=iface,
                                                          extra=interface),
                                     err(decl_key, decl_subkey, decl_type),
                                     manual_review=True,
                                     stage=True)
                    denied += 1

                    # if manual review after 'deny', don't look at allow
                    break

        # deny/allow-connection/installation on-classic with app snaps
        # Note: auto-connection is only for snapd, so don't include it here
        snap_type = 'app'
        if 'type' in self.snap_yaml:
            snap_type = self.snap_yaml['type']
            if snap_type == 'os':
                snap_type = 'core'
        decl_subkey = 'on-classic'
        for i in ['installation', 'connection']:
            for j in ['deny', 'allow']:
                (decl, base_decl, decl_type) = self._get_decl(base, snap, side,
                                                              interface, i)
                decl_key = "%s-%s" % (j, i)
                # when an app snap, flag if deny-*/on-classic=false or
                # allow-*/on-classic=true
                # when not an app snap, flag if deny-*/on-classic=true or
                # allow-*/on-classic=false
                if side in decl and interface in decl[side] and \
                        decl_key in decl[side][interface] and \
                        isinstance(decl[side][interface][decl_key], dict) and \
                        decl_subkey in decl[side][interface][decl_key]:
                    checked += 1
                    if self._search(decl[side][interface], decl_key,
                                    subkey=decl_subkey,
                                    subval=(snap_type == 'app'),
                                    subval_inverted=(j == 'deny')):
                        self._add_result('error',
                                         self._get_check_name("%s_%s" %
                                                              (side, decl_key),
                                                              app=iface,
                                                              extra=interface),
                                         err(decl_key, decl_subkey, decl_type),
                                         manual_review=True,
                                         stage=True)
                        denied += 1

                        # if manual review after 'deny', don't look at allow
                        break

        # deny/allow-connection/installation attributes
        # Note: auto-connection is only for snapd, so don't include it here
        decl_subkey = '%s-attributes' % side[:-1]
        for i in ['installation', 'connection']:
            if attribs is None:
                continue
            for j in ['deny', 'allow']:
                (decl, base_decl, decl_type) = self._get_decl(base, snap, side,
                                                              interface, i)
                decl_key = "%s-%s" % (j, i)
                # flag if any deny-*/attribs match or any allow-*/attribs don't
                if side in decl and interface in decl[side] and \
                        decl_key in decl[side][interface] and \
                        isinstance(decl[side][interface][decl_key], dict) and \
                        decl_subkey in decl[side][interface][decl_key]:
                    checked += 1
                    if self._search(decl[side][interface], decl_key,
                                    subkey=decl_subkey, subval=attribs,
                                    subval_inverted=(j == 'allow')):
                        self._add_result('error',
                                         self._get_check_name("%s_%s" %
                                                              (side, decl_key),
                                                              app=iface,
                                                              extra=interface),
                                         err(decl_key, decl_subkey, decl_type, attribs),
                                         manual_review=True,
                                         stage=True)
                        denied += 1

                        # if manual review after 'deny', don't look at allow
                        break
                # Since base declaration mostly has slots side, if plugs, look
                # at the other side for checking plug-attributes
                elif base_decl and side == 'plugs' and oside in decl and \
                        interface in decl[oside] and \
                        decl_key in decl[oside][interface] and \
                        decl_subkey in decl[oside][interface][decl_key]:
                    checked += 1
                    if self._search(decl[oside][interface], decl_key,
                                    subkey=decl_subkey, subval=attribs,
                                    subval_inverted=(j == 'allow')):
                        self._add_result('error',
                                         self._get_check_name("%s_%s" %
                                                              (side, decl_key),
                                                              app=iface,
                                                              extra=interface),
                                         err(decl_key, decl_subkey, decl_type, attribs),
                                         manual_review=True,
                                         stage=True)
                        denied += 1

                        # if manual review after 'deny', don't look at allow
                        break

        # Return if something prompted for manual review and if everything
        # checked was denied (an exact match denial)
        return (denied > 0, checked == denied)

    def _verify_iface(self, name, iface, interface, attribs=None):
        if name.endswith('slot'):
            side = 'slots'
            oside = 'plugs'
        elif name.endswith('plug'):
            side = 'plugs'
            oside = 'slots'

        t = 'info'
        n = self._get_check_name('%s_known' % name, app=iface, extra=interface)
        s = 'OK'
        if side in self.base_declaration and \
                interface not in self.base_declaration[side] and \
                oside in self.base_declaration and \
                interface not in self.base_declaration[oside]:
            if name.startswith('app_') and side in self.snap_yaml and \
                    interface in self.snap_yaml[side]:
                # If it is an interface reference used by an app, skip since it
                # will be checked in top-level interface checks.
                return
            t = 'error'
            s = "interface '%s' not found in base declaration" % interface
            self._add_result(t, n, s)
            return

        # To support alternates in the base and snap declaration, we need to
        # try each combination of snap alternate constraint and base alternate
        # constraint. If we have alternates and one passes and there are no
        # exact denials, then don't report. Otherwise report if require manual
        # review.
        (decls, has_alternates) = self._get_all_combinations(interface)
        require_manual = False

        exact_deny = True
        for b in decls['base']:
            for s in decls['snap']:
                (manual, exact) = \
                    self._verify_iface_by_declaration(b, s, name, iface,
                                                      interface, attribs, side,
                                                      oside)
                if manual:
                    require_manual = True
                    if has_alternates and not exact:
                        exact_deny = False

        if has_alternates and not exact_deny:
            require_manual = False

        # Apply our staged results if required, otherwise report all is ok
        if require_manual:
            self._apply_staged_results()
        else:
            self._add_result('info',
                             self._get_check_name("%s" % side, app=iface,
                                                  extra=interface),
                             "OK", manual_review=False)

    def check_declaration(self):
        '''Check base/snap declaration requires manual review for top-level
           plugs/slots
        '''
        if not self.is_snap2:
            return

        for side in ['plugs', 'slots']:
            if side not in self.snap_yaml:
                continue

            for iface in self.snap_yaml[side]:
                # If the 'interface' name is the same as the 'plug/slot' name,
                # then 'interface' is optional since the interface name and the
                # plug/slot name are the same
                interface = iface
                attribs = None

                spec = self.snap_yaml[side][iface]
                if isinstance(spec, str):
                    # Abbreviated syntax (no attributes)
                    # <plugs|slots>:
                    #   <alias>: <interface>
                    interface = spec
                elif 'interface' in spec:
                    # Full specification.
                    # <plugs|slots>:
                    #   <alias>:
                    #     interface: <interface>
                    interface = spec['interface']
                    if len(spec) > 1:
                        attribs = spec
                        del attribs['interface']

                # self._verify_iface(side[:-1], iface, interface, attribs)
                self._verify_iface2(side[:-1], iface, interface, attribs)

    def check_declaration_apps(self):
        '''Check base/snap declaration requires manual review for apps
           plugs/slots
        '''
        if not self.is_snap2 or 'apps' not in self.snap_yaml:
            return

        for app in self.snap_yaml['apps']:
            for side in ['plugs', 'slots']:
                if side not in self.snap_yaml['apps'][app]:
                    continue

                # The interface referenced in the app's 'plugs' or 'slots'
                # field can either be a known interface (when the interface
                # name reference and the interface is the same) or can
                # reference a name in the snap's toplevel 'plugs' or 'slots'
                # mapping
                for ref in self.snap_yaml['apps'][app][side]:
                    if not isinstance(ref, str):
                        continue  # checked elsewhere

                    # self._verify_iface('app_%s' % side[:-1], app, ref)
                    self._verify_iface2('app_%s' % side[:-1], app, ref)

    # helpers
    def _getDecl(self, side, iface, snapDecl):
        if snapDecl:
            if iface in self.snap_declaration[side]:
                return copy.deepcopy(self.snap_declaration[side][iface])
            else:
                return None

        if iface in self.base_declaration[side]:
            return copy.deepcopy(self.base_declaration[side][iface])
        elif iface in self.base_declaration['slots']:
            return copy.deepcopy(self.base_declaration['slots'][iface])

        return None

    def _getRules(self, decl, cstr_type):
        rules = {}
        if decl is None:
            return rules
        for i in ['allow', 'deny']:
            cstr = '%s-%s' % (i, cstr_type)
            if cstr in decl:
                if isinstance(decl[cstr], list):
                    rules[cstr] = decl[cstr]
                else:
                    rules[cstr] = [decl[cstr]]
        return rules

    def _attributesCheck(self, side, iface, rules, cstr):
        def _checkAttrib(val, against):
            if type(val) not in [str, list, dict, bool]:
                raise SnapDeclarationException("unknown type '%s'" % val)

            matched = False
            if isinstance(val, str):
                if re.search(r'^(%s)$' % against, val):
                    matched = True
            elif isinstance(val, list):
                for i in val:
                    if _checkAttrib(i, against):
                        matched = True
            else:  # bools and dicts (TODO: nested matches for dicts)
                matched = (against == val)

            return matched

        print("JAMIE3: side=%s, iface=%s, rules=%s, cstr=%s" % (side, iface, rules, cstr))
        matched = False
        checked = False

        for rules_key in rules:
            if not rules_key == "%s-attributes" % side[:-1]:
                continue
            checked = True

            for rules_attrib in rules[rules_key]:
                if rules_attrib in iface:
                    val = iface[rules_attrib]
                    against = rules[rules_key][rules_attrib]

                    if isinstance(against, list):
                        num_matched = 0
                        for i in against:
                            if _checkAttrib(val, i):
                                num_matched += 1
                            matched = (num_matched == len(against))
                    else:
                        matched = _checkAttrib(val, against)

        print("JAMIE3.4: matched=%s, checked=%s, cstr=%s" % (matched, checked, cstr))
        if checked and ((matched and cstr.startswith('deny')) or
                        (not matched and cstr.startswith('allow'))):
            s = "failed due to %s constraint (interface attributes)" % cstr
            if "plug-attributes" in rules and \
                    'allow-sandbox' in rules['plug-attributes'] and \
                    rules['plug-attributes']['allow-sandbox']:
                s += ". If using a chromium webview, you can disable the " + \
                     "internal sandbox (eg, use --no-sandbox) and remove " + \
                     "the 'allow-sandbox' attribute instead. For " + \
                     "QtWebEngine webviews, export " + \
                     "QTWEBENGINE_DISABLE_SANDBOX=1 to disable its " + \
                     "internal sandbox."
            return (checked, s)

        return (checked, None)

    # func checkSnapType() in helpers.go
    def _checkSnapType(self, side, iface, rules, cstr):
        print("JAMIE4: side=%s, iface=%s, rules=%s, cstr=%s" % (side, iface, rules, cstr))
        snap_type = 'app'
        if 'type' in self.snap_yaml:
            snap_type = self.snap_yaml['type']
            if snap_type == 'os':
                snap_type = 'core'

        matched = False
        checked = False
        for rules_key in rules:
            if not rules_key == "%s-snap-type" % side[:-1]:
                continue
            checked = True

            if snap_type in rules[rules_key]:
                matched = True

        print("JAMIE4.4: matched=%s, checked=%s, cstr=%s" % (matched, checked, cstr))
        if checked and ((matched and cstr.startswith('deny')) or
                        (not matched and cstr.startswith('allow'))):
            return (checked, "failed due to %s constraint (snap-type)" % cstr)

        return (checked, None)

    # func checkOnClassic() in helpers.go
    def _checkOnClassic(self, side, iface, rules, cstr):
        print("JAMIE5: side=%s, iface=%s, rules=%s, cstr=%s" % (side, iface, rules, cstr))
        if 'type' in self.snap_yaml and self.snap_yaml['type'] != 'app':
            return (False, None)

        # if on-classic is specified at all, we want to flag since some of
        # the snaps need special attention
        if "on-classic" in rules:
            return (True, "failed due to %s constraint (on-classic)" % cstr)

        return (False, None)

    # func checkDeviceScope() in helpers.go
    def _checkDeviceScope(self, side, iface, rules, cstr):
        print("JAMIE6: side=%s, iface=%s, rules=%s, cstr=%s" % (side, iface, rules, cstr))

        # on-store
        matched = False
        checkedStore = False
        if self.on_store:
            checkedStore = True
            if "on-store" in rules and self.on_store in rules['on-store']:
                matched = True

        print("JAMIE6.4: matched=%s, checkedStore=%s, cstr=%s" % (matched, checkedStore, cstr))
        if checkedStore and ((matched and cstr.startswith('deny')) or
                             (not matched and cstr.startswith('allow'))):
            return (checkedStore, "failed due to %s constraint (on-store)" % cstr)

        # on-brand
        matched = False
        checkedBranch = False
        if self.on_brand:
            checkedBranch = True
            if "on-brand" in rules and self.on_brand in rules['on-brand']:
                matched = True

        print("JAMIE6.5: matched=%s, checkedBranch=%s, cstr=%s" % (matched, checkedBranch, cstr))
        if checkedBranch and ((matched and cstr.startswith('deny')) or
                              (not matched and cstr.startswith('allow'))):
            return (checkedBranch, "failed due to %s constraint (on-brand)" % cstr)

        return (checkedStore or checkedBranch, None)

    # func checkPlugInstallationConstraints1() in helpers.go
    def _checkInstallationConstraints1(self, side, iface, rules, cstr):
        print("JAMIE2: side=%s, iface=%s, rules=%s, cstr=%s" % (side, iface, rules, cstr))

        # no need to check the others if we have a toplevel constraint
        if isinstance(rules, bool):
            if ((rules and cstr.startswith('deny')) or
                    (not rules and cstr.startswith('allow'))):
                return "failed due to %s constraint (bool)" % cstr
            return None

        # if res is not None with allowed, just return res since we have a
        # failure to match. If all the res are not None with denied, then we
        # have a full match and will return the first res.
        denied = []
        num_checked = 0

        (checked, res) = self._attributesCheck(side, iface, rules, cstr)
        if checked:
            num_checked += 1
        if res is not None:
            if cstr.startswith('allow'):
                return res
            denied.append(res)

        (checked, res) = self._checkSnapType(side, iface, rules, cstr)
        if checked:
            num_checked += 1
        if res is not None:
            if cstr.startswith('allow'):
                return res
            denied.append(res)

        (checked, res) = self._checkOnClassic(side, iface, rules, cstr)
        if checked:
            num_checked += 1
        if res is not None:
            if cstr.startswith('allow'):
                return res
            denied.append(res)

        (checked, res) = self._checkDeviceScope(side, iface, rules, cstr)
        if checked:
            num_checked += 1
        if res is not None:
            if cstr.startswith('allow'):
                return res
            denied.append(res)

        print("JAMIE2.1: cstr=%s, num_checked=%s, denied=%s" % (cstr, num_checked, denied))
        if cstr.startswith('deny') and num_checked > 0 and \
                len(denied) == num_checked:
            # FIXME: perhaps allow showing more than just the first
            return denied[0]

        return None

    # func checkPlugInstallationConstraints() in helpers.go
    def _checkInstallationConstraints(self, side, iface, rules, cstr):
        print("JAMIE1: side=%s, iface=%s, rules=%s, cstr=%s" % (side, iface, rules, cstr))
        if cstr not in rules:
            return None

        firstError = None

        # OR of constraints
        if side.startswith('allow'):
            # With allow, the first success is a match and we allow it
            for i in rules[cstr]:
                res = self._checkInstallationConstraints1(side, iface, i, cstr)
                print("JAMIE1.1: res=%s" % res)
                if res is None:
                    return res

                if firstError is None:
                    firstError = res

            return firstError
        else:
            # With deny, the first failure is a match and we deny it
            for i in rules[cstr]:
                res = self._checkInstallationConstraints1(side, iface, i, cstr)
                print("JAMIE1.2: res=%s" % res)
                if res is not None:
                    return res

            return None

    def _checkRule(self, side, iface, rules, cstr_type):
        res = self._checkInstallationConstraints(side, iface, rules, 'deny-%s' % cstr_type)
        if res is not None:
            return res

        res = self._checkInstallationConstraints(side, iface, rules, 'allow-%s' % cstr_type)
        if res is not None:
            return res

        return None

    # func (ic *InstallCandidate) checkPlug()/checkSlot() from policy.go
    def _checkInstallSide(self, side, iface, cstr_type):
        # if the snap declaration has something to say for this constraint,
        # only it is consulted (there is no merging with base declaration)
        snapHasSay = False
        if self.snap_declaration and iface['interface'] in self.snap_declaration[side]:
            for i in ['allow', 'deny']:
                cstr = "%s-%s" % (i, cstr_type)
                if cstr in self.snap_declaration[side][iface['interface']]:
                    snapHasSay = True
                    break

        if snapHasSay:
            decl = self._getDecl(side, iface['interface'], True)
            rules = self._getRules(decl, cstr_type)
            if rules is not None:
                return self._checkRule(side, iface, rules, cstr_type)
            return None

        decl = self._getDecl(side, iface['interface'], False)
        rules = self._getRules(decl, cstr_type)
        if rules is not None:
            return self._checkRule(side, iface, rules, cstr_type)
        return None

    # func (ic *InstallCandidate) Check() in policy.go
    def _installationCheck(self, side, iname, attribs):
        print("JAMIE0.1: side=%s, iname=%s, attribs=%s" % (side, iname, attribs))
        iface = {}
        if attribs is not None:
            iface = copy.deepcopy(attribs)
        iface['interface'] = iname

        if side == 'slots':
            res = self._checkInstallSide('slots', iface, "installation")
            if res is not None:
                return res

        if side == 'plugs':
            res = self._checkInstallSide('plugs', iface, "installation")
            if res is not None:
                return res

        return None

    # TODO: verify this logic is correct for us since it is different than
    # snapd
    # func (ic *ConnectionCandidate) check() in policy.go
    def _connectionCheck(self, side, iname, attribs):
        print("JAMIE0.2: side=%s, iname=%s, attribs=%s" % (side, iname, attribs))
        iface = {}
        if attribs is not None:
            iface = copy.deepcopy(attribs)
        iface['interface'] = iname

        if side == 'slots':
            res = self._checkInstallSide('slots', iface, "connection")
            if res is not None:
                return res

        if side == 'plugs':
            res = self._checkInstallSide('plugs', iface, "connection")
            if res is not None:
                return res

        return None

    def _verify_iface2(self, name, iface, interface, attribs=None):
        print("JAMIE0: name=%s, iface=%s, interface=%s, attribs=%s" % (name, iface, interface, attribs))
        if self.snap_declaration and 'plugs' in self.snap_declaration and interface in self.snap_declaration['plugs']:
            print("JAMIE0: snapdecl[plugs][%s]=%s" % (interface, self.snap_declaration['plugs'][interface]))
        if self.snap_declaration and 'slots' in self.snap_declaration and interface in self.snap_declaration['slots']:
            print("JAMIE0: snapdecl[slots][%s]=%s" % (interface, self.snap_declaration['slots'][interface]))
        if 'plugs' in self.base_declaration and interface in self.base_declaration['plugs']:
            print("JAMIE0: basedecl[plugs][%s]=%s" % (interface, self.base_declaration['plugs'][interface]))
        if 'slots' in self.base_declaration and interface in self.base_declaration['slots']:
            print("JAMIE0: basedecl[slots][%s]=%s" % (interface, self.base_declaration['slots'][interface]))

        if name.endswith('slot'):
            side = 'slots'
            oside = 'plugs'
        elif name.endswith('plug'):
            side = 'plugs'
            oside = 'slots'

        t = 'info'
        n = self._get_check_name('%s_known' % name, app=iface, extra=interface)
        s = 'OK'
        if side in self.base_declaration and \
                interface not in self.base_declaration[side] and \
                oside in self.base_declaration and \
                interface not in self.base_declaration[oside]:
            if name.startswith('app_') and side in self.snap_yaml and \
                    interface in self.snap_yaml[side]:
                # If it is an interface reference used by an app, skip since it
                # will be checked in top-level interface checks.
                return
            t = 'error'
            s = "interface '%s' not found in base declaration" % interface
            self._add_result(t, n, s)
            return

        # only need to check installation and connection since snapd handles
        # auto-connection
        t = 'info'
        n = self._get_check_name('%s' % side, app=iface, extra=interface)
        s = 'OK'
        err = self._installationCheck(side, interface, attribs)
        if err is not None:
            t = 'error'
            s = err
        err = self._connectionCheck(side, interface, attribs)
        if err is not None:
            t = 'error'
            s = err
        self._add_result(t, n, s)
