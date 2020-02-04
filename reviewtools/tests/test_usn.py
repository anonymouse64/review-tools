"""test_usn.py: tests for the usn module"""
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
from unittest.mock import patch, MagicMock

import reviewtools.usn as usn
import reviewtools.common as common

import json
import os
import pprint


class TestUSN(TestCase):
    """Tests for the USN functions."""

    def patch_json_load(self, d):
        p = patch("reviewtools.common.json.load")
        self.mock_load = p.start()
        self.mock_load.return_value = d
        self.addCleanup(p.stop)

    def _mock_read_file_as_json_dict(self, *args, **kwargs):
        # always read in ubuntu-unmatched-bin-versions.json
        if os.path.basename(args[0]) == "ubuntu-unmatched-bin-versions.json":
            fd = common.open_file_read(args[0])
            raw = json.load(fd)
            fd.close()
            return raw
        return self.read_file_as_json_dict_return_value

    def patch_read_file_as_json_dict(self, d):
        self.read_file_as_json_dict_return_value = d
        m = MagicMock(side_effect=self._mock_read_file_as_json_dict)
        p = patch("reviewtools.common.read_file_as_json_dict", new=m)
        self.mock_read_file_as_json_dict = p.start()
        self.addCleanup(p.stop)

    def test_check_read_usn_db(self):
        """Test read_usn_db()"""
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")

        expected_db = {
            "xenial": {
                "libtiff-doc": {
                    "3602-1": {
                        "version": "4.0.6-1ubuntu0.3",
                        "cves": [
                            "CVE-2016-10266",
                            "CVE-2016-10267",
                            "CVE-2016-10268",
                            "CVE-2016-10269",
                            "CVE-2016-10371",
                            "CVE-2017-10688",
                            "CVE-2017-11335",
                            "CVE-2017-12944",
                            "CVE-2017-13726",
                            "CVE-2017-13727",
                            "CVE-2017-18013",
                            "CVE-2017-7592",
                            "CVE-2017-7593",
                            "CVE-2017-7594",
                            "CVE-2017-7595",
                            "CVE-2017-7596",
                            "CVE-2017-7597",
                            "CVE-2017-7598",
                            "CVE-2017-7599",
                            "CVE-2017-7600",
                            "CVE-2017-7601",
                            "CVE-2017-7602",
                            "CVE-2017-9403",
                            "CVE-2017-9404",
                            "CVE-2017-9815",
                            "CVE-2017-9936",
                            "CVE-2018-5784",
                        ],
                    },
                    "3606-1": {
                        "version": "4.0.6-1ubuntu0.4",
                        "cves": [
                            "CVE-2016-3186",
                            "CVE-2016-5102",
                            "CVE-2016-5318",
                            "CVE-2017-11613",
                            "CVE-2017-12944",
                            "CVE-2017-17095",
                            "CVE-2017-18013",
                            "CVE-2017-5563",
                            "CVE-2017-9117",
                            "CVE-2017-9147",
                            "CVE-2017-9935",
                            "CVE-2018-5784",
                        ],
                    },
                },
                "libtiff-opengl": {
                    "3602-1": {
                        "version": "4.0.6-1ubuntu0.3",
                        "cves": [
                            "CVE-2016-10266",
                            "CVE-2016-10267",
                            "CVE-2016-10268",
                            "CVE-2016-10269",
                            "CVE-2016-10371",
                            "CVE-2017-10688",
                            "CVE-2017-11335",
                            "CVE-2017-12944",
                            "CVE-2017-13726",
                            "CVE-2017-13727",
                            "CVE-2017-18013",
                            "CVE-2017-7592",
                            "CVE-2017-7593",
                            "CVE-2017-7594",
                            "CVE-2017-7595",
                            "CVE-2017-7596",
                            "CVE-2017-7597",
                            "CVE-2017-7598",
                            "CVE-2017-7599",
                            "CVE-2017-7600",
                            "CVE-2017-7601",
                            "CVE-2017-7602",
                            "CVE-2017-9403",
                            "CVE-2017-9404",
                            "CVE-2017-9815",
                            "CVE-2017-9936",
                            "CVE-2018-5784",
                        ],
                    },
                    "3606-1": {
                        "version": "4.0.6-1ubuntu0.4",
                        "cves": [
                            "CVE-2016-3186",
                            "CVE-2016-5102",
                            "CVE-2016-5318",
                            "CVE-2017-11613",
                            "CVE-2017-12944",
                            "CVE-2017-17095",
                            "CVE-2017-18013",
                            "CVE-2017-5563",
                            "CVE-2017-9117",
                            "CVE-2017-9147",
                            "CVE-2017-9935",
                            "CVE-2018-5784",
                        ],
                    },
                },
                "libtiff-tools": {
                    "3602-1": {
                        "version": "4.0.6-1ubuntu0.3",
                        "cves": [
                            "CVE-2016-10266",
                            "CVE-2016-10267",
                            "CVE-2016-10268",
                            "CVE-2016-10269",
                            "CVE-2016-10371",
                            "CVE-2017-10688",
                            "CVE-2017-11335",
                            "CVE-2017-12944",
                            "CVE-2017-13726",
                            "CVE-2017-13727",
                            "CVE-2017-18013",
                            "CVE-2017-7592",
                            "CVE-2017-7593",
                            "CVE-2017-7594",
                            "CVE-2017-7595",
                            "CVE-2017-7596",
                            "CVE-2017-7597",
                            "CVE-2017-7598",
                            "CVE-2017-7599",
                            "CVE-2017-7600",
                            "CVE-2017-7601",
                            "CVE-2017-7602",
                            "CVE-2017-9403",
                            "CVE-2017-9404",
                            "CVE-2017-9815",
                            "CVE-2017-9936",
                            "CVE-2018-5784",
                        ],
                    },
                    "3606-1": {
                        "version": "4.0.6-1ubuntu0.4",
                        "cves": [
                            "CVE-2016-3186",
                            "CVE-2016-5102",
                            "CVE-2016-5318",
                            "CVE-2017-11613",
                            "CVE-2017-12944",
                            "CVE-2017-17095",
                            "CVE-2017-18013",
                            "CVE-2017-5563",
                            "CVE-2017-9117",
                            "CVE-2017-9147",
                            "CVE-2017-9935",
                            "CVE-2018-5784",
                        ],
                    },
                },
                "libtiff5": {
                    "3602-1": {
                        "version": "4.0.6-1ubuntu0.3",
                        "cves": [
                            "CVE-2016-10266",
                            "CVE-2016-10267",
                            "CVE-2016-10268",
                            "CVE-2016-10269",
                            "CVE-2016-10371",
                            "CVE-2017-10688",
                            "CVE-2017-11335",
                            "CVE-2017-12944",
                            "CVE-2017-13726",
                            "CVE-2017-13727",
                            "CVE-2017-18013",
                            "CVE-2017-7592",
                            "CVE-2017-7593",
                            "CVE-2017-7594",
                            "CVE-2017-7595",
                            "CVE-2017-7596",
                            "CVE-2017-7597",
                            "CVE-2017-7598",
                            "CVE-2017-7599",
                            "CVE-2017-7600",
                            "CVE-2017-7601",
                            "CVE-2017-7602",
                            "CVE-2017-9403",
                            "CVE-2017-9404",
                            "CVE-2017-9815",
                            "CVE-2017-9936",
                            "CVE-2018-5784",
                        ],
                    },
                    "3606-1": {
                        "version": "4.0.6-1ubuntu0.4",
                        "cves": [
                            "CVE-2016-3186",
                            "CVE-2016-5102",
                            "CVE-2016-5318",
                            "CVE-2017-11613",
                            "CVE-2017-12944",
                            "CVE-2017-17095",
                            "CVE-2017-18013",
                            "CVE-2017-5563",
                            "CVE-2017-9117",
                            "CVE-2017-9147",
                            "CVE-2017-9935",
                            "CVE-2018-5784",
                        ],
                    },
                },
                "libtiff5-dev": {
                    "3602-1": {
                        "version": "4.0.6-1ubuntu0.3",
                        "cves": [
                            "CVE-2016-10266",
                            "CVE-2016-10267",
                            "CVE-2016-10268",
                            "CVE-2016-10269",
                            "CVE-2016-10371",
                            "CVE-2017-10688",
                            "CVE-2017-11335",
                            "CVE-2017-12944",
                            "CVE-2017-13726",
                            "CVE-2017-13727",
                            "CVE-2017-18013",
                            "CVE-2017-7592",
                            "CVE-2017-7593",
                            "CVE-2017-7594",
                            "CVE-2017-7595",
                            "CVE-2017-7596",
                            "CVE-2017-7597",
                            "CVE-2017-7598",
                            "CVE-2017-7599",
                            "CVE-2017-7600",
                            "CVE-2017-7601",
                            "CVE-2017-7602",
                            "CVE-2017-9403",
                            "CVE-2017-9404",
                            "CVE-2017-9815",
                            "CVE-2017-9936",
                            "CVE-2018-5784",
                        ],
                    },
                    "3606-1": {
                        "version": "4.0.6-1ubuntu0.4",
                        "cves": [
                            "CVE-2016-3186",
                            "CVE-2016-5102",
                            "CVE-2016-5318",
                            "CVE-2017-11613",
                            "CVE-2017-12944",
                            "CVE-2017-17095",
                            "CVE-2017-18013",
                            "CVE-2017-5563",
                            "CVE-2017-9117",
                            "CVE-2017-9147",
                            "CVE-2017-9935",
                            "CVE-2018-5784",
                        ],
                    },
                },
                "libtiffxx5": {
                    "3602-1": {
                        "version": "4.0.6-1ubuntu0.3",
                        "cves": [
                            "CVE-2016-10266",
                            "CVE-2016-10267",
                            "CVE-2016-10268",
                            "CVE-2016-10269",
                            "CVE-2016-10371",
                            "CVE-2017-10688",
                            "CVE-2017-11335",
                            "CVE-2017-12944",
                            "CVE-2017-13726",
                            "CVE-2017-13727",
                            "CVE-2017-18013",
                            "CVE-2017-7592",
                            "CVE-2017-7593",
                            "CVE-2017-7594",
                            "CVE-2017-7595",
                            "CVE-2017-7596",
                            "CVE-2017-7597",
                            "CVE-2017-7598",
                            "CVE-2017-7599",
                            "CVE-2017-7600",
                            "CVE-2017-7601",
                            "CVE-2017-7602",
                            "CVE-2017-9403",
                            "CVE-2017-9404",
                            "CVE-2017-9815",
                            "CVE-2017-9936",
                            "CVE-2018-5784",
                        ],
                    },
                    "3606-1": {
                        "version": "4.0.6-1ubuntu0.4",
                        "cves": [
                            "CVE-2016-3186",
                            "CVE-2016-5102",
                            "CVE-2016-5318",
                            "CVE-2017-11613",
                            "CVE-2017-12944",
                            "CVE-2017-17095",
                            "CVE-2017-18013",
                            "CVE-2017-5563",
                            "CVE-2017-9117",
                            "CVE-2017-9147",
                            "CVE-2017-9935",
                            "CVE-2018-5784",
                        ],
                    },
                },
                "libxcursor-dev": {
                    "3501-1": {
                        "cves": ["CVE-2017-16612"],
                        "version": "1:1.1.14-1ubuntu0.16.04.1",
                    }
                },
                "libxcursor1": {
                    "3501-1": {
                        "cves": ["CVE-2017-16612"],
                        "version": "1:1.1.14-1ubuntu0.16.04.1",
                    }
                },
                "libxcursor1-dbg": {
                    "3501-1": {
                        "cves": ["CVE-2017-16612"],
                        "version": "1:1.1.14-1ubuntu0.16.04.1",
                    }
                },
                "libxcursor1-udeb": {
                    "3501-1": {
                        "cves": ["CVE-2017-16612"],
                        "version": "1:1.1.14-1ubuntu0.16.04.1",
                    }
                },
            }
        }

        print(res)
        self.maxDiff = None
        self.assertEqual(len(expected_db), len(res))
        for rel in expected_db:
            self.assertTrue(rel in res)
            self.assertEqual(len(expected_db[rel]), len(res[rel]))
            for pkg in expected_db[rel]:
                self.assertTrue(pkg in res[rel])
                self.assertEqual(len(expected_db[rel][pkg]), len(res[rel][pkg]))
                for sn in expected_db[rel][pkg]:
                    self.assertTrue(sn in res[rel][pkg])
                    pprint.pprint(expected_db[rel][pkg][sn])
                    pprint.pprint(res[rel][pkg][sn])
                    self.assertEqual(
                        expected_db[rel][pkg][sn]["version"],
                        str(res[rel][pkg][sn]["version"]),
                    )
                    self.assertEqual(
                        expected_db[rel][pkg][sn]["cves"], res[rel][pkg][sn]["cves"]
                    )

    def test_check_read_usn_db_no_release(self):
        """Test read_usn_db() - no releases"""
        # mock up the usn db (for simplicity, we read an existing one then
        # modify it)
        raw = common.read_file_as_json_dict("./tests/test-usn-unittest-1.db")

        # delete USNs we don't care about
        usns = list(raw.keys())
        for k in usns:
            if k != "3606-1":
                del raw[k]

        # modify the USN
        del raw["3606-1"]["releases"]

        # mock up returning raw when reading ./tests/test-usn-unittest-1.db
        # with json load
        self.patch_json_load(raw)
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.assertEqual(len(res), 0)

    def test_check_read_usn_db_no_xenial(self):
        """Test read_usn_db() - no xenial"""
        # mock up the usn db (for simplicity, we read an existing one then
        # modify it)
        raw = common.read_file_as_json_dict("./tests/test-usn-unittest-1.db")

        # delete USNs we don't care about
        usns = list(raw.keys())
        for k in usns:
            if k != "3606-1":
                del raw[k]

        # modify the USN
        del raw["3606-1"]["releases"]["xenial"]

        # mock up returning raw when reading ./tests/test-usn-unittest-1.db
        # with json load
        self.patch_json_load(raw)
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.assertEqual(len(res), 0)

    def test_check_read_usn_db_no_sources(self):
        """Test read_usn_db() - no sources"""
        # mock up the usn db (for simplicity, we read an existing one then
        # modify it)
        raw = common.read_file_as_json_dict("./tests/test-usn-unittest-1.db")

        # delete USNs we don't care about
        usns = list(raw.keys())
        for k in usns:
            if k != "3606-1":
                del raw[k]

        # modify the USN
        del raw["3606-1"]["releases"]["xenial"]["sources"]

        # mock up returning raw when reading ./tests/test-usn-unittest-1.db
        # with json load
        self.patch_json_load(raw)
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res["xenial"]), 0)

    def test_check_read_usn_db_no_versions(self):
        """Test read_usn_db() - no versions"""
        # mock up the usn db (for simplicity, we read an existing one then
        # modify it)
        raw = common.read_file_as_json_dict("./tests/test-usn-unittest-1.db")

        # delete USNs we don't care about
        usns = list(raw.keys())
        for k in usns:
            if k != "3606-1":
                del raw[k]

        # modify the USN
        for src in raw["3606-1"]["releases"]["xenial"]["sources"]:
            del raw["3606-1"]["releases"]["xenial"]["sources"][src]["version"]

        # mock up returning raw when reading ./tests/test-usn-unittest-1.db
        # with json load
        self.patch_json_load(raw)
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res["xenial"]), 6)

    def test_check_read_usn_db_no_binaries(self):
        """Test read_usn_db() - no binaries"""
        # mock up the usn db (for simplicity, we read an existing one then
        # modify it)
        raw = common.read_file_as_json_dict("./tests/test-usn-unittest-1.db")

        # delete USNs we don't care about
        usns = list(raw.keys())
        for k in usns:
            if k != "3606-1":
                del raw[k]

        # modify the USN
        del raw["3606-1"]["releases"]["xenial"]["binaries"]

        # mock up returning raw when reading ./tests/test-usn-unittest-1.db
        # with json load
        self.patch_json_load(raw)
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res["xenial"]), 0)

    def test_check_read_usn_db_no_archs(self):
        """Test read_usn_db() - no archs"""
        # mock up the usn db (for simplicity, we read an existing one then
        # modify it)
        raw = common.read_file_as_json_dict("./tests/test-usn-unittest-1.db")

        # delete USNs we don't care about
        usns = list(raw.keys())
        for k in usns:
            if k != "3606-1":
                del raw[k]

        # modify the USN
        del raw["3606-1"]["releases"]["xenial"]["archs"]

        # mock up returning raw when reading ./tests/test-usn-unittest-1.db
        # with json load
        self.patch_json_load(raw)
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res["xenial"]), 0)

    def test_check_read_usn_db_no_urls(self):
        """Test read_usn_db() - no urls"""
        # mock up the usn db (for simplicity, we read an existing one then
        # modify it)
        raw = common.read_file_as_json_dict("./tests/test-usn-unittest-1.db")

        # delete USNs we don't care about
        usns = list(raw.keys())
        for k in usns:
            if k != "3606-1":
                del raw[k]

        # modify the USN
        for arch in raw["3606-1"]["releases"]["xenial"]["archs"]:
            del raw["3606-1"]["releases"]["xenial"]["archs"][arch]["urls"]

        # mock up returning raw when reading ./tests/test-usn-unittest-1.db
        # with json load
        self.patch_json_load(raw)
        res = usn.read_usn_db("./tests/test-usn-unittest-1.db")
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res["xenial"]), 0)

    def test_check_read_usn_db_with_unmatched(self):
        """Test read_usn_db() - unmatched"""
        res = usn.read_usn_db("./tests/test-usn-unittest-lp1841848.db")

        expected_db = {
            "xenial": {
                "uno-libs3": {
                    "4102-1": {
                        "version": "5.1.6~rc2-0ubuntu1~xenial9",
                        "cves": ["CVE-2019-9850", "CVE-2019-9851", "CVE-2019-9852"],
                    }
                },
                "libreoffice-style-tango": {
                    "4102-1": {
                        "version": "1:5.1.6~rc2-0ubuntu1~xenial9",
                        "cves": ["CVE-2019-9850", "CVE-2019-9851", "CVE-2019-9852"],
                    }
                },
            },
            "bionic": {
                "uno-libs3": {
                    "4102-1": {
                        "version": "6.0.7-0ubuntu0.18.04.9",
                        "cves": ["CVE-2019-9850", "CVE-2019-9851", "CVE-2019-9852"],
                    }
                },
                "libreoffice-style-tango": {
                    "4102-1": {
                        "version": "1:6.0.7-0ubuntu0.18.04.9",
                        "cves": ["CVE-2019-9850", "CVE-2019-9851", "CVE-2019-9852"],
                    }
                },
            },
        }

        print(res)
        self.maxDiff = None
        self.assertEqual(len(expected_db), len(res))

        for rel in expected_db:
            self.assertTrue(rel in res)
            self.assertEqual(len(expected_db[rel]), len(res[rel]))
            for pkg in expected_db[rel]:
                self.assertTrue(pkg in res[rel])
                self.assertEqual(len(expected_db[rel][pkg]), len(res[rel][pkg]))
                for sn in expected_db[rel][pkg]:
                    self.assertTrue(sn in res[rel][pkg])
                    pprint.pprint(expected_db[rel][pkg][sn])
                    pprint.pprint(res[rel][pkg][sn])
                    self.assertEqual(
                        expected_db[rel][pkg][sn]["version"],
                        str(res[rel][pkg][sn]["version"]),
                    )
                    self.assertEqual(
                        expected_db[rel][pkg][sn]["cves"], res[rel][pkg][sn]["cves"]
                    )

    def test_check_read_usn_db_with_unmatched_bad_epoch(self):
        """Test read_usn_db() - unmatched bin epoch missing (bin override has no epoch)"""
        res = usn.read_usn_db("./tests/test-usn-unittest-lp1841848-incorrect-epoch.db")

        expected_db = {
            "xenial": {
                "uno-libs3": {
                    "4102-1": {
                        "version": "5.1.6~rc2-0ubuntu1~xenial9",
                        "cves": ["CVE-2019-9850", "CVE-2019-9851", "CVE-2019-9852"],
                    }
                },
                "libreoffice-style-tango": {
                    "4102-1": {
                        "version": "1:5.1.6~rc2-0ubuntu1~xenial9",
                        "cves": ["CVE-2019-9850", "CVE-2019-9851", "CVE-2019-9852"],
                    }
                },
            },
            "bionic": {
                "uno-libs3": {
                    "4102-1": {
                        "version": "6.0.7-0ubuntu0.18.04.9",
                        "cves": ["CVE-2019-9850", "CVE-2019-9851", "CVE-2019-9852"],
                    }
                },
                "libreoffice-style-tango": {
                    "4102-1": {
                        "version": "1:6.0.7-0ubuntu0.18.04.9",
                        "cves": ["CVE-2019-9850", "CVE-2019-9851", "CVE-2019-9852"],
                    }
                },
            },
        }

        print(res)
        self.maxDiff = None
        self.assertEqual(len(expected_db), len(res))

        for rel in expected_db:
            self.assertTrue(rel in res)
            self.assertEqual(len(expected_db[rel]), len(res[rel]))
            for pkg in expected_db[rel]:
                self.assertTrue(pkg in res[rel])
                self.assertEqual(len(expected_db[rel][pkg]), len(res[rel][pkg]))
                for sn in expected_db[rel][pkg]:
                    self.assertTrue(sn in res[rel][pkg])
                    pprint.pprint(expected_db[rel][pkg][sn])
                    pprint.pprint(res[rel][pkg][sn])
                    self.assertEqual(
                        expected_db[rel][pkg][sn]["version"],
                        str(res[rel][pkg][sn]["version"]),
                    )
                    self.assertEqual(
                        expected_db[rel][pkg][sn]["cves"], res[rel][pkg][sn]["cves"]
                    )

    def test_check_read_usn_db_with_unmatched_bad_epoch2(self):
        """Test read_usn_db() - unmatched bin epoch missing (bin override has epoch)"""
        # mock up the usn db (for simplicity, we read an existing one then
        # modify it)
        raw = common.read_file_as_json_dict(
            "./tests/test-usn-unittest-lp1841848-incorrect-epoch2.db"
        )
        # modify the USN to have a missing epoch when it should be there
        raw["999999-1"]["releases"]["xenial"]["allbinaries"]["bsdutils"][
            "version"
        ] = "2.27.1-6ubuntu3"
        raw["999999-1"]["releases"]["xenial"]["binaries"]["bsdutils"][
            "version"
        ] = "2.27.1-6ubuntu3"
        # mock up returning raw when reading ./tests/test-usn-unittest-1.db
        # with json load
        # self.patch_json_load(raw)
        self.patch_read_file_as_json_dict(raw)
        res = usn.read_usn_db("./tests/test-usn-unittest-lp1841848-incorrect-epoch2.db")

        expected_db = {
            "xenial": {
                "bsdutils": {
                    "999999-1": {
                        "version": "1:2.27.1-6ubuntu3",
                        "cves": ["CVE-2019-999999"],
                    }
                }
            }
        }

        print(res)
        self.maxDiff = None
        self.assertEqual(len(expected_db), len(res))

        for rel in expected_db:
            self.assertTrue(rel in res)
            self.assertEqual(len(expected_db[rel]), len(res[rel]))
            for pkg in expected_db[rel]:
                self.assertTrue(pkg in res[rel])
                self.assertEqual(len(expected_db[rel][pkg]), len(res[rel][pkg]))
                for sn in expected_db[rel][pkg]:
                    self.assertTrue(sn in res[rel][pkg])
                    pprint.pprint(expected_db[rel][pkg][sn])
                    pprint.pprint(res[rel][pkg][sn])
                    self.assertEqual(
                        expected_db[rel][pkg][sn]["version"],
                        str(res[rel][pkg][sn]["version"]),
                    )
                    self.assertEqual(
                        expected_db[rel][pkg][sn]["cves"], res[rel][pkg][sn]["cves"]
                    )

    def test_check_read_usn_db_with_unmatched_bad_epoch3(self):
        """Test read_usn_db() - unmatched bin epoch missing (can't guess with allbinaries)"""
        res = usn.read_usn_db(
            "./tests/test-usn-unittest-lp1841848-unmatched-binver-noallbin.db"
        )

        expected_db = {"xenial": {}}
        print(res)
        self.maxDiff = None
        self.assertEqual(len(expected_db), len(res))
        self.assertEqual(len(expected_db["xenial"]), len(res["xenial"]))

    def test_check_read_usn_db_with_unmatched_bad_epoch4(self):
        """Test read_usn_db() - unmatched bin epoch missing (can't guess)"""
        res = usn.read_usn_db("./tests/test-usn-unittest-lp1841848-unmatched-binver.db")

        expected_db = {"xenial": {}}
        print(res)
        self.maxDiff = None
        self.assertEqual(len(expected_db), len(res))
        self.assertEqual(len(expected_db["xenial"]), len(res["xenial"]))
