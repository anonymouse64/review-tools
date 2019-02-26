'''test_usn.py: tests for the usn module'''
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
from unittest.mock import patch

import clickreviews.usn as usn
import clickreviews.common as common

import pprint


class TestUSN(TestCase):
    """Tests for the USN functions."""

    def patch_json_load(self, d):
        p = patch('clickreviews.common.json.load')
        self.mock_load = p.start()
        self.mock_load.return_value = d
        self.addCleanup(p.stop)

    def test_check_read_usn_db(self):
        '''Test read_usn_db()'''
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")

        expected_db = {
            'xenial': {'libtiff-doc': {'3602-1': {'version': '4.0.6-1ubuntu0.3', 'cves': ['CVE-2016-10266', 'CVE-2016-10267', 'CVE-2016-10268', 'CVE-2016-10269', 'CVE-2016-10371', 'CVE-2017-10688', 'CVE-2017-11335', 'CVE-2017-12944', 'CVE-2017-13726', 'CVE-2017-13727', 'CVE-2017-18013', 'CVE-2017-7592', 'CVE-2017-7593', 'CVE-2017-7594', 'CVE-2017-7595', 'CVE-2017-7596', 'CVE-2017-7597', 'CVE-2017-7598', 'CVE-2017-7599', 'CVE-2017-7600', 'CVE-2017-7601', 'CVE-2017-7602', 'CVE-2017-9403', 'CVE-2017-9404', 'CVE-2017-9815', 'CVE-2017-9936', 'CVE-2018-5784']},
                                       '3606-1': {'version': '4.0.6-1ubuntu0.4', 'cves': ['CVE-2016-3186', 'CVE-2016-5102', 'CVE-2016-5318', 'CVE-2017-11613', 'CVE-2017-12944', 'CVE-2017-17095', 'CVE-2017-18013', 'CVE-2017-5563', 'CVE-2017-9117', 'CVE-2017-9147', 'CVE-2017-9935', 'CVE-2018-5784']}},
                       'libtiff-opengl': {'3602-1': {'version': '4.0.6-1ubuntu0.3', 'cves': ['CVE-2016-10266', 'CVE-2016-10267', 'CVE-2016-10268', 'CVE-2016-10269', 'CVE-2016-10371', 'CVE-2017-10688', 'CVE-2017-11335', 'CVE-2017-12944', 'CVE-2017-13726', 'CVE-2017-13727', 'CVE-2017-18013', 'CVE-2017-7592', 'CVE-2017-7593', 'CVE-2017-7594', 'CVE-2017-7595', 'CVE-2017-7596', 'CVE-2017-7597', 'CVE-2017-7598', 'CVE-2017-7599', 'CVE-2017-7600', 'CVE-2017-7601', 'CVE-2017-7602', 'CVE-2017-9403', 'CVE-2017-9404', 'CVE-2017-9815', 'CVE-2017-9936', 'CVE-2018-5784']},
                                          '3606-1': {'version': '4.0.6-1ubuntu0.4', 'cves': ['CVE-2016-3186', 'CVE-2016-5102', 'CVE-2016-5318', 'CVE-2017-11613', 'CVE-2017-12944', 'CVE-2017-17095', 'CVE-2017-18013', 'CVE-2017-5563', 'CVE-2017-9117', 'CVE-2017-9147', 'CVE-2017-9935', 'CVE-2018-5784']}},
                       'libtiff-tools': {'3602-1': {'version': '4.0.6-1ubuntu0.3', 'cves': ['CVE-2016-10266', 'CVE-2016-10267', 'CVE-2016-10268', 'CVE-2016-10269', 'CVE-2016-10371', 'CVE-2017-10688', 'CVE-2017-11335', 'CVE-2017-12944', 'CVE-2017-13726', 'CVE-2017-13727', 'CVE-2017-18013', 'CVE-2017-7592', 'CVE-2017-7593', 'CVE-2017-7594', 'CVE-2017-7595', 'CVE-2017-7596', 'CVE-2017-7597', 'CVE-2017-7598', 'CVE-2017-7599', 'CVE-2017-7600', 'CVE-2017-7601', 'CVE-2017-7602', 'CVE-2017-9403', 'CVE-2017-9404', 'CVE-2017-9815', 'CVE-2017-9936', 'CVE-2018-5784']},
                                         '3606-1': {'version': '4.0.6-1ubuntu0.4', 'cves': ['CVE-2016-3186', 'CVE-2016-5102', 'CVE-2016-5318', 'CVE-2017-11613', 'CVE-2017-12944', 'CVE-2017-17095', 'CVE-2017-18013', 'CVE-2017-5563', 'CVE-2017-9117', 'CVE-2017-9147', 'CVE-2017-9935', 'CVE-2018-5784']}},
                       'libtiff5': {'3602-1': {'version': '4.0.6-1ubuntu0.3', 'cves': ['CVE-2016-10266', 'CVE-2016-10267', 'CVE-2016-10268', 'CVE-2016-10269', 'CVE-2016-10371', 'CVE-2017-10688', 'CVE-2017-11335', 'CVE-2017-12944', 'CVE-2017-13726', 'CVE-2017-13727', 'CVE-2017-18013', 'CVE-2017-7592', 'CVE-2017-7593', 'CVE-2017-7594', 'CVE-2017-7595', 'CVE-2017-7596', 'CVE-2017-7597', 'CVE-2017-7598', 'CVE-2017-7599', 'CVE-2017-7600', 'CVE-2017-7601', 'CVE-2017-7602', 'CVE-2017-9403', 'CVE-2017-9404', 'CVE-2017-9815', 'CVE-2017-9936', 'CVE-2018-5784']},
                                    '3606-1': {'version': '4.0.6-1ubuntu0.4', 'cves': ['CVE-2016-3186', 'CVE-2016-5102', 'CVE-2016-5318', 'CVE-2017-11613', 'CVE-2017-12944', 'CVE-2017-17095', 'CVE-2017-18013', 'CVE-2017-5563', 'CVE-2017-9117', 'CVE-2017-9147', 'CVE-2017-9935', 'CVE-2018-5784']}},
                       'libtiff5-dev': {'3602-1': {'version': '4.0.6-1ubuntu0.3', 'cves': ['CVE-2016-10266', 'CVE-2016-10267', 'CVE-2016-10268', 'CVE-2016-10269', 'CVE-2016-10371', 'CVE-2017-10688', 'CVE-2017-11335', 'CVE-2017-12944', 'CVE-2017-13726', 'CVE-2017-13727', 'CVE-2017-18013', 'CVE-2017-7592', 'CVE-2017-7593', 'CVE-2017-7594', 'CVE-2017-7595', 'CVE-2017-7596', 'CVE-2017-7597', 'CVE-2017-7598', 'CVE-2017-7599', 'CVE-2017-7600', 'CVE-2017-7601', 'CVE-2017-7602', 'CVE-2017-9403', 'CVE-2017-9404', 'CVE-2017-9815', 'CVE-2017-9936', 'CVE-2018-5784']},
                                        '3606-1': {'version': '4.0.6-1ubuntu0.4', 'cves': ['CVE-2016-3186', 'CVE-2016-5102', 'CVE-2016-5318', 'CVE-2017-11613', 'CVE-2017-12944', 'CVE-2017-17095', 'CVE-2017-18013', 'CVE-2017-5563', 'CVE-2017-9117', 'CVE-2017-9147', 'CVE-2017-9935', 'CVE-2018-5784']}},
                       'libtiffxx5': {'3602-1': {'version': '4.0.6-1ubuntu0.3', 'cves': ['CVE-2016-10266', 'CVE-2016-10267', 'CVE-2016-10268', 'CVE-2016-10269', 'CVE-2016-10371', 'CVE-2017-10688', 'CVE-2017-11335', 'CVE-2017-12944', 'CVE-2017-13726', 'CVE-2017-13727', 'CVE-2017-18013', 'CVE-2017-7592', 'CVE-2017-7593', 'CVE-2017-7594', 'CVE-2017-7595', 'CVE-2017-7596', 'CVE-2017-7597', 'CVE-2017-7598', 'CVE-2017-7599', 'CVE-2017-7600', 'CVE-2017-7601', 'CVE-2017-7602', 'CVE-2017-9403', 'CVE-2017-9404', 'CVE-2017-9815', 'CVE-2017-9936', 'CVE-2018-5784']},
                                      '3606-1': {'version': '4.0.6-1ubuntu0.4', 'cves': ['CVE-2016-3186', 'CVE-2016-5102', 'CVE-2016-5318', 'CVE-2017-11613', 'CVE-2017-12944', 'CVE-2017-17095', 'CVE-2017-18013', 'CVE-2017-5563', 'CVE-2017-9117', 'CVE-2017-9147', 'CVE-2017-9935', 'CVE-2018-5784']}},
                       'libxcursor-dev': {'3501-1':
                                          {'cves': ['CVE-2017-16612'], 'version': '1:1.1.14-1ubuntu0.16.04.1'}},
                       'libxcursor1': {'3501-1':
                                       {'cves': ['CVE-2017-16612'], 'version': '1:1.1.14-1ubuntu0.16.04.1'}},
                       'libxcursor1-dbg': {'3501-1':
                                           {'cves': ['CVE-2017-16612'], 'version': '1:1.1.14-1ubuntu0.16.04.1'}},
                       'libxcursor1-udeb': {'3501-1':
                                            {'cves': ['CVE-2017-16612'], 'version': '1:1.1.14-1ubuntu0.16.04.1'}},
                       }}

        print(res)
        self.maxDiff = None
        self.assertEquals(len(expected_db), len(res))
        for rel in expected_db:
            self.assertTrue(rel in res)
            self.assertEquals(len(expected_db[rel]), len(res[rel]))
            for pkg in expected_db[rel]:
                self.assertTrue(pkg in res[rel])
                self.assertEquals(len(expected_db[rel][pkg]),
                                  len(res[rel][pkg]))
                for sn in expected_db[rel][pkg]:
                    self.assertTrue(sn in res[rel][pkg])
                    pprint.pprint(expected_db[rel][pkg][sn])
                    pprint.pprint(res[rel][pkg][sn])
                    self.assertEquals(expected_db[rel][pkg][sn]['version'],
                                      str(res[rel][pkg][sn]['version']))
                    self.assertEquals(expected_db[rel][pkg][sn]['cves'],
                                      res[rel][pkg][sn]['cves'])

    def test_check_read_usn_db_no_release(self):
        '''Test read_usn_db() - no releases'''
        # mock up the usn db (for simplicity, we read an existing one then
        # modify it)
        raw = common.read_file_as_json_dict("./tests/test-usn-unittest-1.db")

        # delete USNs we don't care about
        usns = list(raw.keys())
        for k in usns:
            if k != '3606-1':
                del raw[k]

        # modify the USN
        del raw['3606-1']['releases']

        # mock up returning raw when reading ./tests/test-usn-unittest-1.db
        # with json load
        self.patch_json_load(raw)
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.assertEquals(len(res), 0)

    def test_check_read_usn_db_no_xenial(self):
        '''Test read_usn_db() - no xenial'''
        # mock up the usn db (for simplicity, we read an existing one then
        # modify it)
        raw = common.read_file_as_json_dict("./tests/test-usn-unittest-1.db")

        # delete USNs we don't care about
        usns = list(raw.keys())
        for k in usns:
            if k != '3606-1':
                del raw[k]

        # modify the USN
        del raw['3606-1']['releases']['xenial']

        # mock up returning raw when reading ./tests/test-usn-unittest-1.db
        # with json load
        self.patch_json_load(raw)
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.assertEquals(len(res), 0)

    def test_check_read_usn_db_no_sources(self):
        '''Test read_usn_db() - no sources'''
        # mock up the usn db (for simplicity, we read an existing one then
        # modify it)
        raw = common.read_file_as_json_dict("./tests/test-usn-unittest-1.db")

        # delete USNs we don't care about
        usns = list(raw.keys())
        for k in usns:
            if k != '3606-1':
                del raw[k]

        # modify the USN
        del raw['3606-1']['releases']['xenial']['sources']

        # mock up returning raw when reading ./tests/test-usn-unittest-1.db
        # with json load
        self.patch_json_load(raw)
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.assertEquals(len(res), 1)
        self.assertEquals(len(res['xenial']), 0)

    def test_check_read_usn_db_no_versions(self):
        '''Test read_usn_db() - no versions'''
        # mock up the usn db (for simplicity, we read an existing one then
        # modify it)
        raw = common.read_file_as_json_dict("./tests/test-usn-unittest-1.db")

        # delete USNs we don't care about
        usns = list(raw.keys())
        for k in usns:
            if k != '3606-1':
                del raw[k]

        # modify the USN
        for src in raw['3606-1']['releases']['xenial']['sources']:
            del raw['3606-1']['releases']['xenial']['sources'][src]['version']

        # mock up returning raw when reading ./tests/test-usn-unittest-1.db
        # with json load
        self.patch_json_load(raw)
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.assertEquals(len(res), 1)
        self.assertEquals(len(res['xenial']), 6)

    def test_check_read_usn_db_no_binaries(self):
        '''Test read_usn_db() - no binaries'''
        # mock up the usn db (for simplicity, we read an existing one then
        # modify it)
        raw = common.read_file_as_json_dict("./tests/test-usn-unittest-1.db")

        # delete USNs we don't care about
        usns = list(raw.keys())
        for k in usns:
            if k != '3606-1':
                del raw[k]

        # modify the USN
        del raw['3606-1']['releases']['xenial']['binaries']

        # mock up returning raw when reading ./tests/test-usn-unittest-1.db
        # with json load
        self.patch_json_load(raw)
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.assertEquals(len(res), 1)
        self.assertEquals(len(res['xenial']), 0)

    def test_check_read_usn_db_no_archs(self):
        '''Test read_usn_db() - no archs'''
        # mock up the usn db (for simplicity, we read an existing one then
        # modify it)
        raw = common.read_file_as_json_dict("./tests/test-usn-unittest-1.db")

        # delete USNs we don't care about
        usns = list(raw.keys())
        for k in usns:
            if k != '3606-1':
                del raw[k]

        # modify the USN
        del raw['3606-1']['releases']['xenial']['archs']

        # mock up returning raw when reading ./tests/test-usn-unittest-1.db
        # with json load
        self.patch_json_load(raw)
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.assertEquals(len(res), 1)
        self.assertEquals(len(res['xenial']), 0)

    def test_check_read_usn_db_no_urls(self):
        '''Test read_usn_db() - no urls'''
        # mock up the usn db (for simplicity, we read an existing one then
        # modify it)
        raw = common.read_file_as_json_dict("./tests/test-usn-unittest-1.db")

        # delete USNs we don't care about
        usns = list(raw.keys())
        for k in usns:
            if k != '3606-1':
                del raw[k]

        # modify the USN
        for arch in raw['3606-1']['releases']['xenial']['archs']:
            del raw['3606-1']['releases']['xenial']['archs'][arch]['urls']

        # mock up returning raw when reading ./tests/test-usn-unittest-1.db
        # with json load
        self.patch_json_load(raw)
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.assertEquals(len(res), 1)
        self.assertEquals(len(res['xenial']), 0)
