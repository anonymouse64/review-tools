"""test_sr_functional.py: tests for the sr_functional module"""
#
# Copyright (C) 2017 Canonical Ltd.
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
from unittest import TestCase
import os
import shutil
import tempfile

from reviewtools.common import cleanup_unpack
from reviewtools.common import check_results as common_check_results
from reviewtools.common import cmd as cmd
from reviewtools.sr_functional import SnapReviewFunctional
import reviewtools.sr_tests as sr_tests
from reviewtools.tests import utils


class TestSnapReviewFunctional(sr_tests.TestSnapReview):
    """Tests for the functional lint review tool."""

    def setUp(self):
        super().setUp()
        self.set_test_pkgfmt("snap", "16.04")

    def test_all_checks_as_v2(self):
        """Test snap v2 has checks"""
        self.set_test_pkgfmt("snap", "16.04")
        c = SnapReviewFunctional(self.test_name)
        c.do_checks()
        sum = 0
        for i in c.review_report:
            sum += len(c.review_report[i])
        self.assertTrue(sum != 0)


class TestSnapReviewFunctionalNoMock(TestCase):
    """Tests without mocks where they are not needed."""

    def setUp(self):
        # XXX cleanup_unpack() is required because global variables
        # UNPACK_DIR, RAW_UNPACK_DIR, PKG_FILES and PKG_BIN_FILES are
        # initialised to None at module load time, but updated when a real
        # (non-Mock) test runs, such as here. While, at the same time, two of
        # the existing tests using mocks depend on both global vars being None.
        # Ideally, those global vars should be refactored away.
        self.addCleanup(cleanup_unpack)
        super().setUp()

    def mkdtemp(self):
        """Create a temp dir which is cleaned up after test."""
        tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp_dir)
        return tmp_dir

    def check_results(
        self, report, expected_counts={"info": 1, "warn": 0, "error": 0}, expected=None
    ):
        common_check_results(self, report, expected_counts, expected)

    def _execstack_has_lp1850861(self):
        """See if execstack breaks on LP: 1850861"""
        fn = os.path.join(self.mkdtemp(), "ls")
        shutil.copyfile("/bin/ls", fn)
        (rc, out) = cmd(["execstack", "--set-execstack", fn])
        if rc != 0:
            return True

    def test_check_execstack(self):
        """Test check_execstack() - execstack found execstack binary"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return

        # copy /bin/ls nonexecstack.bin
        package = utils.make_snap2(
            output_dir=self.mkdtemp(), extra_files=["/bin/ls:nonexecstack.bin"]
        )
        c = SnapReviewFunctional(package)
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_execstack_found_binary(self):
        """Test check_execstack() - execstack found execstack binary"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return
        elif self._execstack_has_lp1850861():
            print("SKIPPING: execstack failed (LP: #1850861)")
            return

        output_dir = self.mkdtemp()
        fn = os.path.join(output_dir, "hasexecstack.bin")
        shutil.copyfile("/bin/ls", fn)
        # create a /bin/ls with executable stack
        cmd(["execstack", "--set-execstack", fn])

        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = [fn]
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": None, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

        # with how we mocked, we have the absolute path of the file in the
        # tmpdir, so verify beginning of warn only
        self.assertTrue("warn" in report)
        name = "functional-snap-v2:execstack"
        self.assertTrue(name in report["warn"])
        self.assertTrue("text" in report["warn"][name])
        self.assertTrue(
            report["warn"][name]["text"].startswith("Found files with executable stack")
        )

    def test_check_execstack_found_binary_devmode(self):
        """Test check_execstack() - execstack found execstack binary - devmode"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return
        elif self._execstack_has_lp1850861():
            print("SKIPPING: execstack failed (LP: #1850861)")
            return

        output_dir = self.mkdtemp()
        fn = os.path.join(output_dir, "hasexecstack.bin")
        shutil.copyfile("/bin/ls", fn)
        # create a /bin/ls with executable stack
        cmd(["execstack", "--set-execstack", fn])

        yaml = """architectures: [ all ]
