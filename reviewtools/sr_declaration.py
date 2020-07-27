"""sr_declaration.py: snap declaration"""
#
# Copyright (C) 2014-2020 Canonical Ltd.
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
from reviewtools.sr_common import SnapReview, SnapReviewException
from reviewtools.common import error, ReviewBase, read_snapd_base_declaration
from reviewtools.overrides import sec_iface_ref_overrides
import copy
import re

# Specification for snapd:
# https://docs.google.com/document/d/1QkglVjSzHC65lPthXV3ZlQcqPpKxuGEBL-FMuGP6ogs/edit#
#
# Key terms:
#
# * the "base declaration" declares the policy as shipped in snapd
# * the "snap declaration" declares the optional policy is provided by the
#   store
# * constraints are things like "allow-installation: false" or
#   "deny-connection: true". In this code, we consider "installation" and
#   "connection" as "constraint types"
#
# Rationale for how the review-tools interpret the base and snap declarations
# for when to decide when to trigger a manual review:
#
# * only connection and installation are considered (see _verify_iface()).
#   auto-connection is not considered since snapd mediates the access
# * if the snap declaration has something to say for this constraint type, only
#   it is consulted (there is no merging with base declaration). Specifically,
#   first the snap declaration's plug is examined, then the snap declaration's
#   slot, then the base declaration's plugs, then the base declaration's
#   slots. See snapd specification and _check_side()
#   * specifically, when a snap declaration doesn't have anything to say about
#     a given interface and the base declaration doesn't have anything to say
#     about a given interface, the checks fallback to the "slots" from the base
#     declaration. This is known as the "base/fallback"
# * if the snap declaration specifies one constraint type (eg, "connection"),
#   and another is missing (eg, "installation"), then the missing type uses
#   the constraint type's defaults. The default is "allow". See the snapd
#   specification and _ensure_snap_declaration_defaults()
# * _verify_iface() and the functions it calls loosely follows snapd's
#   algorithm in policy.go where first installation constrainsts are checked,
#   then connection. Since when to trigger for manual review is a different
#   question than how snapd applies the base/snap declarations for a given
#   constraint, the logic here differs.
# * To avoid superflous manual reviews, we want to limit when we want to check
#   to:
#   * any installation constraints
#   * slotting non-core snap connection constraints (ie, a snap providing a
#     service to other snaps via an interface)
#   * plugging snap connection constraints (eg, a snap that plugs dbus to
#     connect to specific slotting snap). We won't flag if the constaint is
#     boolean when falling back to consult the base declaration since the
#     slotting snap will have been flagged and require a snap declaration for
#     snaps to connect to it. See _check_constraints1()
#
# The specific checks are (see _check_constraints1()):
# * _check_names() checks if specified plug-names/slot-names in the snap
#   declaration matches the interface reference
# * _check_attributes() checks if there are any matching attributes in the
#   constraint. Importantly:
#   * if attributes are specified in the constraint, they all must match
#   * if the attribute in the constraint is a list, just one must match (since
#     it is considered a list of alternatives)
#   * don't check slot-attributes with plugs in connection constrains when
#     falling back since the slot's snap declaration will cover this
#   * to promote writing better snap declarations for installation constraints
#     with interface attributes, enforce that both:
#     * the snap uses all the attributes in the snap declaration (as per snapd)
#     * the snap declaration uses all the attributes in the snap (diverges from
#       snapd). We diverge from snapd since there isn't a convenient way to
#       express '<attrib> should not be specified' in the snap declaration
#       syntax so this logic ensures that if a snap adds another attribute at
#       some later point, it is flagged for review
#   * the type of the attribute in the snap declaration means something
#     different than the type in the snap.yaml (see _check_attrib())
# * _check_snap_type() checks if the snap type in the snap matches the snap's
#   type as specified in snap.yaml (defaulting to "app")
# * _check_on_classic() checks "on-classic" for "app" snaps and will flag when:
#   * installation constraint is specified with on-classic, since it will be
#     blocked somewhere
#   * a providing (slotting) non-core snap on an all-snaps system has
#     allow/on-classic True or deny/on-classic False with connection since it
#     will be blocked on core (we omit core snaps since they are blocked for
#     other reasons)
#   Ignore plugs with on classic for connections since core snaps won't plugs
#   and app snaps will obtain their connection ability from the providing
#   (slotting) snap
# * all constraints are automatically scoped to a snap unless "on-store" and/or
#   "on-brand" is specified in the snap declaration. See _check_side() and
#   _ensure_snap_declaration_defaults(). When --on-store or --on-brand is
#   specified to the review-tools:
#   * if the snap declaration constraint specifies "on-store" or "on-brand", it
#     must match --on-store or --on-brand, respectively
#   * if the the snap declaration constraint does not specify "on-store" and/or
#     "on-brand", --on-store and/or --on-brand are ignored (if store behavior
#     changes, this might need revisiting). See _is_scoped()
# * slots-per-plug/plugs-per-slot (aka "Arities") are not considered since they
#   only affect snapd's decision making wrt choosing how many slots/plugs to
#   connect. Note that evaluation rules apply (see above) and so specifying
#   only "allow-connection": {"slots-per-plug": "*"} means that the constraint
#   correctly evaluates to "allow-connection: true". The snap declaration
#   author should take care to replicate the base declaration when doing
#   something like this.


class SnapDeclarationException(SnapReviewException):
    """This class represents SnapDeclaration exceptions"""


