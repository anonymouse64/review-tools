'''test_store.py: tests for the store module'''
#
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

from unittest import TestCase

import yaml

import clickreviews.store as store

from clickreviews.common import (
    read_file_as_json_dict,
)
import clickreviews.usn as usn


class TestStore(TestCase):
    """Tests for the store functions."""
    def setUp(self):
        '''Read in a sample store and security notice db'''
        self.secnot_db = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.store_db = read_file_as_json_dict(
            "./tests/test-store-unittest-1.db")

    def test_check_get_package_revisions_empty(self):
        '''Test get_package_revisions() - empty item'''

        try:
            store.get_pkg_revisions({}, self.secnot_db, {})
        except ValueError:
            return

        raise Exception("Should have raised ValueError")  # pragma: nocover

    def test_check_get_package_revisions_valid(self):
        '''Test get_package_revisions() - valid'''
        errors = {}
        res = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEquals(len(errors), 0)

        # verify the structure is what we expect
        self.assertTrue('name' in res)
        self.assertEquals(res['name'], "0ad")

        self.assertTrue('publisher' in res)
        self.assertEquals(res['publisher'], "olivier.tilloy@canonical.com")

        self.assertTrue('uploaders' in res)
        self.assertTrue(isinstance(res['uploaders'], list))
        self.assertEquals(len(res['uploaders']), 0)

        self.assertTrue('additional' in res)
        self.assertTrue(isinstance(res['additional'], list))
        self.assertEquals(len(res['additional']), 0)

        self.assertTrue('revisions' in res)
        self.assertTrue('12' in res['revisions'])

        self.assertTrue('channels' in res['revisions']['12'])
        self.assertTrue('stable' in res['revisions']['12']['channels'])

        self.assertTrue('architectures' in res['revisions']['12'])
        self.assertTrue('i386' in res['revisions']['12']['architectures'])

        self.assertTrue('secnot-report' in res['revisions']['12'])
        self.assertTrue('libxcursor1' in res['revisions']['12']['secnot-report'])
        self.assertTrue('3501-1' in
                        res['revisions']['12']['secnot-report']['libxcursor1'])

    def test_check_get_package_revisions_missing_publisher(self):
        '''Test get_package_revisions() - missing publisher'''
        self.store_db[0]['publisher_email'] = ''
        errors = {}
        store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEquals(len(errors), 1)
        self.assertEquals(errors['0ad'][0], "publisher_email '' invalid")

    def test_check_get_package_revisions_missing_revision(self):
        '''Test get_package_revisions() - missing revision'''
        del self.store_db[0]['revisions'][0]['revision']
        errors = {}
        store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEquals(len(errors), 1)
        self.assertEquals(errors['0ad'][0], "no revisions found")

    def test_check_get_package_revisions_missing_manifest(self):
        '''Test get_package_revisions() - missing manifest'''
        del self.store_db[0]['revisions'][0]['manifest_yaml']
        errors = {}
        store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEquals(len(errors), 1)
        self.assertEquals(errors['0ad'][0], "manifest_yaml missing for revision '12'")

    def test_check_get_package_revisions_bad_secnot(self):
        '''Test get_package_revisions() - bad secnot db'''
        self.secnot_db = "bad"
        errors = {}
        store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEquals(len(errors), 1)
        self.assertEquals(errors['0ad'][0],
                          "'xenial' not found in security notification "
                          "database")

    def test_check_get_package_revisions_empty_uploader(self):
        '''Test get_package_revisions() - empty uploader'''
        self.store_db[0]['revisions'][0]['uploader_email'] = ''
        errors = {}
        store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEquals(len(errors), 1)
        self.assertEquals(errors['0ad'][0], "uploader_email '' invalid")

    def test_check_get_package_revisions_has_uploader(self):
        '''Test get_package_revisions() - has uploader'''
        self.store_db[0]['revisions'][0]['uploader_email'] = 'test@example.com'
        errors = {}
        res = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEquals(len(errors), 0)
        self.assertTrue('uploaders' in res)
        self.assertTrue(isinstance(res['uploaders'], list))
        self.assertEquals(len(res['uploaders']), 1)
        self.assertEquals(res['uploaders'][0], "test@example.com")

    def test_check_get_package_revisions_pkg_override(self):
        '''Test get_package_revisions() - pkg override'''
        # update the overrides for this snap
        from clickreviews.overrides import update_publisher_overrides
        update_publisher_overrides['rt-tests@example.com'] = {}
        update_publisher_overrides['rt-tests@example.com']['0ad'] = \
            ['over@example.com']
        self.store_db[0]['publisher_email'] = 'rt-tests@example.com'
        errors = {}
        res = store.get_pkg_revisions(self.store_db[0], self.secnot_db, errors)
        self.assertEquals(len(errors), 0)
        self.assertTrue('additional' in res)
        self.assertTrue(isinstance(res['additional'], list))
        self.assertEquals(len(res['additional']), 1)
        self.assertEquals(res['additional'][0], "over@example.com")

    def test_check_get_shared_snap_without_override_missing(self):
        '''Test get_shared_snap_without_override() - missing'''
        # update the overrides for this snap
        from clickreviews.overrides import update_publisher_overrides
        update_publisher_overrides['rt-tests@example.com'] = {}
        self.store_db[0]['publisher_email'] = 'rt-tests@example.com'
        res = store.get_shared_snap_without_override(self.store_db)
        self.assertTrue(isinstance(res, dict))
        self.assertEquals(len(res), 1)
        self.assertTrue('rt-tests@example.com' in res)
        self.assertEquals(len(res['rt-tests@example.com']), 1)
        self.assertEquals(res['rt-tests@example.com'][0], "0ad")

    def test_check_get_shared_snap_without_override_missing_publisher(self):
        '''Test get_shared_snap_without_override() - missing publisher'''
        del self.store_db[0]['publisher_email']
        res = store.get_shared_snap_without_override(self.store_db)
        self.assertTrue(isinstance(res, dict))
        self.assertEquals(len(res), 0)

    def test_check_get_shared_snap_without_override_not_present(self):
        '''Test get_shared_snap_without_override() - not present'''
        res = store.get_shared_snap_without_override(self.store_db)
        self.assertTrue(isinstance(res, dict))
        self.assertEquals(len(res), 0)

    def test_check_verify_snap_manifest(self):
        '''Test verify_snap_manifest()'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])
        store.verify_snap_manifest(m)

    def test_check_verify_snap_manifest_bad(self):
        '''Test verify_snap_manifest()'''
        try:
            store.verify_snap_manifest([])
        except ValueError:
            return

        raise Exception("Should have raised ValueError")  # pragma: nocover

    def test_check_get_staged_packages_from_manifest(self):
        '''Test get_staged_packages_from_manifest()'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])

        res = store.get_staged_packages_from_manifest(m)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue(len(res) > 0)
        self.assertTrue('libxcursor1' in res)
        self.assertTrue('1:1.1.14-1' in res['libxcursor1'])

    def test_check_get_staged_packages_from_manifest_missing_parts(self):
        '''Test get_staged_packages_from_manifest() - missing parts'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])
        del m['parts']

        res = store.get_staged_packages_from_manifest(m)
        self.assertEquals(res, None)

    def test_check_get_staged_packages_from_manifest_bad_staged(self):
        '''Test get_staged_packages_from_manifest() - bad staged'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])
        m['parts']['0ad-launcher']['stage-packages'].append('foo')

        res = store.get_staged_packages_from_manifest(m)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue(len(res) > 0)
        self.assertFalse('foo' in res)
        self.assertTrue('libxcursor1' in res)
        self.assertTrue('1:1.1.14-1' in res['libxcursor1'])

    def test_check_get_staged_packages_from_manifest_empty_staged(self):
        '''Test get_staged_packages_from_manifest() - empty staged'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])
        m['parts']['0ad-launcher']['stage-packages'] = []

        res = store.get_staged_packages_from_manifest(m)
        self.assertEquals(res, None)

    def test_check_get_staged_packages_from_manifest_binary_ignored(self):
        '''Test get_staged_packages_from_manifest()'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])
        m['parts']['0ad-launcher']['stage-packages'].append(
            'linux-libc-dev=4.4.0-104.127')

        res = store.get_staged_packages_from_manifest(m)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue(len(res) > 0)
        self.assertTrue('libxcursor1' in res)
        self.assertTrue('1:1.1.14-1' in res['libxcursor1'])
        # make sure the ignored package is not present
        self.assertFalse('linux-libc-dev' in res)

    def test_check_get_secnots_for_manifest(self):
        '''Test get_secnots_for_manifest()'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])

        res = store.get_secnots_for_manifest(m, self.secnot_db)
        self.assertTrue(isinstance(res, dict))
        self.assertEquals(len(res), 2)
        self.assertTrue('libxcursor1' in res)
        self.assertEquals(len(res['libxcursor1']), 1)
        self.assertEquals(res['libxcursor1'][0], '3501-1')
        self.assertTrue('libtiff5' in res)
        self.assertEquals(len(res['libtiff5']), 2)
        self.assertTrue('3602-1' in res['libtiff5'])
        self.assertTrue('3606-1' in res['libtiff5'])

    def test_check_get_secnots_for_manifest_empty_staged(self):
        '''Test get_secnots_for_manifest() - empty staged'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])
        m['parts']['0ad-launcher']['stage-packages'] = []

        res = store.get_secnots_for_manifest(m, self.secnot_db)
        self.assertTrue(isinstance(res, dict))
        self.assertEquals(len(res), 0)

    def test_check_get_secnots_for_manifest_has_newer(self):
        '''Test get_secnots_for_manifest() - has newer'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])

        # clear out all the stage-packages and then add one that has a
        # newer package than what is in the security notices
        for part in m['parts']:
            m['parts'][part]['stage-packages'] = []
            if part == '0ad-launcher':
                m['parts'][part]['stage-packages'].append(
                    "libxcursor1=999:1.1.14-1")

        res = store.get_secnots_for_manifest(m, self.secnot_db)
        self.assertTrue(isinstance(res, dict))
        self.assertEquals(len(res), 0)

    def test_check_get_ubuntu_release_from_manifest(self):
        '''Test get_ubuntu_release_from_manifest()'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])
        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEquals(res, "xenial")

    def test_check_get_ubuntu_release_from_manifest_missing_parts(self):
        '''Test get_ubuntu_release_from_manifest() - missing parts'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])
        del m['parts']

        try:
            store.get_ubuntu_release_from_manifest(m)
        except ValueError:
            return

        raise Exception("Should have raised ValueError")  # pragma: nocover

    def test_check_get_ubuntu_release_from_manifest_bad_staged(self):
        '''Test get_ubuntu_release_from_manifest() - bad staged'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])
        m['parts']['0ad-launcher']['installed-snaps'].append('foo')

        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEquals(res, "xenial")

    def test_check_get_ubuntu_release_from_manifest_base18(self):
        '''Test get_ubuntu_release_from_manifest() - base-18'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])
        m['parts']['0ad-launcher']['installed-snaps'].append('base-18=123')

        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEquals(res, "bionic")

    def test_check_get_ubuntu_release_from_manifest_base18_with_others(self):
        '''Test get_ubuntu_release_from_manifest() - base-18 with others'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])
        m['parts']['0ad-launcher']['installed-snaps'].append('abc=123')
        m['parts']['0ad-launcher']['installed-snaps'].append('base-18=123')

        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEquals(res, "bionic")

    def test_check_get_ubuntu_release_from_manifest_base18_with_core(self):
        '''Test get_ubuntu_release_from_manifest() - base-18 with others'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])
        m['parts']['0ad-launcher']['installed-snaps'].append('core=123')
        m['parts']['0ad-launcher']['installed-snaps'].append('base-18=123')

        try:
            store.get_ubuntu_release_from_manifest(m)
        except ValueError:
            return

        raise Exception("Should have raised ValueError")  # pragma: nocover

    def test_check_get_ubuntu_release_from_manifest_core18(self):
        '''Test get_ubuntu_release_from_manifest() - core18'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])
        m['parts']['0ad-launcher']['installed-snaps'].append('core18=123')

        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEquals(res, "bionic")

    def test_check_get_ubuntu_release_from_manifest_core16(self):
        '''Test get_ubuntu_release_from_manifest() - core16'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])
        m['parts']['0ad-launcher']['installed-snaps'].append('core16=123')

        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEquals(res, "xenial")

    def test_check_get_ubuntu_release_from_manifest_core(self):
        '''Test get_ubuntu_release_from_manifest() - core'''
        m = yaml.load(self.store_db[0]['revisions'][0]['manifest_yaml'])
        m['parts']['0ad-launcher']['installed-snaps'].append('core=123')

        res = store.get_ubuntu_release_from_manifest(m)
        self.assertEquals(res, "xenial")