name: test
version: 1.0
summary: An application
description: An application
confinement: devmode
"""
        package = utils.make_snap2(output_dir=output_dir, yaml=yaml)
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = [fn]
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        # with how we mocked, we have the absolute path of the file in the
        # tmpdir, so verify beginning of info only
        self.assertTrue("info" in report)
        name = "functional-snap-v2:execstack"
        self.assertTrue(name in report["info"])
        self.assertTrue("text" in report["info"][name])
        self.assertTrue(
            report["info"][name]["text"].startswith("Found files with executable stack")
        )

    def test_check_execstack_found_binary_override(self):
        """Test check_execstack() - execstack found execstack binary - override"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return
        elif self._execstack_has_lp1850861():
            print("SKIPPING: execstack failed (LP: #1850861)")
            return

        output_dir = self.mkdtemp()
        fn = os.path.join(output_dir, "hasexecstack.bin")
        shutil.copyfile("/bin/ls", fn)
        # create a /bin/ls with executable stack
        cmd(["execstack", "--set-execstack", fn])
        package = utils.make_snap2(name="test-override", output_dir=output_dir)
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = [fn]

        # update overrides for our snap
        from reviewtools.overrides import func_execstack_overrides

        func_execstack_overrides.append("test-override")
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        # with how we mocked, we have the absolute path of the file in the
        # tmpdir, so verify beginning of info only
        self.assertTrue("info" in report)
        name = "functional-snap-v2:execstack"
        self.assertTrue(name in report["info"])
        self.assertTrue("text" in report["info"][name])
        self.assertTrue(
            report["info"][name]["text"].startswith(
                "OK (allowing files with executable stack:"
            )
        )

    def test_check_execstack_os(self):
        """Test check_execstack() - os snap"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return
        elif self._execstack_has_lp1850861():
            print("SKIPPING: execstack failed (LP: #1850861)")
            return

        output_dir = self.mkdtemp()
        fn = os.path.join(output_dir, "hasexecstack.bin")
        shutil.copyfile("/bin/ls", fn)
        # create a /bin/ls with executable stack
        cmd(["execstack", "--set-execstack", fn])

        yaml = """architectures: [ all ]
name: test
version: 1.0
summary: An application
description: An application
type: os
"""
        package = utils.make_snap2(output_dir=output_dir, yaml=yaml)
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = [fn]
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_execstack_rc_nonzero(self):
        """Test check_execstack() - execstack returns non-zero"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return

        package = utils.make_snap2(output_dir=self.mkdtemp())
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = ["path/to/nonexistent/file"]
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_execstack_binary_skip(self):
        """Test check_execstack() - execstack found only skipped execstack
           binaries"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return
        elif self._execstack_has_lp1850861():
            print("SKIPPING: execstack failed (LP: #1850861)")
            return

        test_files = [
            "boot/memtest86+_multiboot.bin",
            "lib/klibc-T5LXP1hTwH_ezt-1EUSxPbNR_es.so",
            "usr/alpha-linux-gnu/lib/libgnatprj.so.6",
            "usr/bin/aarch64-linux-gnu-gnatmake-5",
            "usr/bin/gnatcheck",
            "usr/bin/grub-emu",
            "usr/bin/i686-w64-mingw32-gnatclean-posix",
            "usr/lib/debug/usr/bin/iac",
            "usr/lib/grub/i386-coreboot/kernel.exec",
            "usr/lib/i386-linux-gnu/libgnatprj.so.6",
            "usr/lib/klibc/bin/cat",
            "usr/lib/libatlas-test/xcblat1",
            "usr/lib/nvidia-340/bin/nvidia-cuda-mps-control",
            "usr/lib/syslinux/modules/bios/gfxboot.c32",
            "usr/share/dpdk/test/test",
        ]
        output_dir = self.mkdtemp()

        pkg_bin_files = []
        for f in test_files:
            dir = os.path.join(output_dir, os.path.dirname(f))
            if not os.path.exists(dir):
                os.makedirs(dir, 0o0755)
            fn = os.path.join(output_dir, f)
            shutil.copyfile("/bin/ls", fn)
            # create a /bin/ls with executable stack
            cmd(["execstack", "--set-execstack", fn])
            pkg_bin_files.append(fn)

        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = pkg_bin_files
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_execstack_found_with_binary_skip(self):
        """Test check_execstack() - execstack found skipped execstack binary"""
        os.environ["SNAP_ARCH"] = utils.debian_architecture()
        if os.environ["SNAP_ARCH"] == "arm64":  # pragma: nocover
            return
        elif self._execstack_has_lp1850861():
            print("SKIPPING: execstack failed (LP: #1850861)")
            return

        test_files = ["hasexecstack.bin", "usr/lib/klibc/bin/cat"]
        output_dir = self.mkdtemp()

        pkg_bin_files = []
        for f in test_files:
            dir = os.path.join(output_dir, os.path.dirname(f))
            if not os.path.exists(dir):
                os.makedirs(dir, 0o0755)
            fn = os.path.join(output_dir, f)
            shutil.copyfile("/bin/ls", fn)
            # create a /bin/ls with executable stack
            cmd(["execstack", "--set-execstack", fn])
            pkg_bin_files.append(fn)

        package = utils.make_snap2(output_dir=output_dir)
        c = SnapReviewFunctional(package)
        c.pkg_bin_files = pkg_bin_files
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": None, "warn": 1, "error": 0}
        self.check_results(report, expected_counts)

        # with how we mocked, we have the absolute path of the file in the
        # tmpdir, so verify beginning of warn only
        self.assertTrue("warn" in report)
        name = "functional-snap-v2:execstack"
        self.assertTrue(name in report["warn"])
        self.assertTrue("text" in report["warn"][name])
        self.assertTrue(
            report["warn"][name]["text"].startswith("Found files with executable stack")
        )
        self.assertTrue("hasexecstack.bin" in report["warn"][name]["text"])
        self.assertTrue("klibc" not in report["warn"][name]["text"])

    def test_check_execstack_skipped_arm64(self):
        """Test check_execstack() - skipped on arm64"""
        os.environ["SNAP_ARCH"] = "arm64"

        package = utils.make_snap2()
        c = SnapReviewFunctional(package)
        c.check_execstack()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        self.assertTrue("info" in report)
        name = "functional-snap-v2:execstack"
        self.assertTrue(name in report["info"])
        self.assertTrue("text" in report["info"][name])
        self.assertTrue(report["info"][name]["text"] == ("OK (skipped on arm64)"))

    def test_check_base_mountpoints(self):
        """Test check_base_mountpoints()"""
        test_files = [
            "/dev/",
            "/etc/",
            "/home/",
            "/root/",
            "/proc/",
            "/sys/",
            "/tmp/",
            "/var/snap/",
            "/var/lib/snapd/",
            "/var/tmp/",
            "/run/",
            "/usr/src/",
            "/var/log/",
            "/media/",
            "/usr/lib/snapd/",
            "/usr/local/share/fonts/",
            "/usr/share/fonts/",
            "/var/cache/fontconfig/",
            "/lib/modules/",
            "/mnt/",
        ]

        yaml = """
