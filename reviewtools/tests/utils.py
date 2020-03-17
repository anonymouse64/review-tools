"""utils.py: test utils for click reviewer tools"""
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

from reviewtools.common import MKSQUASHFS_DEFAULT_COMPRESSION, MKSQUASHFS_OPTS, cmd
import copy
import json
import os
import shutil
import subprocess
import tempfile


def make_snap2(
    name="test",
    pkgfmt_type="snap",
    pkgfmt_version="16.04",
    version="1.0",
    summary="An application",
    extra_files=None,
    output_dir=None,
    yaml=None,
    add_icon=True,
    compression="xz",
):
    """Return the path to a snap v2 package with the given data.

    Caller is responsible for deleting the output_dir afterwards.
    """
    assert pkgfmt_type == "snap" and pkgfmt_version != "15.04"

    build_dir = tempfile.mkdtemp()
    os.chmod(build_dir, 0o775)

    try:
        make_dir_structure(
            build_dir,
            pkgfmt_type=pkgfmt_type,
            pkgfmt_version=pkgfmt_version,
            extra_files=extra_files,
        )
        if add_icon:
            write_icon(build_dir)
        description = summary
        write_meta_data2(build_dir, name, version, summary, description, yaml=yaml)
        pkg_path = build_package(
            build_dir,
            name,
            version,
            pkgfmt_type,
            pkgfmt_version,
            output_dir=output_dir,
            pkgfmt_comp=compression,
        )
    finally:
        shutil.rmtree(build_dir)

    return pkg_path


def make_click(
    name="test",
    pkgfmt_type="click",
    pkgfmt_version="0.4",
    package_types=None,
    version="1.0",
    title="An application",
    framework="ubuntu-sdk-15.04",
    extra_files=None,
    output_dir=None,
):
    """Return the path to a click/snap package with the given data.

    Caller is responsible for deleting the output_dir afterwards.
    """
    assert pkgfmt_type == "click" or (
        pkgfmt_type == "snap" and pkgfmt_version == "15.04"
    )

    is_snap1 = pkgfmt_type == "snap"
    build_dir = tempfile.mkdtemp()
    package_types = package_types or []

    try:
        make_dir_structure(
            build_dir,
            pkgfmt_type=pkgfmt_type,
            pkgfmt_version=pkgfmt_version,
            extra_files=extra_files,
        )
        write_icon(build_dir)

        write_manifest(
            build_dir, name, version, title, framework, package_types, is_snap1
        )
        write_control(build_dir, name, version, title, pkgfmt_version)
        write_preinst(build_dir)
        write_apparmor_profile(build_dir, name)
        write_other_files(build_dir)

        if pkgfmt_type == "snap":
            write_meta_data(build_dir, name, version, title, framework)

        pkg_path = build_package(
            build_dir, name, version, pkgfmt_type, pkgfmt_version, output_dir=output_dir
        )
    finally:
        shutil.rmtree(build_dir)

    return pkg_path


def make_dir_structure(path, pkgfmt_type, pkgfmt_version, extra_files=None):
    """Create the mandatory dir structure and extra_files. Format for
       extra_files:
         path/to/file                   create empty file in path
         path/to/dir/                   create empty dir in path
         path/to/file?PERM              create file/dir with PERM in octal
         path/to/source,path/to/link    create symlink in path
         path/to/source:path/to/link    copy source to path

         For symlink and copy, source can be an absolute path for pointing
         outside of the dir (for symlinks) or copying into the package.
    """
    extra_files = extra_files or []

    directories = ["meta"]  # write_icon() and write_manifest() assume this
    if pkgfmt_type == "click" or pkgfmt_version == 15.04:
        directories.append("DEBIAN")

    # enumerate the directories to create
    for extra_file in extra_files:
        if "," in extra_file:
            extra = extra_file.split(",", 1)[1]
        elif ":" in extra_file:
            extra = extra_file.split(":", 1)[1]
        elif "?" in extra_file:
            extra = extra_file.split("?", 1)[0]
        else:
            extra = extra_file

        if extra.startswith("/"):
            extra = extra[1:]

        if extra.endswith("/"):
            directories.append(extra)
        else:
            directories.append(os.path.dirname(extra))

    # make the enumerated directories
    for directory in directories:
        directory = os.path.join(path, directory)
        if not os.path.exists(directory):
            os.makedirs(directory)

    for extra_file in extra_files:
        if extra_file.endswith("/"):  # nothing more to do for directories
            continue

        source_link = None
        source_path = None
        perm = None
        if "," in extra_file:
            (source_link, target_path) = extra_file.split(",", 1)
        elif ":" in extra_file:
            (source_path, target_path) = extra_file.split(":", 1)
        elif "?" in extra_file:
            (target_path, perm) = extra_file.split("?", 1)
        else:
            target_path = extra_file

        dirname, basename = os.path.split(target_path)
        if basename != "":
            if source_path:
                if not source_path.startswith("/"):
                    source_path = os.path.join(path, source_path)
                shutil.copyfile(source_path, os.path.join(path, target_path))
            elif source_link:
                cur = os.getcwd()
                if target_path.startswith("/"):
                    target_path = os.path.join(path, target_path[1:])
                else:
                    os.chdir(path)
                os.symlink(source_link, target_path)
                os.chdir(cur)
            else:
                with open(os.path.join(path, target_path), "wb"):
                    pass

            if perm is not None:
                os.chmod(os.path.join(path, target_path), int(perm, 8))


