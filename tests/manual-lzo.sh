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

# this list of snaps are the only snaps available for all 7 architectures,
# note that core, core18, snapd, etc. are not available on powerpc which is
# puzzling...
all_arch_snaps=(gtk-common-themes hello-world lxd snappy-debug)

amd64_snaps=(core20 chromium gnome-calculator libreoffice aws-cli bandwhich chocolate-doom-jdstrand firefox gimp gnome-3-26-1604 gnome-3-28-1804 gnome-characters gnome-logs gnome-system-monitor gtk2-common-themes multipass remmina sdlpop ubuntu-image spotify wormhole snapcraft review-tools core core18 snapd docker bobrossquotes cvescan)
i386_snaps=(chromium gnome-calculator bandwhich chocolate-doom-jdstrand gimp gnome-3-26-1604 gnome-3-28-1804 gnome-characters gnome-logs gnome-system-monitor remmina sdlpop ubuntu-image wormhole snapcraft review-tools core core18 snapd docker bobrossquotes cvescan)
arm64_snaps=(core20 chromium gnome-calculator aws-cli bandwhich chocolate-doom-jdstrand gimp gnome-3-28-1804 gnome-characters gnome-logs gnome-system-monitor gtk2-common-themes multipass remmina sdlpop wormhole snapcraft review-tools core core18 snapd docker bobrossquotes cvescan)
armhf_snaps=(core20 chromium gnome-calculator chocolate-doom-jdstrand gimp gnome-3-28-1804 gnome-characters gnome-logs gnome-system-monitor gtk2-common-themes multipass remmina sdlpop wormhole snapcraft review-tools core core18 snapd docker bobrossquotes cvescan)
s390x_snaps=(core20 bandwhich wormhole snapcraft review-tools core core18 snapd docker bobrossquotes cvescan)
ppc64el_snaps=(core20 bandwhich remmina sdlpop wormhole snapcraft review-tools core core18 snapd docker bobrossquotes cvescan)
powerpc_snaps=()

case "$(uname -m)" in
    x86_64)
        echo "running on amd64"
        all_snaps=("${amd64_snaps[@]}" "${all_arch_snaps[@]}")
        ;;
    aarch64)
        echo "running on arm64"
        all_snaps=("${arm64_snaps[@]}" "${all_arch_snaps[@]}")
        ;;
    arm*)
        echo "running on armhf"
        all_snaps=("${armhf_snaps[@]}" "${all_arch_snaps[@]}")
        ;;
    i686|i386)
        echo "running on i386"
        all_snaps=("${i386_snaps[@]}" "${all_arch_snaps[@]}")
        ;;
    ppc64le)
        echo "running on ppc64el"
        all_snaps=("${ppc64el_snaps[@]}" "${all_arch_snaps[@]}")
        ;;
    s390x)
        echo "running on s390x"
        all_snaps=("${s390x_snaps[@]}" "${all_arch_snaps[@]}")
        ;;
    powerpc|ppc)
        echo "running on powerpc"
        all_snaps=("${powerpc_snaps[@]}" "${all_arch_snaps[@]}")
        ;;
    *)
        echo "unknown architecture $(dpkg --print-architecture), giving up"
        exit 1
        ;;
esac

function maybe_sudo {
    # base snaps need to be sudo to extract/pack/rm/etc
    # chromium and snapd have setuid files that get stripped when run as non-root
    if is_core_or_snapd_snap "$1" || [ "$1" = "chromium" ]; then
        echo "sudo"
        # use sudo so that later in the loop the user doesn't get prompted for
        # sudo again
        sudo echo "useless sudo to keep authenticated against sudo during loops..." > /dev/null
    else
        echo ""
    fi
}

function is_core_or_snapd_snap {
    if is_core_snap "$1" || [ "$1" = "snapd" ] ; then
        return 0
    else
        return 1
    fi
}

function is_core_snap {
    if [ "$1" = "core" ] || [ "$1" = "core18" ] || [ "$1" = "core20" ] || [ "$1" = "core22" ]; then
        return 0
    else
        return 1
    fi
}