name: test
version: 1.0
type: base
"""
        package = utils.make_snap2(extra_files=test_files, yaml=yaml)
        c = SnapReviewFunctional(package)
        c.check_base_mountpoints()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

    def test_check_base_mountpoints_missing(self):
        """Test check_base_mountpoints() - missing"""
        test_files = [
            "/dev/",
            "/home/",
            "/root/",
            "/proc/",
            "/sys/",
            "/tmp/",
            "/var/snap/",
            "/var/lib/snapd/",
            "/var/tmp/",
            "/run/",
            "/usr/src/",
            "/var/log/",
            "/media/",
            "/usr/lib/snapd/",
            "/usr/local/share/fonts/",
            "/usr/share/fonts/",
            "/var/cache/fontconfig/",
            "/lib/modules/",
            "/mnt/",
        ]

        yaml = """
name: test
version: 1.0
type: base
"""
        package = utils.make_snap2(extra_files=test_files, yaml=yaml)
        c = SnapReviewFunctional(package)
        c.check_base_mountpoints()
        report = c.review_report
        expected_counts = {"info": 0, "warn": 0, "error": 1}
        self.check_results(report, expected_counts)

        self.assertTrue("info" in report)
        name = "functional-snap-v2:base_mountpoints"
        self.assertTrue(name in report["error"])
        self.assertTrue("text" in report["error"][name])
        self.assertTrue(
            report["error"][name]["text"] == ("missing required mountpoints: /etc")
        )

    def test_check_base_mountpoints_missing_overridden(self):
        """Test check_base_mountpoints() - missing (overridden)"""
        test_files = [
            "/dev/",
            "/home/",
            "/root/",
            "/proc/",
            "/sys/",
            "/tmp/",
            "/var/snap/",
            "/var/lib/snapd/",
            "/var/tmp/",
            "/run/",
            "/usr/src/",
            "/var/log/",
            "/media/",
            "/usr/lib/snapd/",
            "/usr/local/share/fonts/",
            "/usr/share/fonts/",
            "/var/cache/fontconfig/",
            "/lib/modules/",
            "/mnt/",
        ]

        yaml = """
name: test-override
version: 1.0
type: base
"""
        package = utils.make_snap2(extra_files=test_files, yaml=yaml)
        c = SnapReviewFunctional(package)
        from reviewtools.overrides import func_base_mountpoints_overrides

        func_base_mountpoints_overrides.append("test-override")
        c.check_base_mountpoints()
        report = c.review_report
        expected_counts = {"info": 1, "warn": 0, "error": 0}
        self.check_results(report, expected_counts)

        self.assertTrue("info" in report)
        name = "functional-snap-v2:base_mountpoints"
        self.assertTrue(name in report["info"])
        self.assertTrue("text" in report["info"][name])
        self.assertTrue(
            report["info"][name]["text"]
            == ("missing required mountpoints: /etc (overridden)")
        )