class SnapReviewDeclaration(SnapReview):
    """This class represents snap declaration reviews"""

    def __init__(self, fn, overrides=None):
        SnapReview.__init__(self, fn, "declaration-snap-v2", overrides=overrides)

        self._verify_declaration(self.base_declaration, base=True)

        self.on_store = None
        if overrides is not None and "snap_on_store" in overrides:
            if not isinstance(overrides["snap_on_store"], str):
                raise ValueError("'--on-store' should be a str")
            self.on_store = overrides["snap_on_store"]

        self.on_brand = None
        if overrides is not None and "snap_on_brand" in overrides:
            if not isinstance(overrides["snap_on_brand"], str):
                raise ValueError("'--on-brand' should be a str")
            self.on_brand = overrides["snap_on_brand"]

        self.snap_declaration = None
        if overrides is not None and (
            "snap_decl_plugs" in overrides or "snap_decl_slots" in overrides
        ):
            self.snap_declaration = {}
            self.snap_declaration = {"plugs": {}, "slots": {}}
            if "snap_decl_plugs" in overrides:
                self.snap_declaration["plugs"] = overrides["snap_decl_plugs"]
            if "snap_decl_slots" in overrides:
                self.snap_declaration["slots"] = overrides["snap_decl_slots"]

            self._verify_declaration(self.snap_declaration, base=False)

            # do this after the verify since _verify_declaration() calls
            # _add_result() and we don't want that for our defaults
            self._ensure_snap_declaration_defaults()

    def _ensure_snap_declaration_defaults(self):
        """Ensure defaults are set for non-present keys in the snap
           declaration.
        """
        if self.snap_declaration is None:
            return

        # https://bugs.launchpad.net/review-tools/+bug/1864103
        #
        # Historically we've said "if we have no scoped rules, then it is as if
        # the snap decl wasn't specified for this constraint". However, we
        # really need to say is for a particular interface and in all the
        # cstr_types (ie, installation, connection, auto-connection):
        #
        #  * if there are no scoped rules or unscoped rules in the snap decl,
        #    use the base decl
        #  * if we have scoped rules in the snap decl for any cstr_types, use
        #    those and defaults for the missing cstr_types
        #  * if we have no scoped rules but have unscoped rules, use unscoped
        #    rules and defaults for missing cstr_types
        #
        # In practical terms, this means that an interface in the base decl
        # that has an installation constraint and slot side connection
        # constraint (ie, two things that could cause an manual review), only
        # needs only one in the snap decl to pass automated review.
        #
        # Considering the above, we can reduce this to simply: "if the snap
        # declaration for this interface has any cstr_type, use it and use
        # defaults for any missing cstr_types).

        cstr_types = ["installation", "connection", "auto-connection"]

        for side in ["plugs", "slots"]:
            if side in self.snap_declaration:
                for iface in self.snap_declaration[side]:
                    missing = []
                    for cstr_type in cstr_types:
                        found = False
                        for t in ["allow", "deny"]:
                            key = "%s-%s" % (t, cstr_type)
                            if key in self.snap_declaration[side][iface]:
                                found = True
                                break
                        if not found:
                            missing.append(cstr_type)

                    # As a special case, we don't add defaults if
                    # self.snap_declaration[side][iface] didn't have anything
                    # to say about any cstr_types
                    if len(missing) < len(cstr_types):
                        for cstr in missing:
                            dkey = "allow-%s" % cstr
                            self.snap_declaration[side][iface][dkey] = True

    def _verify_declaration(self, decl, base=False):
        """Verify declaration"""

        def is_bool(item):
            if isinstance(item, int) and (item is True or item is False):
                return True
            return False

        def str2bool(s):
            if s == "true" or s == "True":
                return True
            if s == "false" or s == "False":
                return False
            return s

        def malformed(name, s, base=False):
            pre = ""
            if base:
                pre = "base "
            err = "%sdeclaration malformed (%s)" % (pre, s)
            if base:
                raise SnapDeclarationException(err)
            self._add_result("error", name, err)

        def verify_constraint(cstr, decl, key, iface, index, allowed, has_alternates):
            found_errors = False
            if is_bool(cstr):
                if not base:
                    self._add_result("info", n, s)
                return False
            elif not isinstance(cstr, dict):
                malformed(n, "%s not True, False or dict" % constraint, base)
                return False

            for cstr_key in cstr:
                if cstr_key not in allowed:
                    name = self._get_check_name(
                        "valid_%s" % key,
                        app=iface,
                        extra="%s_%s" % (constraint, cstr_key),
                    )
                    malformed(name, "unknown constraint key '%s'" % cstr_key, base)
                    found_errors = True

            if found_errors:
                return False

            cstr_bools = ["on-classic"]
            cstr_lists = [
                "plug-snap-type",
                "slot-snap-type",
                "plug-publisher-id" "slot-publisher-id",
                "plug-snap-id",
                "slot-snap-id",
                "on-store",
                "on-brand",
                "plug-names",  # https://forum.snapcraft.io/t/plug-slot-rules-plug-names-slot-names-constraints/12439
                "slot-names",
            ]
            cstr_dicts = ["plug-attributes", "slot-attributes"]
            cstr_strs = ["plugs-per-slot", "slots-per-plug"]
            for cstr_key in cstr:
                badn = self._get_check_name(
                    "valid_%s" % key, app=iface, extra="%s_%s" % (constraint, cstr_key)
                )
                if cstr_key in cstr_bools:
                    # snap declarations from the store express bools as
                    # strings
                    if isinstance(cstr[cstr_key], str):
                        cstr[cstr_key] = str2bool(cstr[cstr_key])
                        if has_alternates:
                            decl[key][iface][constraint][index][cstr_key] = str2bool(
                                decl[key][iface][constraint][index][cstr_key]
                            )
                    if not is_bool(cstr[cstr_key]):
                        malformed(badn, "'%s' not True or False" % cstr_key, base)
                        found_errors = True
                elif cstr_key in cstr_strs:
                    if not isinstance(cstr[cstr_key], str):
                        malformed(badn, "'%s' not a str" % cstr_key, base)
                        found_errors = True
                elif cstr_key in cstr_lists:
                    if not isinstance(cstr[cstr_key], list):
                        malformed(badn, "'%s' not a list" % cstr_key, base)
                        found_errors = True
                    else:
                        for entry in cstr[cstr_key]:
                            if not isinstance(entry, str):
                                malformed(
                                    badn,
                                    "'%s' in '%s' not a string" % (entry, cstr_key),
                                    base,
                                )
                                found_errors = True
                elif cstr_key in cstr_dicts:
                    if not isinstance(cstr[cstr_key], dict):
                        malformed(badn, "'%s' not a dict" % cstr_key, base)
                        found_errors = True
                    else:
                        for attrib in cstr[cstr_key]:
                            bn = self._get_check_name(
                                "valid_%s" % key,
                                app=iface,
                                extra="%s_%s" % (constraint, cstr_key),
                            )
                            if iface not in self.interfaces_attribs:
                                malformed(bn, "unknown attribute '%s'" % attrib, base)
                                found_errors = True
                                continue

                            found_iface_attr = False
                            for tmp in self.interfaces_attribs[iface]:
                                known, side = tmp.split("/")
                                if attrib != known:
                                    continue
                                spec_side = side[:-1]

                                if cstr_key.startswith(spec_side):
                                    found_iface_attr = True

                                # snap declarations from the store express
                                # bools as strings
                                if isinstance(cstr[cstr_key][attrib], str):
                                    cstr[cstr_key][attrib] = str2bool(
                                        cstr[cstr_key][attrib]
                                    )
                                    if has_alternates:
                                        decl[key][iface][constraint][index][cstr_key][
                                            attrib
                                        ] = str2bool(
                                            decl[key][iface][constraint][index][
                                                cstr_key
                                            ][attrib]
                                        )

                                attr_type = cstr[cstr_key][attrib]

                                # Mark as malformed if the attribute type in
                                # the decl is different from that defined in
                                # sr_common.py, except when that in
                                # sr_common.py is a list and the decl specifies
                                # a string (since in the decl one can specify a
                                # string as a match/regex for something in the
                                # list)
                                if not isinstance(
                                    attr_type, type(self.interfaces_attribs[iface][tmp])
                                ) and not (
                                    isinstance(
                                        self.interfaces_attribs[iface][tmp], list
                                    )
                                    and isinstance(attr_type, str)
                                ):
                                    malformed(
                                        bn,
                                        "wrong type '%s' for attribute '%s'"
                                        % (attr_type, attrib),
                                        base,
                                    )
                                    found_errors = True
                                    break

                            if not found_iface_attr:
                                malformed(
                                    bn,
                                    "attribute '%s' wrong for '%ss'"
                                    % (attrib, cstr_key[:4]),
                                    base,
                                )
                                found_errors = True

                if not found_errors and (
                    cstr_key == "plug-publisher-id" or cstr_key == "slot-publisher-id"
                ):
                    for pubid in cstr[cstr_key]:
                        if not pub_pat.search(pubid):
                            malformed(n, "invalid format for publisher id '%s'" % pubid)
                            found_errors = True
                            break
                        if pubid.startswith("$"):
                            if (
                                cstr_key == "plug-publisher-id"
                                and pubid != "$SLOT_PUBLISHER_ID"
                            ):
                                malformed(n, "invalid publisher id '%s'" % pubid)
                                found_errors = True
                                break
                            elif (
                                cstr_key == "slot-publisher-id"
                                and pubid != "$PLUG_PUBLISHER_ID"
                            ):
                                malformed(n, "invalid publisher id '%s'" % pubid)
                                found_errors = True
                                break
                elif not found_errors and (
                    cstr_key == "plug-snap-id" or cstr_key == "slot-snap-id"
                ):
                    for id in cstr[cstr_key]:
                        if not id_pat.search(id):
                            malformed(n, "invalid format for snap id '%s'" % id)
                            found_errors = True
                            break
                elif not found_errors and (
                    cstr_key == "plug-snap-type" or cstr_key == "slot-snap-type"
                ):
                    for snap_type in cstr[cstr_key]:
                        if snap_type not in self.valid_snap_types:
                            malformed(n, "invalid snap type '%s'" % snap_type)
                            found_errors = True
                            break
                elif not found_errors and (
                    cstr_key == "slots-per-plug" or cstr_key == "plugs-per-slot"
                ):
                    # see asserts/ifacedecls.go
                    if not re.search(r"^(\*|[1-9][0-9]*)$", cstr[cstr_key]):
                        malformed(
                            n,
                            "invalid format for '%s': %s"
                            % (cstr[cstr_key], cstr[cstr_key]),
                        )
                        found_errors = True
                        break

                    if cstr_key == "plugs-per-slot":
                        # snapd ignores setting plugs-per-slot, so warn
                        self._add_result("warn", n, "%s not supported yet" % cstr_key)
                    elif cstr[cstr_key] != "*":
                        # snapd ignores other values than '*', so warn
                        self._add_result(
                            "warn", n, "%s currently only supports '*'" % cstr_key
                        )

            return not found_errors
            # end verify_constraint()

        # from snapd.git/assers/ifacedecls.go
        id_pat = re.compile(r"^[a-z0-9A-Z]{32}$")
        pub_pat = re.compile(r"^(?:[a-z0-9A-Z]{32}|[-a-z0-9]{2,28}|\$[A-Z][A-Z0-9_]*)$")

        if not isinstance(decl, dict):
            malformed(self._get_check_name("valid_dict"), "not a dict", base)
            return
        elif len(decl) == 0:
            malformed(self._get_check_name("valid_dict"), "empty", base)
            return

        for key in decl:
            if key not in ["plugs", "slots"]:
                malformed(
                    self._get_check_name("valid_key"), "unknown key '%s'" % key, base
                )
                return

            if not isinstance(decl[key], dict):
                malformed(
                    self._get_check_name("valid_dict", app=key), "not a dict", base
                )
                return

            for iface in decl[key]:
                # snap declarations from the store express bools as strings
                if isinstance(decl[key][iface], str):
                    decl[key][iface] = str2bool(decl[key][iface])
                # iface may be bool or dict
                if is_bool(decl[key][iface]):
                    n = self._get_check_name("valid_%s_bool" % key, app=iface)
                    self._add_result("info", n, "OK")
                    continue
                elif not isinstance(decl[key][iface], dict):
                    malformed(
                        self._get_check_name("valid_%s_dict" % key, app=iface),
                        "interface not True, False or dict",
                        base,
                    )
                    continue

                for constraint in decl[key][iface]:
                    # snap declarations from the store express bools as strings
                    if isinstance(decl[key][iface][constraint], str):
                        decl[key][iface][constraint] = str2bool(
                            decl[key][iface][constraint]
                        )

                    t = "info"
                    n = self._get_check_name(
                        "valid_%s" % key, app=iface, extra=constraint
                    )
                    s = "OK"
                    cstr = decl[key][iface][constraint]

                    allowed_ctrs = [
                        "allow-installation",
                        "deny-installation",
                        "allow-connection",
                        "allow-auto-connection",
                        "deny-connection",
                        "deny-auto-connection",
                    ]
                    if constraint not in allowed_ctrs:
                        malformed(n, "unknown constraint '%s'" % constraint, base)
                        continue

                    allowed = []
                    if constraint.endswith("-installation"):
                        allowed = ["on-classic", "on-store", "on-brand"]
                        if key == "plugs":
                            allowed.append("plug-snap-type")
                            allowed.append("plug-attributes")
                            allowed.append("plug-names")
                        elif key == "slots":
                            allowed.append("slot-snap-type")
                            allowed.append("slot-attributes")
                            allowed.append("slot-names")
                    else:
                        allowed = [
                            "plug-attributes",
                            "slot-attributes",
                            "on-classic",
                            "on-store",
                            "on-brand",
                        ]
                        if key == "plugs":
                            allowed.append("slot-publisher-id")
                            allowed.append("slot-snap-id")
                            allowed.append("slot-snap-type")
                            allowed.append("plug-names")
                        elif key == "slots":
                            allowed.append("plug-publisher-id")
                            allowed.append("plug-snap-id")
                            allowed.append("plug-snap-type")
                            allowed.append("slot-names")

                        # These may be slot or plug, but not installation
                        # or deny-*. Ie, only allow-(auto-)connection
                        # https://forum.snapcraft.io/t/plug-slot-declaration-rules-greedy-plugs/12438
                        if constraint.startswith("allow"):
                            allowed.append("slots-per-plug")
                            allowed.append("plugs-per-slot")

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
                        if not verify_constraint(
                            alt, decl, key, iface, index, allowed, (len(alternates) > 1)
                        ):
                            found_errors = True
                        index += 1

                    if not base and not found_errors:
                        self._add_result(t, n, s)

    def _get_decl(self, side, iface, snapDecl):
        """Obtain the declaration for the interface. When snapDecl is False,
           get the base declaration, falling back to slots as needed.
           Returns (found decl, [snap|base]/[<side>|fallback])
        """
        if snapDecl:
            if iface in self.snap_declaration[side]:
                return (
                    copy.deepcopy(self.snap_declaration[side][iface]),
                    "snap/%s" % side,
                )
            else:
                return (None, None)

        if iface in self.base_declaration[side]:
            return (copy.deepcopy(self.base_declaration[side][iface]), "base/%s" % side)
        elif iface in self.base_declaration["slots"]:
            # Fallback to slots in the base declaration if nothing is in plugs
            return (
                copy.deepcopy(self.base_declaration["slots"][iface]),
                "base/fallback",
            )

        return (None, None)

    def _is_scoped(self, rules):
        """Return whether or not the specified rules are scoped to the snap as
           dictated by the --on-store and --on-brand overrides
        """
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
            if (
                self.on_store in rules["on-store"]
                and self.on_brand in rules["on-brand"]
            ):
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
        """Obtain the rules, if any, from the specified decl for this
           constraint type (eg, 'connection' or 'installation').
        """
        scoped = True
        rules = {}

        if decl is None:
            return rules, False
        elif "allow-%s" % cstr_type not in decl and "deny-%s" % cstr_type not in decl:
            return rules, False

        for i in ["allow", "deny"]:
            cstr = "%s-%s" % (i, cstr_type)
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

    # func checkNameConstraints() in interfaces/policy/helpers.go and
    # func compileNameConstraints() in asserts/ifacedecls.go
    def _check_names(self, side, iref, iface, rules, cstr):
        """Check if there are any matching names for this side, interface,
           rules and constraint. A matching name consists of:
           - the interface reference (iref) matches a list entry regex
           - the interface reference (iref) matches the interface name
             when the list entry is $INTERFACE
        """
        matched = False
        checked = False
        for rules_key in rules:
            if not rules_key == "%s-names" % side[:-1]:
                continue
            checked = True

            for matcher in rules[rules_key]:
                if matcher.startswith("$"):
                    if matcher == "$INTERFACE":
                        if "interface" in iface and iref == iface["interface"]:
                            matched = True
                    else:
                        raise SnapDeclarationException(
                            "unknown special name '%s'" % matcher
                        )
                elif re.search(r"^(%s)$" % matcher, iref):
                    matched = True

        if checked and (
            (matched and cstr.startswith("deny"))
            or (not matched and cstr.startswith("allow"))
        ):
            return (
                checked,
                "human review required due to '%s' constraint (%s)" % (cstr, rules_key),
            )

        return (checked, None)

    def _check_attributes(self, side, iface, rules, cstr, whence):
        """Check if there are any matching attributes for this side, interface,
           rules and constraint.
        """

        def _check_attrib(val, against, side, rules_attrib):
            # val = iface[rules_attrib]
            # against = rules[rules_key][rules_attrib]

            if type(val) not in [str, list, dict, bool]:
                raise SnapDeclarationException("unknown type '%s'" % val)

            # Keep in mind by this point each OR constraint is being iterated
            # through such that 'against' as a list is a nested list.
            # For now, punt on nested lists since they are impractical in use
            # since they are a list of OR options where one option must match
            # all of val, but if you have that you may as well just use a
            # string. Eg for this snap.yaml:
            #   snap.yaml:
            #     plugs:
            #       foo:
            #         bar: [ baz, norf ]
            #
            # a snap decl that uses a list for 'bar' might be:
            #   snap decl:
            #     foo:
            #       plug-attributes:
            #         bar:
            #         - baz|norf
            #         - something|else
            #
            # but, 'something|else' is pointless so it will never match, so the
            # decl should be rewritten more simply as:
            #   snap decl:
            #     foo:
            #       plug-attributes:
            #         bar: baz|norf
            # Importantly, the type of the attribute in the snap decl means
            # something different than the type in snap.yaml
            if isinstance(against, list):
                raise SnapDeclarationException(
                    "attribute lists in the declaration not supported"
                )

            matched = False
            if isinstance(val, str) and isinstance(against, str):
                if against.startswith("$"):
                    if against == "$MISSING":
                        matched = False  # value must not be set
                    elif re.search(r"^\$PLUG\(%s\)$" % rules_attrib, against):
                        matched = True
                    elif re.search(r"^\$SLOT\(%s\)$" % rules_attrib, against):
                        matched = True
                    else:
                        raise SnapDeclarationException(
                            "unknown special attrib '%s'" % against
                        )
                elif re.search(r"^(%s)$" % against, val):
                    matched = True
            elif isinstance(val, list):
                # if the attribute in the snap (val) is a list and the
                # declaration value (against) is a string, then to match,
                # against must be a regex that matches all entries in val
                num_matched = 0
                for i in val:
                    if _check_attrib(i, against, side, rules_attrib):
                        num_matched += 1
                if num_matched == len(val):
                    matched = True
            else:  # bools and dicts (TODO: nested matches for dicts)
                matched = against == val

            return matched

        # If attributes are specified in the constraint, they all must match.
        matched = False
        checked = False
        attributes_matched = {}

        for rules_key in rules:
            if rules_key not in ["slot-attributes", "plug-attributes"]:
                continue
            elif len(rules[rules_key]) == 0:  # if empty, then just ignore
                continue
            elif (
                side == "plugs"
                and "connection" in cstr
                and rules_key == "slot-attributes"
                and whence == "base/fallback"
            ):
                # As a practical matter, don't flag connection constraints for
                # slot-attributes in plugging snaps when checking against the
                # fallback base declaration slot since the slotting snap will
                # have been flagged and require a snap declaration for snaps to
                # connect to it
                continue
            elif "installation" in cstr and "snap" in whence:
                # snapd itself applies the snap declaration to regulate
                # installation and connection. snapd does not require that the
                # snap only has the specified attributes in the snap decl. Eg,
                # if snap has:
                #
                #   plugs:
                #     iface-foo:
                #       interface: foo
                #       bar: blah
                #       baz: blahblah
                #
                # and the snap declaration has only:
                #
                #   plugs:
                #     foo:
                #       allow-installation:
                #         plug-attributes:
                #           bar: blah
                #
                # then 'baz' is not considered (since the snap declaration
                # declares what must match). This is convenient for interfaces
                # like content or dbus which have many attributes but we only
                # want to regulate one. snapd does enforce that if the
                # attribute is in the declaration, they cannot be missing from
                # the snap.
                #
                # To promote writing better snap declarations for installation
                # constraints with interface attributes, not only do we enforce
                # that the snap uses all the attributes in the snap declaration
                # (see above), we also diverge from snapd and require that all
                # specified attributes in the snap are also in the snap
                # declaration. Since there isn't a convenient way to express
                # '<attrib> should not be specified' in the snap declaration
                # syntax, this logic ensures that if a snap adds another
                # attribute at some later point, it is flagged for review.

                # Quick check: ensure that if the snap declaration specified
                # attributes that the interface also specifies attributes (the
                # matching logic, below, will ensure that everything matches).
                if len(iface) == 1 and len(rules[rules_key]) > 0:
                    checked = True
                    continue

                # Make sure nothing from the snap is missing from the snap
                # declaration.
                missing = False
                for i in iface:
                    if i != "interface" and i not in rules[rules_key]:
                        missing = True
                        break
                if missing:
                    checked = True
                    continue

            attributes_matched[rules_key] = {}
            attributes_matched[rules_key]["len"] = len(rules[rules_key])
            attributes_matched[rules_key]["matched"] = 0
            for rules_attrib in rules[rules_key]:
                if rules_attrib in iface:
                    checked = True
                    val = iface[rules_attrib]
                    against = rules[rules_key][rules_attrib]

                    if isinstance(against, list):
                        # As a practical matter, if the attribute in the
                        # constraint is a list, just one must match (it is
                        # considered a list of alternatives, aka, a list of
                        # OR constraints).
                        for i in against:
                            if _check_attrib(val, i, side, rules_attrib):
                                attributes_matched[rules_key]["matched"] += 1
                                break
                    else:
                        if _check_attrib(val, against, side, rules_attrib):
                            attributes_matched[rules_key]["matched"] += 1
                else:
                    # when the attribute is missing from the interface don't
                    # mark as checked (missing attributes are checked
                    # elsewwhere in 'interfaces_required' from sr_common.py in
                    # sr_lint.py
                    pass

        # all the attributes specified in the decl must match the interface
        if (
            "slot-attributes" in attributes_matched
            and "plug-attributes" in attributes_matched
        ):
            if (
                attributes_matched["slot-attributes"]["len"]
                == attributes_matched["slot-attributes"]["matched"]
                and attributes_matched["plug-attributes"]["len"]
                == attributes_matched["plug-attributes"]["matched"]
            ):
                matched = True
        elif "slot-attributes" in attributes_matched:
            if (
                attributes_matched["slot-attributes"]["len"]
                == attributes_matched["slot-attributes"]["matched"]
            ):
                matched = True
        elif "plug-attributes" in attributes_matched:
            if (
                attributes_matched["plug-attributes"]["len"]
                == attributes_matched["plug-attributes"]["matched"]
            ):
                matched = True

        if checked and (
            (matched and cstr.startswith("deny"))
            or (not matched and cstr.startswith("allow"))
        ):
            s = (
                "human review required due to '%s' constraint (interface attributes)"
                % cstr
            )
            if (
                "plug-attributes" in rules
                and "allow-sandbox" in rules["plug-attributes"]
                and rules["plug-attributes"]["allow-sandbox"]
            ):
                # old Oxide is OXIDE_NO_SANDBOX=1
                s += (
                    ". If using a chromium webview, you can disable the "
                    + "internal sandbox (eg, use --no-sandbox) and remove "
                    + "the 'allow-sandbox' attribute instead. For "
                    + "QtWebEngine webviews, export "
                    + "QTWEBENGINE_DISABLE_SANDBOX=1 to disable its "
                    + "internal sandbox."
                )
            return (checked, s)

        return (checked, None)

    # func checkSnapType() in interfaces/policy/helpers.go
    def _check_snap_type(self, side, iface, rules, cstr):
        """Check if there are any matching snap types for this side, interface,
           rules and constraint.
        """
        snap_type = "app"
        if "type" in self.snap_yaml:
            snap_type = self.snap_yaml["type"]
            if snap_type == "os":
                snap_type = "core"

        matched = False
        checked = False
        for rules_key in rules:
            if not rules_key == "%s-snap-type" % side[:-1]:
                continue
            checked = True

            if snap_type in rules[rules_key]:
                matched = True

        if checked and (
            (matched and cstr.startswith("deny"))
            or (not matched and cstr.startswith("allow"))
        ):
            return (
                checked,
                "human review required due to '%s' constraint (snap-type)" % cstr,
            )

        return (checked, None)

    # func checkOnClassic() in interfaces/policy/helpers.go
    def _check_on_classic(self, side, iface, rules, cstr):
        """Check if there is a matching on-classic for this side, interface,
           rules and constraint.
        """
        snap_type = "app"
        if "type" in self.snap_yaml:
            snap_type = self.snap_yaml["type"]
            if snap_type == "os":
                snap_type = "core"

        matched = False
        checked = False

        # only worry about on-classic with app snaps
        if snap_type != "app":
            return (checked, None)

        if "on-classic" in rules:
            checked = True

            if "installation" in cstr:
                # If installation is specified with on-classic, it might be
                # blocked somewhere, so always consider it.
                matched = True
            else:
                # Note: we ignore plugs for connections since core snaps won't
                # plugs and app snaps will obtain their connection ability
                # from the providing (slotting) snap
                if side == "slots" and (
                    (cstr.startswith("allow") and rules["on-classic"])
                    or (cstr.startswith("deny") and not rules["on-classic"])
                ):
                    # A snap that slots with a connection constraint might
                    # be blocked on all-snaps systems, so consider it too.
                    matched = True

        if matched:
            return (
                checked,
                "human review required due to '%s' constraint (on-classic)" % cstr,
            )

        return (checked, None)

    # based on, func check*Constraints1() in interfaces/policy/helpers.go
    def _check_constraints1(self, side, iref, iface, rules, cstr, whence):
        """Check one constraint"""
        if isinstance(rules, bool):
            # Don't flag connection constraints in the base/fallback in
            # plugging snaps when the constraint is boolean. Normally the
            # slotting snap will have been flagged and require a snap
            # declaration for snaps to connect to it, so don't worry about
            # checking the plugging snap in this scenario.
            if side == "plugs" and "connection" in cstr and whence == "base/fallback":
                return None

            if (rules and cstr.startswith("deny")) or (
                not rules and cstr.startswith("allow")
            ):
                return "human review required due to '%s' constraint (bool)" % cstr

            return None

        tmp = []
        num_checked = 0

        (checked, res) = self._check_names(side, iref, iface, rules, cstr)
        if checked:
            num_checked += 1
        if res is not None:
            tmp.append(res)

        (checked, res) = self._check_attributes(side, iface, rules, cstr, whence)
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

        # NOTE: Arities (ie, slots-per-plug and plugs-per-slot) only affect
        # snapd's decision making wrt choosing how many slots/plugs to connect
        # and thus have no bearing on whether we should flag for manual review
        # or not (though, like any other constraint, their presence in the snap
        # declaration means that only the snap declaration for that constraint
        # is used due to evaluation rules). Ie, this in the snap declaration:
        #
        #   allow-connection:
        #   - slots-per-plug: *
        #
        # correctly evaluates to: allow-connection: true

        # When we have scoped snap decl rules ('snap' in whence) for a deny
        # constraint but had no matching checks, then treat the scoped rule
        # as a bool.
        if "snap" in whence and num_checked == 0 and cstr.startswith("deny"):
            return "human review required due to '%s' constraint (scoped bool)" % cstr

        # If multiple constraints are specified, they all must match.
        # Specifically, since tmp contains the error strings for this
        # alternation, when checks were performed we return an error if:
        # - at least one check errored with 'allow' since not fully matching
        #   the allow means means we should display an error (not allowed)
        # - all checks errored with 'deny' since not fully matching the
        #   deny means we should pass (allowed)
        if num_checked > 0 and (
            (cstr.startswith("deny") and len(tmp) == num_checked)
            or (cstr.startswith("allow") and len(tmp) > 0)
        ):
            # FIXME: perhaps allow showing more than just the first
            return tmp[0]

        return None

    # func check*Constraints() in interfaces/policy/helpers.go
    def _check_constraints(self, side, iref, iface, rules, cstr, whence):
        """Check alternate constraints"""
        if cstr not in rules:
            return None

        firstError = None

        # OR of alternative constraints
        if cstr.startswith("allow"):
            # With allow, the first success is a match and we allow it
            for i in rules[cstr]:
                res = self._check_constraints1(side, iref, iface, i, cstr, whence)
                if res is None:
                    return res

                if firstError is None:
                    firstError = res

            return firstError
        else:
            # With deny, the first failure is a match and we deny it
            for i in rules[cstr]:
                res = self._check_constraints1(side, iref, iface, i, cstr, whence)
                if res is not None:
                    return res

            return None

    def _check_rule(self, side, iref, iface, rules, cstr_type, whence):
        """Check any constraints for this set of rules"""
        res = self._check_constraints(
            side, iref, iface, rules, "deny-%s" % cstr_type, whence
        )
        if res is not None:
            return res

        res = self._check_constraints(
            side, iref, iface, rules, "allow-%s" % cstr_type, whence
        )
        if res is not None:
            return res

        return None

    # func (ic *Candidate) checkPlug()/checkSlot() from interfaces/policy/policy.go
    def _check_side(self, side, iref, iface, cstr_type):
        """Check the set of rules for this side (plugs/slots) for this
           constraint
        """
        # if the snap declaration has something to say for this constraint,
        # only it is consulted (there is no merging with base declaration)
        snapHasSay = False
        if self.snap_declaration and iface["interface"] in self.snap_declaration[side]:
            for i in ["allow", "deny"]:
                cstr = "%s-%s" % (i, cstr_type)
                if cstr in self.snap_declaration[side][iface["interface"]]:
                    snapHasSay = True
                    break

        if snapHasSay:
            (decl, whence) = self._get_decl(side, iface["interface"], True)
            (rules, scoped) = self._get_rules(decl, cstr_type)
            # The snap declaration can only have a say if its rules are scoped
            # to the snap. If we have no scoped rules, then it is as if the
            # snap decl wasn't specified for this constraint
            if scoped and rules is not None:
                return self._check_rule(side, iref, iface, rules, cstr_type, whence)

        (decl, whence) = self._get_decl(side, iface["interface"], False)
        (rules, scoped) = self._get_rules(decl, cstr_type)
        if rules is not None:
            return self._check_rule(side, iref, iface, rules, cstr_type, whence)

        # unreachable: the base declaration will have something for all
        # existing interfaces, and nonexistence tests are done elsewhere
        return None  # pragma: nocover

    # func (ic *InstallCandidate) Check() in interfaces/policy/policy.go
    def _installation_check(self, side, iref, iname, attribs):
        """Check for any installation constraints"""
        iface = {}
        if attribs is not None:
            iface = copy.deepcopy(attribs)
        iface["interface"] = iname

        if side == "slots":
            res = self._check_side("slots", iref, iface, "installation")
            if res is not None:
                return res

        if side == "plugs":
            res = self._check_side("plugs", iref, iface, "installation")
            if res is not None:
                return res

        return None

    # func (ic *ConnectionCandidate) check() in policy.go
    def _connection_check(self, side, iref, iname, attribs):
        """Check for any connecttion constraints"""
        iface = {}
        if attribs is not None:
            iface = copy.deepcopy(attribs)
        iface["interface"] = iname

        if side == "slots":
            res = self._check_side("slots", iref, iface, "connection")
            if res is not None:
                return res

        if side == "plugs":
            res = self._check_side("plugs", iref, iface, "connection")
            if res is not None:
                return res

        return None

    def _verify_iface(self, name, iface, interface, attribs=None):
        """Verify the interface for any matching constraints"""
        if name.endswith("slot"):
            side = "slots"
            oside = "plugs"
        elif name.endswith("plug"):
            side = "plugs"
            oside = "slots"

        # If it is an interface reference used by an app, skip since it will be
        # checked in top-level interface checks.
        if (
            (name.startswith("app_") or name.startswith("hook_"))
            and side in self.snap_yaml
            and interface in self.snap_yaml[side]
        ):
            return

        t = "info"
        n = self._get_check_name("%s_known" % name, app=iface, extra=interface)
        s = "OK"
        if (
            side in self.base_declaration
            and interface not in self.base_declaration[side]
            and oside in self.base_declaration
            and interface not in self.base_declaration[oside]
        ):
            t = "error"
            s = "interface '%s' not found in base declaration" % interface
            self._add_result(t, n, s)
            return

        # only need to check installation and connection since snapd handles
        # auto-connection
        err1 = self._installation_check(side, iface, interface, attribs)
        if err1 is not None:
            t = "error"
            n = self._get_check_name(
                "%s_installation" % side, app=iface, extra=interface
            )
            s = err1
            self._add_result(t, n, s, manual_review=True)

        err2 = self._connection_check(side, iface, interface, attribs)
        if err2 is not None:
            t = "error"
            n = self._get_check_name("%s_connection" % side, app=iface, extra=interface)
            s = err2
            self._add_result(t, n, s, manual_review=True)

        if err1 is None and err2 is None:
            t = "info"
            n = self._get_check_name("%s" % side, app=iface, extra=interface)
            s = "OK"
            self._add_result(t, n, s)

    def check_declaration(self):
        """Check base/snap declaration requires manual review for top-level
           plugs/slots
        """
        for side in ["plugs", "slots"]:
            if side not in self.snap_yaml:
                continue

            for iface in self.snap_yaml[side]:
                # If the 'interface' name is the same as the 'plug/slot' name,
                # then 'interface' is optional since the interface name and the
                # plug/slot name are the same
                interface = iface
                attribs = None

                spec = copy.deepcopy(self.snap_yaml[side][iface])
                if isinstance(spec, str):
                    # Abbreviated syntax (no attributes)
                    # <plugs|slots>:
                    #   <alias>: <interface>
                    interface = spec
                elif isinstance(spec, dict):
                    # Full specification.
                    # <plugs|slots>:
                    #   <alias>:
                    #     interface: <interface>
                    #     attrib: ...
                    #
                    # or
                    # <plugs|slots>:
                    #   <interface>:
                    #     attrib: ...
                    if "interface" in spec:
                        interface = spec["interface"]
                        if len(spec) > 1:
                            attribs = spec
                            del attribs["interface"]
                    elif len(spec) > 0:
                        attribs = spec
                else:  # this is checked elsewhere, so just avoid a traceback
                    # coverage doesn't detect without this o_O
                    continue  # pragma: nocover

                self._verify_iface(side[:-1], iface, interface, attribs)

    def _verify_declaration_apps_hooks(self, key):
        """Verify declaration for apps and hooks"""
        if key not in self.snap_yaml:
            return

        for app in self.snap_yaml[key]:
            for side in ["plugs", "slots"]:
                if side not in self.snap_yaml[key][app]:
                    continue

                # The interface referenced in the app's 'plugs' or 'slots'
                # field can either be a known interface (when the interface
                # name reference and the interface is the same) or can
                # reference a name in the snap's toplevel 'plugs' or 'slots'
                # mapping
                for ref in self.snap_yaml[key][app][side]:
                    if not isinstance(ref, str):
                        continue  # checked elsewhere

                    self._verify_iface("%s_%s" % (key[:-1], side[:-1]), app, ref)

    def check_declaration_apps(self):
        """Check base/snap declaration requires manual review for apps
           plugs/slots
        """
        self._verify_declaration_apps_hooks("apps")

    def check_declaration_hooks(self):
        """Check base/snap declaration requires manual review for hooks
           plugs/slots
        """
        self._verify_declaration_apps_hooks("hooks")

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
            elif (
                "interface" in self.snap_yaml[side][ref]
                and self.snap_yaml[side][ref]["interface"] == interface
            ):
                refname = ref
            if refname is None:
                continue  # nothing to check

            t = "info"
            n = self._get_check_name(
                "interface-reference", app=refname, extra=interface
            )
            s = "OK"
            if self.snap_yaml["name"] not in sec_iface_ref_overrides[interface]:
                t = "warn"
                s = (
                    "override not found for '%s/%s'. " % (side, refname)
                    + "Use of the %s interface is reserved for " % interface
                    + "vetted publishers. If your snap legitimately "
                    + "requires this access, please make a request in "
                    + "the forum using the 'store-requests' category ("
                    + "https://forum.snapcraft.io/c/store-requests), or if "
                    + "you would prefer to keep this private, the 'sensitive' "
                    + "category."
                )
                self._add_result(t, n, s)
            elif (
                refname
                not in sec_iface_ref_overrides[interface][self.snap_yaml["name"]]
            ):
                t = "error"
                s = (
                    "interface reference '%s' not allowed. " % refname
                    + "Please use one of: %s"
                    % ", ".join(
                        sec_iface_ref_overrides[interface][self.snap_yaml["name"]]
                    )
                )
            self._add_result(t, n, s)

    def check_personal_files_iface_reference(self):
        """Check personal-files interface references"""
        self._allowed_iface_reference("plugs", "personal-files")

    def check_system_files_iface_reference(self):
        """Check system-files interface references"""
        self._allowed_iface_reference("plugs", "system-files")