# step 0. ensure pre-reqs are available
#         * snap is to download the snap
#         * unsquashfs is to unpack the snap
#         * mksquashfs is to re-pack the snap
#         * lxc is to create a xenial/bionic container to check the re-packed snap for
#           deterministic repacking - the review-tools used in there does NOT is not
#           kernel specific, so it's fine to use a container for this purpose
#         * sha256sum is for checking the hashes of the snap
#         * jq is for checking the output of review-tools for the specific test
#           we care about
#         * curl is to download the review-tools tarball to avoid git pulling it

for cmd in snap unsquashfs mksquashfs lxc sha256sum jq curl; do
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

    for sn in "${all_snaps[@]}"; do
        MAYBE_SUDO=$(maybe_sudo "$sn")
        # also cleanup the intermediate hashed snaps
        $MAYBE_SUDO rm -f "${sn}_lzo-"*.snap
        $MAYBE_SUDO rm -rf "${sn}-src"

    done
    exit 1
}
trap cleanup EXIT SIGINT SIGTERM


# save some distro/system info
{
    echo "[[ UNAME VERSION ]]"
    uname -a
    echo "[[ SNAP VERSION ]]"
    snap version
    echo "[[ LXD VERSION ]]"
    lxd version
    echo "[[ UNSQUASHFS VERSION ]]"
    unsquashfs -v || true
    echo "[[ ETC/OS-RELEASE VERSION ]]"
    cat /etc/os-release
}>> "$SCRIPT_DIR/system.info"

TARBALL="$(pwd)/lzo-results.tgz"
tar cvf "$TARBALL" "system.info"

pushd "$SCRIPT_DIR"

# download the review-tools tarball so we don't pull it every time
# TODO: it would be nice if github supported -C- to resume/not have to re-download
# this every time automatically with curl
curl -L -o review-tools.tgz https://github.com/anonymouse64/review-tools/archive/lzo-test-2.tar.gz

# NOTE: we can only do step 3 of this test, the deterministic resquash, on
#       systems that have squashfs-tools with the -fstime option, as otherwise
#       the resquashes will have different fstimes and thus never match. Thus,
#       before running this check, we ensure that the mksquashfs we have
#       available supports -fstime, and if it doesn't we skip it
HAVE_FSTIME=yes

# make simple squashfs
rm -rf test-squashfs
mkdir test-squashfs
date "+%Y-%m-%dT%H:%M:%S%:z" > test-squashfs/filedate
# don't need sudo cause no special device nodes or set{u,g}id bit files
mksquashfs test-squashfs test-squashfs-1.snap -no-progress -noappend -comp xz -all-root -no-xattrs -no-fragments

if TEST_FSTIME=$(unsquashfs -fstime test-squashfs-1.snap); then
    # verify that the fstime options actually works as advertised on this system
    mksquashfs test-squashfs test-squashfs-2.snap -fstime "$TEST_FSTIME" -no-progress -noappend -comp xz -all-root -no-xattrs -no-fragments
    sleep 1
    mksquashfs test-squashfs test-squashfs-3.snap -fstime "$TEST_FSTIME" -no-progress -noappend -comp xz -all-root -no-xattrs -no-fragments

    # all 3 snaps should have the same hash
    # verify that the fstime option actually works by resquashing twice with the 
    # option
    prev_sum=""
    for j in 1 2 3; do
        sum=$(sha256sum "test-squashfs-$j.snap" | cut -f1 -d' ')
        # if we have the previous one (not on the first iteration), check it matches
        # the current one
        if [ -n "$prev_sum" ] && [ "$sum" != "$prev_sum" ]; then
            # fstime is broken, didn't produce the same hash of snap files
            HAVE_FSTIME=no
            break
        fi
        prev_sum=$sum
    done
else
    # probably unsquashfs doesn't support fstime
    HAVE_FSTIME=no
fi


sudo echo "useless sudo to keep authenticated against sudo during loops..." > /dev/null

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

