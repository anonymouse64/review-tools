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

                                # Mark as malformed if the attribute type in
                                # the decl is different from that defined in
                                # sr_common.py, except when that in
                                # sr_common.py is a list and the decl specifies
                                # a string (since in the decl one can specify a
                                # string as a match/regex for something in the
                                # list)
                                if not isinstance(attr_type,
                                                  type(self.interfaces_attribs[iface][tmp])) \
                                    and not (isinstance(self.interfaces_attribs[iface][tmp], list) and
                                             isinstance(attr_type, str)):
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

    def _get_decl(self, side, iface, snapDecl):
        '''Obtain the declaration for the interface. When snapDecl is False,
           get the base declaration, falling back to slots as needed.
           Returns (found decl, [snap|base]/[<side>|fallback])
        '''
        if snapDecl:
            if iface in self.snap_declaration[side]:
                return (copy.deepcopy(self.snap_declaration[side][iface]),
                        "snap/%s" % side)
            else:
                return (None, None)

        if iface in self.base_declaration[side]:
            return (copy.deepcopy(self.base_declaration[side][iface]),
                    "base/%s" % side)
        elif iface in self.base_declaration['slots']:
            # Fallback to slots in the base declaration if nothing is in plugs
            return (copy.deepcopy(self.base_declaration['slots'][iface]),
                    "base/fallback")

        return (None, None)

    def _is_scoped(self, rules):
        '''Return whether or not the specified rules are scoped to the snap as
           dictated by the --on-store and --on-brand overrides
        '''
        # NOTE: currently if --on-store/--on-brand is specified to the
        # review-tools but the constraint here is not scoped (doesn't
        # contain on-store/on-brand: []) then we treat it as if
        # --on-store/--on-brand was not specified. If store behavior
        # changes, this code might have to change.
        scoped = False
        if not isinstance(rules, dict):
            # no defined scoping, so scoped to us
            scoped = True
        elif "on-store" not in rules and "on-brand" not in rules:
            # no defined scoping, so scoped to us
            scoped = True
        elif "on-store" in rules and "on-brand" in rules:
            if self.on_store in rules["on-store"] and \
                    self.on_brand in rules["on-brand"]:
                # both store and brand match
                scoped = True
        elif "on-store" in rules and self.on_store in rules["on-store"]:
            # store matches
            scoped = True
        elif "on-brand" in rules and self.on_brand in rules["on-brand"]:
            # brand matches
            scoped = True

        return scoped

    def _get_rules(self, decl, cstr_type):
        '''Obtain the rules, if any, from the specified decl for this
           constraint type (eg, 'connection' or 'installation'.
        '''
        scoped = True
        rules = {}

        if decl is None:
            return rules, False
        elif 'allow-%s' % cstr_type not in decl and \
                'deny-%s' % cstr_type not in decl:
            return rules, False

        for i in ['allow', 'deny']:
            cstr = '%s-%s' % (i, cstr_type)
            if cstr in decl:
                if isinstance(decl[cstr], list):
                    tmp = []
                    for r in decl[cstr]:
                        if self._is_scoped(r):
                            tmp.append(r)
                    if len(tmp) == 0:
                        scoped = False
                    else:
                        rules[cstr] = tmp
                else:
                    if self._is_scoped(decl[cstr]):
                        rules[cstr] = [decl[cstr]]
                    else:
                        scoped = False

        return (rules, scoped)

    def _check_attributes(self, side, iface, rules, cstr):
        '''Check if there are any matching attributes for this side, interface,
           rules and constraint. If attributes are specified in the constraint,
           they all must match. If the attribute is a list, just one must
           match (it is considered a list of alternatives).
        '''
        def _check_attrib(val, against, side, rules_attrib):
            if type(val) not in [str, list, dict, bool]:
                raise SnapDeclarationException("unknown type '%s'" % val)

            matched = False
            if isinstance(val, str):
                if against.startswith('$'):
                    if against == '$MISSING':
                        matched = False  # value must not be set
                    elif re.search(r'^\$PLUG\(%s\)$' % rules_attrib, against):
                        matched = True
                    elif re.search(r'^\$SLOT\(%s\)$' % rules_attrib, against):
                        matched = True
                    else:
                        raise SnapDeclarationException(
                            "unknown special attrib '%s'" % against)
                elif re.search(r'^(%s)$' % against, val):
                    matched = True
            elif isinstance(val, list):
                for i in val:
                    if _check_attrib(i, against, side, rules_attrib):
                        matched = True
            else:  # bools and dicts (TODO: nested matches for dicts)
                matched = (against == val)

            return matched

        matched = False
        checked = False
        attributes_matched = {}
        num_iface_attribs = len(iface) - 1  # skip the 'interface' key

        for rules_key in rules:
            if rules_key not in ['slot-attributes', 'plug-attributes']:
                continue
            elif len(rules[rules_key]) == 0:  # if empty, then just ignore
                continue

            checked = True

            attributes_matched[rules_key] = {}
            attributes_matched[rules_key]['len'] = len(rules[rules_key])
            attributes_matched[rules_key]['matched'] = 0
            for rules_attrib in rules[rules_key]:
                if rules_attrib in iface:
                    val = iface[rules_attrib]
                    against = rules[rules_key][rules_attrib]

                    if isinstance(against, list):
                        # when the attribute is a list, all items in the list
                        # must match
                        num_matched = 0
                        for i in against:
                            if _check_attrib(val, i, side, rules_attrib):
                                num_matched += 1
                        if (num_matched == len(against)):
                            attributes_matched[rules_key]['matched'] += 1
                    else:
                        if _check_attrib(val, against, side, rules_attrib):
                            attributes_matched[rules_key]['matched'] += 1

        # all the attributes specified in the decl must match the interface
        if 'slot-attributes' in attributes_matched and \
                'plug-attributes' in attributes_matched:
            if attributes_matched['slot-attributes']['len'] == \
                    attributes_matched['slot-attributes']['matched'] and \
                    attributes_matched['plug-attributes']['len'] == \
                    attributes_matched['plug-attributes']['matched']:
                matched = True
        elif 'slot-attributes' in attributes_matched:
            if attributes_matched['slot-attributes']['len'] == \
                    attributes_matched['slot-attributes']['matched']:
                matched = True
        elif 'plug-attributes' in attributes_matched:
            if attributes_matched['plug-attributes']['len'] == \
                    attributes_matched['plug-attributes']['matched']:
                matched = True

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
    def _check_snap_type(self, side, iface, rules, cstr):
        '''Check if there are any matching snap types for this side, interface,
           rules and constraint.
        '''
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

        if checked and ((matched and cstr.startswith('deny')) or
                        (not matched and cstr.startswith('allow'))):
            return (checked, "failed due to %s constraint (snap-type)" % cstr)

        return (checked, None)

    # func checkOnClassic() in helpers.go
    def _check_on_classic(self, side, iface, rules, cstr):
        '''Check if there is a matching on-classic for this side, interface,
           rules and constraint.

           Flag when:
           - installation constraint is specified with on-classic, since it
             will be blocked somewhere
           - a providing (slotting) !core snap on all-snaps system has
             allow/on-classic True or deny/on-classic False with connection
             since it will be blocked on core (we omit core snaps since they
             are blocked for other reasons
           - we ignore plugs with on classic for connections since core snaps
             won't plugs and app snaps will obtain their connection ability
             from the providing (slotting) snap
        '''
        snap_type = 'app'
        if 'type' in self.snap_yaml:
            snap_type = self.snap_yaml['type']
            if snap_type == 'os':
                snap_type = 'core'

        matched = False
        checked = False

        # only worry about on-classic with app snaps
        if snap_type != 'app':
            return (checked, None)

        if "on-classic" in rules:
            checked = True

            if 'installation' in cstr:
                matched = True
            else:
                if side == 'slots' and  \
                        ((cstr.startswith('allow') and rules['on-classic']) or
                         (cstr.startswith('deny') and not rules['on-classic'])):
                    matched = True

        if matched:
            return (checked, "failed due to %s constraint (on-classic)" % cstr)

        return (checked, None)

    # based on, func check*Constraints1() in helpers.go
    def _check_constraints1(self, side, iface, rules, cstr, whence):
        '''Check one constraint

           To avoid superflous manual reviews, we want to limit when we want to
           check to:
           - any installation constraints
           - slotting non-core snap connection constraints
           - plugging snap connection constraints (excepting when not boolean
             in the fallback base declaration slot, since as a practical
             matter, the slotting snap will have been flagged and require a
             snap declaration for snaps to connect to it) no need to check the
             others if we have a toplevel constraint
        '''
        if isinstance(rules, bool):
            # don't flag connection constraints in the base/fallback in
            # plugging snaps
            if side == 'plugs' and 'connection' in cstr and \
                    whence == "base/fallback":
                return None

            if ((rules and cstr.startswith('deny')) or
                    (not rules and cstr.startswith('allow'))):
                return "failed due to %s constraint (bool)" % cstr

            return None

        tmp = []
        num_checked = 0

        (checked, res) = self._check_attributes(side, iface, rules, cstr)
        if checked:
            num_checked += 1
        if res is not None:
            tmp.append(res)

        (checked, res) = self._check_snap_type(side, iface, rules, cstr)
        if checked:
            num_checked += 1
        if res is not None:
            tmp.append(res)

        (checked, res) = self._check_on_classic(side, iface, rules, cstr)
        if checked:
            num_checked += 1
        if res is not None:
            tmp.append(res)

        # NOTE: snapd uses checkDeviceScope() here but we instead apply the
        # scope rules in _get_rules() since we need to still flag when nothing
        # is scoped (ie, base decl is in effect)

        # If multiple constraints are specified, they all must match
        if num_checked > 0 and len(tmp) == num_checked:
            # FIXME: perhaps allow showing more than just the first
            return tmp[0]

        return None

    # func check*Constraints() in helpers.go
    def _check_constraints(self, side, iface, rules, cstr, whence):
        '''Check alternate constraints'''
        if cstr not in rules:
            return None

        firstError = None

        # OR of alternative constraints
        if cstr.startswith('allow'):
            # With allow, the first success is a match and we allow it
            for i in rules[cstr]:
                res = self._check_constraints1(side, iface, i, cstr, whence)
                if res is None:
                    return res

                if firstError is None:
                    firstError = res

            return firstError
        else:
            # With deny, the first failure is a match and we deny it
            for i in rules[cstr]:
                res = self._check_constraints1(side, iface, i, cstr, whence)
                if res is not None:
                    return res

            return None

    def _check_rule(self, side, iface, rules, cstr_type, whence):
        '''Check any constraints for this set of rules'''
        res = self._check_constraints(side, iface, rules,
                                      'deny-%s' % cstr_type, whence)
        if res is not None:
            return res

        res = self._check_constraints(side, iface, rules,
                                      'allow-%s' % cstr_type, whence)
        if res is not None:
            return res

        return None

    # func (ic *Candidate) checkPlug()/checkSlot() from policy.go
    def _check_side(self, side, iface, cstr_type):
        '''Check the set of rules for this side (plugs/slots) for this
           constraint
        '''
        # if the snap declaration has something to say for this constraint,
        # only it is consulted (there is no merging with base declaration)
        snapHasSay = False
        if self.snap_declaration and \
                iface['interface'] in self.snap_declaration[side]:
            for i in ['allow', 'deny']:
                cstr = "%s-%s" % (i, cstr_type)
                if cstr in self.snap_declaration[side][iface['interface']]:
                    snapHasSay = True
                    break

        if snapHasSay:
            (decl, whence) = self._get_decl(side, iface['interface'], True)
            (rules, scoped) = self._get_rules(decl, cstr_type)
            # if we have no scoped rules, then it is as if the snap decl wasn't
            # specified for this constraint
            if scoped and rules is not None:
                return self._check_rule(side, iface, rules, cstr_type, whence)

        (decl, whence) = self._get_decl(side, iface['interface'], False)
        (rules, scoped) = self._get_rules(decl, cstr_type)
        if rules is not None:
            return self._check_rule(side, iface, rules, cstr_type, whence)

        # unreachable: the base declaration will have something for all
        # existing interfaces, and nonexistence tests are done elsewhere
        return None  # pragma: nocover

    # func (ic *InstallCandidate) Check() in policy.go
    def _installation_check(self, side, iname, attribs):
        '''Check for any installation constraints'''
        iface = {}
        if attribs is not None:
            iface = copy.deepcopy(attribs)
        iface['interface'] = iname

        if side == 'slots':
            res = self._check_side('slots', iface, "installation")
            if res is not None:
                return res

        if side == 'plugs':
            res = self._check_side('plugs', iface, "installation")
            if res is not None:
                return res

        return None

    # func (ic *ConnectionCandidate) check() in policy.go
    def _connection_check(self, side, iname, attribs):
        '''Check for any connecttion constraints'''
        iface = {}
        if attribs is not None:
            iface = copy.deepcopy(attribs)
        iface['interface'] = iname

        if side == 'slots':
            res = self._check_side('slots', iface, "connection")
            if res is not None:
                return res

        if side == 'plugs':
            res = self._check_side('plugs', iface, "connection")
            if res is not None:
                return res

        return None

    def _verify_iface(self, name, iface, interface, attribs=None):
        '''Verify the interface for any matching constraints'''
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
        err1 = self._installation_check(side, interface, attribs)
        if err1 is not None:
            t = 'error'
            n = self._get_check_name('%s_installation' % side, app=iface,
                                     extra=interface)
            s = err1
            self._add_result(t, n, s)

        err2 = self._connection_check(side, interface, attribs)
        if err2 is not None:
            t = 'error'
            n = self._get_check_name('%s_connection' % side, app=iface,
                                     extra=interface)
            s = err2
            self._add_result(t, n, s)

        if err1 is None and err2 is None:
            t = 'info'
            n = self._get_check_name('%s' % side, app=iface, extra=interface)
            s = 'OK'
            self._add_result(t, n, s)

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

                self._verify_iface(side[:-1], iface, interface, attribs)

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

                    self._verify_iface('app_%s' % side[:-1], app, ref)