#
# Helper functions
#
def verify_snap_declaration(snap_decl, base_decl=None):
    """Perform a review on the snap declaration. Returns a Review object"""
    review = ReviewBase("snap-declaration-verify_v2")

    # Setup everything needed by _verify_declaration()
    review.interfaces_attribs = SnapReview.interfaces_attribs
    review.valid_snap_types = SnapReview.valid_snap_types

    # Read in and verify the base declaration
    if base_decl is None:
        base_decl_series, base_decl = read_snapd_base_declaration()
    try:
        SnapReviewDeclaration._verify_declaration(review, base_decl, base=True)
    except Exception as e:  # pragma: nocover
        error("_verify_declaration() raised exception for base decl: %s" % e)

    # First make sure that the interfaces in the snap declaration are known to
    # the base declaration
    for side in snap_decl:
        for iface in snap_decl[side]:
            found = False
            for bside in base_decl:
                if iface in base_decl[bside]:
                    found = True
                    break
            if not found:
                review._add_result(
                    "error",
                    review._get_check_name("valid_interface", app=iface),
                    "interface '%s' not found in base declaration" % iface,
                )

    # Then verify the snap declaration for correctness
    try:
        SnapReviewDeclaration._verify_declaration(review, snap_decl, base=False)
    except Exception as e:  # pragma: nocover
        error("_verify_declaration() raised exception for snap decl: %s" % e)

    return review
