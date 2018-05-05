'''test_available.py: tests for the available module'''
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

import os
import tempfile

import clickreviews.available as available
import clickreviews.store as store
import clickreviews.usn as usn

from clickreviews.common import (
    read_file_as_json_dict,
    recursive_rm,
)


class TestAvailable(TestCase):
    """Tests for the updates available functions."""
    def setUp(self):
        self.secnot_db = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.store_db = read_file_as_json_dict(
            "./tests/test-store-unittest-1.db")
        errors = {}
        self.pkg_db = store.get_pkg_revisions(self.store_db[0], self.secnot_db,
                                              errors)
        self.assertEquals(len(errors), 0)

        os.environ['CRT_SEND_EMAIL'] = '0'

        self.tmpdir = None

    def tearDown(self):
        if self.tmpdir is not None:
            recursive_rm(self.tmpdir)

    def test_check_generate_report(self):
        '''Test generate_report()'''
        res = available.generate_report(self.pkg_db, {})
        needle = '''
Revision r11 (amd64; channels: stable, candidate, beta)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1

Revision r12 (i386; channels: stable, candidate, beta)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1

Revision r13 (amd64; channels: edge)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1

Revision r14 (i386; channels: edge)
 * libtiff5: 3602-1, 3606-1
 * libxcursor1: 3501-1
'''
        self.assertTrue(needle in res)

    def test_check_generate_report_rev_no_secnots(self):
        '''Test generate_report() - rev no secnots'''
        self.pkg_db['revisions']['11']['secnot-report'] = {}
        res = available.generate_report(self.pkg_db, {})
        self.assertFalse(' r11 ' in res)

    def test_check_generate_report_no_urls(self):
        '''Test generate_report() - no urls'''
        for rev in self.pkg_db['revisions']:
            self.pkg_db['revisions'][rev]['secnot-report'] = {}
        res = available.generate_report(self.pkg_db, {})
        self.assertEquals(res, "")

    def test_check_generate_email_report_only_new_secnot(self):
        '''Test email_report() - only new secnot'''
        seen_db = {
            '0ad': {
                '11': ['3501-1', '3602-1'],
                '12': ['3501-1', '3602-1'],
                '13': ['3501-1', '3602-1'],
                '14': ['3501-1', '3602-1'],
            }
        }
        res = available.generate_report(self.pkg_db, seen_db)
        needle = '''
Revision r11 (amd64; channels: stable, candidate, beta)
 * libtiff5: 3606-1

Revision r12 (i386; channels: stable, candidate, beta)
 * libtiff5: 3606-1

Revision r13 (amd64; channels: edge)
 * libtiff5: 3606-1

Revision r14 (i386; channels: edge)
 * libtiff5: 3606-1
'''
        self.assertTrue(needle in res)

    def test_check_generate_email_report_only_new_secnot_budgie(self):
        '''Test email_report() - only new secnot budgie'''
        self.secnot_db = usn.read_usn_db("./tests/test-usn-budgie-2.db")
        self.store_db = read_file_as_json_dict("./tests/test-store-budgie.db")
        errors = {}
        self.pkg_db = store.get_pkg_revisions(self.store_db[0], self.secnot_db,
                                              errors)
        self.assertEquals(len(errors), 0)

        seen_db = {
            'ubuntu-budgie-welcome': {
                '11': ['3598-1', '3602-1', '3606-1', '3610-1', '3611-1',
                       '3622-1', '3628-1'],
                '12': ['3598-1', '3602-1', '3606-1', '3610-1', '3611-1',
                       '3622-1', '3628-1'],
                '43': ['3598-1', '3602-1', '3606-1', '3610-1', '3611-1',
                       '3622-1', '3628-1'],
                '44': ['3598-1', '3602-1', '3606-1', '3610-1', '3611-1',
                       '3622-1', '3628-1'],
                '45': ['3598-1', '3602-1', '3606-1', '3610-1', '3611-1',
                       '3622-1', '3628-1'],
                '46': ['3598-1', '3602-1', '3606-1', '3610-1', '3611-1',
                       '3622-1', '3628-1'],
            }
        }
        res = available.generate_report(self.pkg_db, seen_db)
        needle = '''
Revision r11 (amd64; channels: candidate, beta)
 * gir1.2-javascriptcoregtk-4.0: 3635-1
 * gir1.2-webkit2-4.0: 3635-1
 * libjavascriptcoregtk-4.0-18: 3635-1
 * libwebkit2gtk-4.0-37: 3635-1

Revision r12 (i386; channels: candidate, beta)
 * gir1.2-javascriptcoregtk-4.0: 3635-1
 * gir1.2-webkit2-4.0: 3635-1
 * libjavascriptcoregtk-4.0-18: 3635-1
 * libwebkit2gtk-4.0-37: 3635-1
'''
        self.assertTrue(needle in res)

    def test_check_email_report(self):
        '''Test email_report()'''
        res = available.email_report(self.pkg_db, {})
        self.assertTrue(res)

    def test_check_email_report_no_urls(self):
        '''Test generate_report() - no urls'''
        for rev in self.pkg_db['revisions']:
            self.pkg_db['revisions'][rev]['secnot-report'] = {}
        res = available.email_report(self.pkg_db, {})
        self.assertFalse(res)

    def test_check_email_report_with_uploaders(self):
        '''Test email_report() - with uploaders'''
        self.pkg_db['uploaders'] = ["testme@example.com"]
        res = available.email_report(self.pkg_db, {})
        self.assertTrue(res)

    def test_check_email_report_with_additional(self):
        '''Test email_report() - with additional'''
        self.pkg_db['additional'] = ["testme@example.com"]
        res = available.email_report(self.pkg_db, {})
        self.assertTrue(res)

    def test_check_read_seen_db(self):
        '''Test read_seen_db()'''
        self.tmpdir = tempfile.mkdtemp()
        tmp = os.path.join(self.tmpdir, "seen.db")
        res = available.read_seen_db(tmp)
        self.assertEquals(len(res), 0)

    def test_check_update_seen(self):
        '''Test update_seen()'''
        self.tmpdir = tempfile.mkdtemp()
        tmp = os.path.join(self.tmpdir, "seen.db")
        res = available.read_seen_db(tmp)
        self.assertEquals(len(res), 0)
        seen_db = res

        available.update_seen(tmp, seen_db, self.pkg_db)

        res = available.read_seen_db(tmp)
        self.assertEquals(len(res), 1)
        self.assertTrue('0ad' in res)

        expected_db = {
            '0ad': {
                '11': ['3501-1', '3602-1', '3606-1'],
                '12': ['3501-1', '3602-1', '3606-1'],
                '13': ['3501-1', '3602-1', '3606-1'],
                '14': ['3501-1', '3602-1', '3606-1'],
            }
        }
        self.assertEquals(len(expected_db), len(res))

        for pkg in expected_db:
            self.assertTrue(pkg in res)
            self.assertEquals(len(expected_db[pkg]), len(res[pkg]))
            for rev in expected_db[pkg]:
                self.assertTrue(rev in res[pkg])
                self.assertEquals(len(expected_db[pkg][rev]),
                                  len(res[pkg][rev]))
                for secnot in expected_db[pkg][rev]:
                    self.assertTrue(secnot in res[pkg][rev])

    def test_check_update_seen_no_secnots(self):
        '''Test update_seen() - no secnots'''
        self.tmpdir = tempfile.mkdtemp()
        tmp = os.path.join(self.tmpdir, "seen.db")
        res = available.read_seen_db(tmp)
        self.assertEquals(len(res), 0)
        seen_db = res

        for rev in self.pkg_db['revisions']:
            self.pkg_db['revisions'][rev]['secnot-report'] = {}
        available.update_seen(tmp, seen_db, self.pkg_db)

        res = available.read_seen_db(tmp)
        self.assertEquals(len(res), 1)
        self.assertTrue('0ad' in res)
        self.assertEquals(len(res['0ad']), 0)

    def test_check_update_seen_remove_old_revision(self):
        '''Test update_seen() - remove old revision'''
        self.tmpdir = tempfile.mkdtemp()
        tmp = os.path.join(self.tmpdir, "seen.db")
        res = available.read_seen_db(tmp)
        self.assertEquals(len(res), 0)

        seen_db = {
            '0ad': {
                '9': ['3401-1'],
                '10': ['3401-1'],
                '8': ['3401-1'],
                '7': ['3401-1'],
            }
        }
        available.update_seen(tmp, seen_db, self.pkg_db)

        res = available.read_seen_db(tmp)
        self.assertEquals(len(res), 1)
        self.assertTrue('0ad' in res)
        self.assertEquals(len(res['0ad']), 4)

        for r in ['7', '8', '9', '10']:
            self.assertFalse(r in seen_db['0ad'])
