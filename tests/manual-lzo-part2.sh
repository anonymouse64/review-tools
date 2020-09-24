#!/bin/bash

#
# Author: Ian Johnson <ian.johnson@canonical.com>
# Copyright (C) 2020 Canonical Ltd.
#
# This script is distributed under the terms and conditions of the GNU General
# Public License, Version 3 or later. See http://www.gnu.org/copyleft/gpl.html
# for details.
#
# Notes:
# * to prevent snap refreshes during runs, especially for lxd which happens a
#   lot, use:
#   $ sudo snap set system refresh.hold="$(date --date="7 days" +%Y-%m-%dT%H:%M:%S%:z)"
# * The primary goal of this matrix is to capture different versions of
#   squashfs-tools, across a range of architectures. It's not imperative that
#   we get all possible values filled out, as it shouldn't be the case that
#   other distros have weird patches on top of squashfs-tools that are also
#   arch specific, so i.e. as long as we get a single debian run and a single
#   arm64 run that should imply that debian with arm64 is likely ok
#

set -ex

# get the directory of this script
# snippet from https://stackoverflow.com/a/246128/10102404
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

if [ "$#" != 1 ]; then
    echo "usage: ./manual-lzo-part2.sh <tarball>"
    exit 1
fi

TARBALL=$(readlink -f "$1")

# TODO: share common snippets of this script with manual-lzo.sh ?
function is_core_snap {
    if [ "$1" = "core" ] || [ "$1" = "core18" ] || [ "$1" = "core20" ] ; then
        return 0
    else
        return 1
    fi
}

# step 0. ensure pre-reqs are available
#         * snap is to download the snap
#         * lxc is to create a xenial/bionic container to check the re-packed snap for
#           deterministic repacking - the review-tools used in there does NOT is not
#           kernel specific, so it's fine to use a container for this purpose
#         * jq is for checking the output of review-tools for the specific test
#           we care about
#         * curl is to download the review-tools tarball to avoid git pulling it

for cmd in snap lxc jq curl; do
    if ! command -v $cmd >/dev/null; then
        echo "$cmd is not installed, please install and run again"
        if [ "$cmd" = "lxc" ]; then
            echo "also initialize lxd with \`sudo lxd init\`, and do not use zfs storage backend as it is currently buggy with mksquashfs/unsquashfs"
        fi
        exit 1
    fi
done

# we need a recent enough jq otherwise older ones, i.e. 1.3 from trusty archive
# will fail with an error like
# error: syntax error, unexpected QQSTRING_START, expecting $end
# . | ."snap.v2_security"."info"."security-snap-v2:squashfs_repack_checksum"."text"
#      ^
# 1 compile error

if [ "$(jq --help 2>&1| grep version | grep -Po 'version 1\.\K[0-9]')" -le "4" ]; then
    echo "jq version too old, please upgrade to at least 1.5"
    echo "hint: the snap is currently at 1.5, snap install jq"
    exit 1
fi

# on some distros, i.e. debian sudo does not have /snap/bin on path
LXC=$(command -v lxc)

# ensure that lxd is setup to not use zfs storage dir, as that is buggy
if sudo "$LXC" info | grep -q "storage: zfs"; then
    echo "zfs storage dir for lxd is not supported due to a bug, please use storage: dir"
    exit 1
fi

function cleanup {
    echo "signalled unexpectedly, triggering cleanup..."
    set +x
    set +e
    trap - EXIT SIGINT SIGTERM
    for series in 16 18 20; do
        cont_name="review-tools-$series-04-checker"
        if sudo "$LXC" list --fast | grep -q "${cont_name}"; then
            sudo "$LXC" delete "${cont_name}" --force || true
        fi
    done

    exit 1
}
trap cleanup EXIT SIGINT SIGTERM

pushd "$SCRIPT_DIR"

# download the review-tools tarball so we don't pull it every time
# TODO: it would be nice if github supported -C- to resume/not have to re-download
# this every time automatically with curl
curl -L -o review-tools.tgz https://github.com/anonymouse64/review-tools/archive/lzo-test-2.tar.gz