# download all the snaps up front, this saves networking time for the long haul
# which will just be CPU intensive and thus more resilient against volatile
# networking/store outages
for sn in "${all_snaps[@]}" ; do
    sudo echo "useless sudo to keep authenticated against sudo during loops..." > /dev/null

    # step 1. download the snap as that is our baseline xz compressed
    until snap download --edge "$sn" --basename="${sn}_xz"; do
        echo "waiting to re-try download"
        sleep 5
    done
done

for sn in "${all_snaps[@]}" ; do
    MAYBE_SUDO=$(maybe_sudo "$sn")

    sudo echo "useless sudo to keep authenticated against sudo during loops..." > /dev/null

    # step 2. unsquash the snap
    $MAYBE_SUDO rm -rf "${sn}-src" # in case of interrupted runs
    $MAYBE_SUDO unsquashfs -d "${sn}-src" "${sn}_xz.snap"


    # step 3. repack with lzo options set 10 times checking that the compressed
    #         snap has the same hash each time (only if we have fstime)
    if [ "$HAVE_FSTIME" = "yes" ]; then
        # get the fstime to use for the deterministm check
        fstime=$(unsquashfs -fstime "${sn}_xz.snap")

        for i in $(seq 1 10); do
            hashfile="${sn}.lzo.sha256"

            # pack the snap - these options match "snap pack"
            if [ -n "$MAYBE_SUDO" ]; then
                # if we are calling sudo, don't use -all-root
                sudo mksquashfs "${sn}-src" "${sn}_lzo-$i.snap" -fstime "$fstime" -no-progress -noappend -comp lzo -no-xattrs -no-fragments
            else
                # use -all-root when we are not using sudo
                mksquashfs "${sn}-src" "${sn}_lzo-$i.snap" -fstime "$fstime" -no-progress -noappend -comp lzo -all-root -no-xattrs -no-fragments
            fi

            # calculate the sha256sum for the re-packed snap
            sum=$(sha256sum "${sn}_lzo-$i.snap" | cut -f1 -d' ')

            # in the first go-around, save the hash
            if [ "$i" = "1" ]; then
                echo "$sum" > "$hashfile"
            else
                # in all other iterations make sure the calculated hash matches the
                # saved one from the first iteration
                if [ "$sum" != "$(cat "$hashfile")"  ]; then
                    echo ">>> TEST FAIL <<< snap $sn lzo compressed on iteration $i had sha256sum of $sum, expected $(cat "$hashfile") from iteration 1"
                    exit 1
                fi

                # we're done with this passing lzo, so discard it to not waste
                # space during the runs
                rm -f "${sn}_lzo-$i.snap"

                # sleep a small amount of time to ensure that the time is different
                # when we re-pack again in the next iteration
                sleep 0.5
            fi

            sudo echo "useless sudo to keep authenticated against sudo during loops..." > /dev/null
        done

        # cleanup the re-packed snaps, saving the first one for later usage
        $MAYBE_SUDO mv "${sn}_lzo-1.snap" "${sn}_lzo.snap"
        $MAYBE_SUDO rm -f "${sn}_lzo-"*.snap
        $MAYBE_SUDO rm -rf "${sn}-src"
    else
        # we don't have -fstime, but we still need to produce a lzo snap to test
        # in the store check
        if [ -n "$MAYBE_SUDO" ]; then
            # if we are calling sudo, don't use -all-root
            sudo mksquashfs "${sn}-src" "${sn}_lzo.snap" -no-progress -noappend -comp lzo -no-xattrs -no-fragments
        else
            # use -all-root when we are not using sudo
            mksquashfs "${sn}-src" "${sn}_lzo.snap" -no-progress -noappend -comp lzo -all-root -no-xattrs -no-fragments
        fi
    fi

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
        # as root for snaps that have setuid , and when unpacking within the lxd
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

    # finally packup the lzo snap for final testing of the review-tools check
    # on amd64
    $MAYBE_SUDO tar --append --file="$TARBALL" "${sn}_lzo.snap"
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