def write_icon(path):
    source_path = os.path.join(os.getcwd(), "reviewtools/tests/data/icon.png")
    target_path = os.path.join(path, "meta", "icon.png")
    shutil.copyfile(source_path, target_path)


def write_manifest(path, name, version, title, framework, types, is_snap):
    manifest_content = {
        "framework": framework,
        "maintainer": "Someone <someone@example.com>",
        "name": name,
        "title": title,
        "version": version,
        "icon": "meta/icon.png",
        "hooks": {"app": {"apparmor": "meta/{}.apparmor".format(name)}},
        "description": "This is a test app.",
    }
    if types:
        if is_snap:
            manifest_content.update({"type": types[0]})
        else:
            if "scope" in types:
                manifest_content["hooks"]["app"].update({"scope": ""})
            if "application" in types:
                manifest_content["hooks"]["app"].update({"desktop": ""})

    manifest_paths = [
        os.path.join(path, "DEBIAN", "manifest"),
        os.path.join(path, "manifest.json"),
    ]
    for manifest_path in manifest_paths:
        with open(manifest_path, "w") as f:
            json.dump(manifest_content, f)


def write_meta_data(path, name, version, title, framework):
    yaml_path = os.path.join(path, "meta", "package.yaml")
    content = """architectures:
icon: meta/icon.png
name: {}
version: {}
framework: {}
vendor: 'Someone <someone@example.com>',
""".format(
        name, version, framework
    )

    # don't overwrite 'copy' via make_dir_structure()
    if not os.path.exists(yaml_path):
        with open(yaml_path, "w") as f:
            f.write(content)
    with open(os.path.join(path, "meta", "readme.md"), "w") as f:
        f.write(title)


def write_meta_data2(path, name, version, summary, description, yaml=None):
    yaml_path = os.path.join(path, "meta", "snap.yaml")
    if yaml:
        content = yaml
    else:
        content = """architectures: [ all ]
name: {}
version: {}
summary: {}
description: {}
""".format(
            name, version, summary, description
        )

    # don't overwrite 'copy' via make_dir_structure()
    if not os.path.exists(yaml_path):
        with open(yaml_path, "w") as f:
            f.write(content)


def write_control(path, name, version, title, pkgfmt_version):
    control_path = os.path.join(path, "DEBIAN", "control")
    control_content = {
        "Package": name,
        "Version": version,
        "Click-Version": pkgfmt_version,
        "Architecture": "all",
        "Maintainer": "Someone <someone@example.com>",
        "Installed-Size": "123",
        "Description": title,
    }
    with open(control_path, "w") as f:
        for key, value in control_content.items():
            f.write(key + ": " + value + "\n")


def write_preinst(path):
    preinst_path = os.path.join(path, "DEBIAN", "preinst")
    with open(preinst_path, "w") as f:
        f.write(
            """#! /bin/sh
echo "Click packages may not be installed directly using dpkg."
echo "Use 'click install' instead."
exit 1
"""
        )
    os.chmod(preinst_path, 0o775)


def write_apparmor_profile(path, name):
    profile_path = os.path.join(path, "meta", "{}.apparmor".format(name))
    profile = {"policy_version": 1.3, "policy_groups": []}
    with open(profile_path, "w") as f:
        json.dump(profile, f)


def write_other_files(path):
    def write_empty_file(path, perms=0o664):
        with open(path, "wb"):
            pass
        os.chmod(path, perms)

    write_empty_file(os.path.join(path, "DEBIAN", "md5sums"))


def build_package(
    path, name, version, pkgfmt_type, pkgfmt_version, output_dir=None, pkgfmt_comp="xz"
):
    filename = "{}_{}_all.{}".format(name, version, pkgfmt_type)
    output_dir = output_dir or tempfile.mkdtemp()
    output_path = os.path.join(output_dir, filename)

    if pkgfmt_type == "snap" and pkgfmt_version != "15.04":
        mksquash_opts = copy.copy(MKSQUASHFS_OPTS)
        if pkgfmt_comp != MKSQUASHFS_DEFAULT_COMPRESSION:
            idx = mksquash_opts.index(MKSQUASHFS_DEFAULT_COMPRESSION)
            mksquash_opts[idx] = pkgfmt_comp
        args = ["mksquashfs", path, output_path] + mksquash_opts
        # debugging
        # subprocess.check_call(args)
        # subprocess.check_call(['unsquashfs', '-lls', output_path])
        fd = open(os.devnull, "w")
        subprocess.check_call(args, stdout=fd)
        fd.close()
    else:  # click and snap v1
        # Note: We're not using 'click build' here as it corrects errors (such
        # as filtering out a .click directory present in the build). We want
        # to test with manually constructed, potentially tampered-with
        # clicks/snaps. Ideally, we'd be using click rather than dpkg to
        # construct the click without filtering any files in the build dir.
        subprocess.check_call(["dpkg-deb", "-b", path, output_path])
    return output_path


def debian_architecture():
    (rc, out) = cmd(["dpkg-architecture", "-q", "DEB_BUILD_ARCH"])
    if rc != 0:
        raise ValueError("Could not determined DEB_BUILD_ARCH")
    return out.strip()