# start the containers up front to share the same containers across all snaps
# this saves us networking time and ensures we
for series in 16 18 20; do
    cont_name="review-tools-$series-04-checker"

    sudo "$LXC" launch "ubuntu:$series.04" "${cont_name}"

    # wait for networking to work before pushing any files to the container
    sudo "$LXC" exec "${cont_name}" -- /bin/bash -c 'until nslookup -timeout=1 archive.ubuntu.com; do sleep 0.1; done'

    sudo "$LXC" file push review-tools.tgz "${cont_name}/root/review-tools.tgz"

    sudo "$LXC" exec "${cont_name}" -- apt update
    sudo "$LXC" exec "${cont_name}" -- apt upgrade -y

    # dependencies for review-tools as per the snapcraft.yaml
    sudo "$LXC" exec "${cont_name}" -- apt install -y binutils fakeroot file libdb5.3 libmagic1 python3-magic python3-requests python3-simplejson python3-yaml squashfs-tools
    sudo "$LXC" exec "${cont_name}" -- apt clean

    sudo "$LXC" exec "${cont_name}" -- mkdir /root/review-tools
    sudo "$LXC" exec "${cont_name}" -- tar -C /root/review-tools --strip-components=1 -xf /root/review-tools.tgz
done

# get the full list of snaps from the tarball
# see shellcheck 2207 for why this mapfile, etc.
# note this only works on bash 4.x+ however
mapfile -t all_snaps < <(tar --wildcards -tf "$TARBALL" '*.snap' | grep -Po '(.+)(?=_lzo.snap)')

for sn in "${all_snaps[@]}" ; do
    # first extract the snap file from the tarball, we do this one at a time to
    # optimize total disk space usage during the test
    tar -xf "$TARBALL" "${sn}_lzo.snap"

    sudo echo "useless sudo to stay authenticated against sudo during loops..." > /dev/null

    # step 4. run the review-tools inside the various ubuntu lxc containers to
    #         check that the snap is unsquashed and resquashed to the same blob
    for series in 16 18 20; do
        cont_name="review-tools-$series-04-checker"

        sudo "$LXC" file push "${sn}_lzo.snap" "${cont_name}/root/${sn}_lzo.snap"

        # the core* base snaps are not properly checked within the lxd container
        # by the review-tools because they have files like /dev/* that are not
        # properly preserved when unpacked and repacked inside the lxd container
        # because lxd does not allow mknod, etc.
        # as such, the check for the base snaps is somewhat artifical, but we
        # still expect a specific message from the review-tools to ensure that
        # something else didn't fail
        # note that root owned files and setuid files are ok here (i.e. from the
        # chromium and snapd snaps), because we created the squashfs files above
        # as root for snaps that have setuid, and when unpacking within the lxd
        # container the files are ok to be created setuid, owned as root, etc.
        if is_core_snap "$sn"; then
            expected="OK (check not enforced for base and os snaps)"
        else
            expected="OK"
        fi

        # use SNAP_ENFORCE_RESQUASHFS_COMP=0 to ensure that we don't fail on
        # snaps that haven't been given permission to upload with lzo compression
        # also use --json so that we can check specifically the result of the
        # squashfs_repack_checksum test, as some snaps like chromium have been
        # granted permission to use interfaces that normally trigger a review,
        # but we don't have that state available to us about the interfaces and
        # we don't really care about that the interface usage anyways
        repack_check=$(
            sudo "$LXC" exec \
                --cwd /root/review-tools \
                --env SNAP_ENFORCE_RESQUASHFS_COMP=0 \
                --env SNAP_DEBUG_RESQUASHFS=1 \
                --env PYTHONPATH=/root/review-tools \
                "${cont_name}" -- \
                /root/review-tools/bin/snap-review --json "/root/${sn}_lzo.snap" || true
        )

        if [ "$(echo "$repack_check" | jq -r '."snap.v2_security".info."security-snap-v2:squashfs_repack_checksum".text')" != "$expected" ]; then
            echo ">>> TEST FAIL <<< snap $sn lzo compressed failed review-tools check for squashfs_repack_checksum in lxd $series.04 container"
            exit 1
        fi

        # We're done with the lzo in the container
        sudo "$LXC" exec "${cont_name}" -- rm -f "/root/${sn}_lzo.snap"

        sudo echo "useless sudo to keep authenticated against sudo during loops..." > /dev/null
    done

    rm "${sn}_lzo.snap"
done

for series in 16 18 20; do
    cont_name="review-tools-$series-04-checker"

    sudo "$LXC" stop "${cont_name}" --force
    sudo "$LXC" delete "${cont_name}" --force
done

popd

echo "test done, results in $TARBALL"

# reset the cleanup so we don't unnecessarily run it and exit with non-zero status
trap - EXIT SIGINT SIGTERM
