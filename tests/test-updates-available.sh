#!/bin/sh
#set -e

help() {
    cat <<EOM
$ $(basename "$0")
EOM
}

if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    help
    exit
fi

tmp=$(mktemp)
tmp_seen=$(mktemp)


run() {
    seen="$1"
    usn="./tests/$2"
    store="./tests/$3"
    echo "Running: snap-updates-available --seen-db='<tmpfile>' --usn-db='$usn' --store-db='$store'..." | tee -a "$tmp"
    PYTHONPATH=./ ./bin/snap-updates-available --seen-db="$seen" --usn-db="$usn" --store-db="$store" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
}

comment() {
    echo "$@" | tee -a "$tmp"
}

reset_seen() {
    seen="$1"
    comment "Emptying seen.db"
    echo "{}" > "$seen"
}

# should show 3602-1 and 3501-1
comment "= Test --seen-db updated ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-1.db test-store-1.db
run "$tmp_seen" test-usn-1.db test-store-1.db

# should show 3602-1, 3606-1 and 3501-1
comment "= Test multiple USNs with --seen-db updated ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-2.db test-store-1.db
run "$tmp_seen" test-usn-2.db test-store-1.db

# test-usn-unittest-build-pkgs.db contains all USNs in test-usn-2.db + one
# USN for build packages.
# first should show 3602-1, 3606-1 and 3501-1 and subject should only say
# "contains". Second should show 5501-1 and subject should only say "was
# built". https://bugs.launchpad.net/review-tools/+bug/1906827
comment "= Test --seen-db updated. First email subject says 'contains' and second email subject says 'was built' ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-2.db test-store-unittest-3.db
run "$tmp_seen" test-usn-unittest-build-pkgs.db test-store-unittest-3.db
run "$tmp_seen" test-usn-unittest-build-pkgs.db test-store-unittest-3.db

# test-usn-unittest-build-pkgs.db contains all USNs in test-usn-1.db + one
# USN for staged-packages + one USN for build packages.
# first should show 3602-1 and 3501-1 and subject should only say
# "contains". Second should show 3606-1 and 5501-1 and subject should say
# "contains and was built". https://bugs.launchpad.net/review-tools/+bug/1906827
comment "= Test --seen-db updated. First email subject says 'contains' and second email subject says 'contains and was built' ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-1.db test-store-unittest-3.db
run "$tmp_seen" test-usn-unittest-build-pkgs.db test-store-unittest-3.db
run "$tmp_seen" test-usn-unittest-build-pkgs.db test-store-unittest-3.db

# first should show 5501-1 and subject should only say "was
# built". Second should show 3602-1, 3606-1 and 3501-1 and subject should only
# say "contains". https://bugs.launchpad.net/review-tools/+bug/1906827
comment "= Test --seen-db updated. First email subject says 'was built' and second email subject says 'contains' ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-unittest-build-pkgs-only.db test-store-unittest-3.db
run "$tmp_seen" test-usn-2.db test-store-unittest-3.db
run "$tmp_seen" test-usn-2.db test-store-unittest-3.db

# first should show 3606-1 and 5501-1 and subject should say "contains and was
# built". Second should show 3598-1, 3610-1 and 3622-1 and subject should only
# say "contains". https://bugs.launchpad.net/review-tools/+bug/1906827
comment "= Test --seen-db updated. First email subject says 'contains and was built' and second email subject says 'contains' ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-unittest-build-pkgs.db test-store-unittest-3.db
run "$tmp_seen" test-usn-budgie-1.db test-store-unittest-3.db
run "$tmp_seen" test-usn-budgie-1.db test-store-unittest-3.db

# should show 3606-1
comment "= Test previous USNs not reported with --seen-db updated ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-2.db test-store-2.db
run "$tmp_seen" test-usn-2.db test-store-2.db

# should show nothing
comment "= Test up to date with --seen-db updated ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-2.db test-store-3.db
run "$tmp_seen" test-usn-2.db test-store-3.db

comment "= Test real world ="
reset_seen "$tmp_seen"
# should show 3602-1 and 3501-1
comment "== one USN affects snap =="
run "$tmp_seen" test-usn-1.db test-store-1.db
run "$tmp_seen" test-usn-1.db test-store-1.db

# should show 3606-1
comment "== two USNs affect snap =="
run "$tmp_seen" test-usn-2.db test-store-1.db
run "$tmp_seen" test-usn-2.db test-store-1.db

# should show nothing
comment "== no USNs affect snap (snap updated) =="
run "$tmp_seen" test-usn-2.db test-store-3.db
run "$tmp_seen" test-usn-2.db test-store-3.db

# should show 3602-1, 3606-1 and 3501-1
comment "== two USNs affect snap (snap reverted) =="
run "$tmp_seen" test-usn-2.db test-store-1.db
run "$tmp_seen" test-usn-2.db test-store-1.db

# should show nothing
comment "== no USNs affect snap (snap updated again) =="
run "$tmp_seen" test-usn-2.db test-store-3.db
run "$tmp_seen" test-usn-2.db test-store-3.db

# should show 3598-1, 3602-1, 3606-1, 3610-1, 3611-1, 3622-1, and 3628-1
comment "= Test --seen-db for ubuntu-budgie-welcome ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-budgie-1.db test-store-budgie.db
# should show only 3635-1
run "$tmp_seen" test-usn-budgie-2.db test-store-budgie.db

# should show 3790-1 for test-xenial and test-bionic, but not test-default
comment "= Test --seen-db updated for test-xenial and test-bionic ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-os-release.db test-store-os-release.db
run "$tmp_seen" test-usn-os-release.db test-store-os-release.db

# should show 3848-1 and 3879-1
# test-usn-kernel.db contains only USNs for kernel
comment "= Test --seen-db updated for linux-generic-bbb ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-kernel.db test-store-kernel.db
run "$tmp_seen" test-usn-kernel.db test-store-kernel.db

# should show 3848-1, 3879-1 and 5501-1
# test-usn-kernel-and-build-pkgs.db contains USNs for kernel and build pkgs
comment "= Test --seen-db updated for linux-generic-bbb, kernel and snapcraft USNs ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-kernel-and-build-pkgs.db test-store-kernel.db
run "$tmp_seen" test-usn-kernel-and-build-pkgs.db test-store-kernel.db

# test-usn-kernel-and-build-pkgs.db contains all USNs in test-usn-kernel.db +
# one USN for build packages.
# first should show 3848-1, 3879-1 and subject should only say
# "built from outdated". Second should show 5501-1 and subject should only
# say "was built with". https://bugs.launchpad.net/review-tools/+bug/1906827
comment "= Test --seen-db updated for linux-generic-bbb. First for kernel USNs and then for snapcraft USN ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-kernel.db test-store-kernel.db
run "$tmp_seen" test-usn-kernel-and-build-pkgs.db test-store-kernel.db
run "$tmp_seen" test-usn-kernel-and-build-pkgs.db test-store-kernel.db

# first should show 5501-1 and subject should only say "was built with".
# Second should show 3848-1, 3879-1 and subject should only say
# "built from outdated". https://bugs.launchpad.net/review-tools/+bug/1906827
comment "= Test --seen-db updated for linux-generic-bbb. First for snapcraft USN and then for kernel USNs ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-unittest-build-pkgs-only.db test-store-kernel.db
run "$tmp_seen" test-usn-kernel.db test-store-kernel.db
run "$tmp_seen" test-usn-kernel.db test-store-kernel.db

# test-usn-kernel-and-build-pkgs-1.db contains only 1 USN present in
# test-usn-kernel.db + one USN for build packages.
# first should show 5501-1 and 3879-1 and subject should say "built from...
# and with outdated". Second should show 3848-1 and subject should only say
# "built from outdated". https://bugs.launchpad.net/review-tools/+bug/1906827
comment "= Test --seen-db updated for linux-generic-bbb. First for both kernel and snapcraft USNs and then for kernel USN only ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-kernel-and-build-pkgs-1.db test-store-kernel.db
run "$tmp_seen" test-usn-kernel.db test-store-kernel.db
run "$tmp_seen" test-usn-kernel.db test-store-kernel.db

# test-usn-kernel-reduced.db is a reduced version of test-usn-kernel.db.
# test-usn-kernel-and-build-pkgs.db contains all USNs in
# test-usn-kernel-reduced.db + one USN for kernel + one USN for build packages.
# first should show 3879-1 and subject should only say "built from outdated".
# Second should show 3848-1 and 5501-1 and subject should say "built from ...
# and with ...". https://bugs.launchpad.net/review-tools/+bug/1906827
comment "= Test --seen-db updated for linux-generic-bbb. First for kernel USN only and then for both kernel and snapcraft USNs ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-kernel-reduced.db test-store-kernel.db
run "$tmp_seen" test-usn-kernel-and-build-pkgs.db test-store-kernel.db
run "$tmp_seen" test-usn-kernel-and-build-pkgs.db test-store-kernel.db


# should show 5501-1
# test-usn-unittest-build-pkgs-only.db contains only USNs for build pkgs
comment "= Test --seen-db updated for build-pkgs only ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-unittest-build-pkgs-only.db test-store-kernel.db
run "$tmp_seen" test-usn-unittest-build-pkgs-only.db test-store-kernel.db

# should show 5501-1
# test-usn-unittest-build-pkgs.db contains USNs for staged and build pkgs, no
# kernel USNs at all
comment "= Test --seen-db updated for build-pkgs and staged packages ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-unittest-build-pkgs.db test-store-kernel.db
run "$tmp_seen" test-usn-unittest-build-pkgs.db test-store-kernel.db

# should show nothing with release that doesn't exist and release that isn't
# in the usn db yet
comment "= Test unkown release and missing usn release ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-os-release-dne.db test-store-os-release-dne.db
reset_seen "$tmp_seen"

# Test --snap
echo "Running: snap-updates-available --usn-db='./tests/test-usn-budgie-2.db' --snap='./tests/test-snapcraft-manifest_0_amd64.snap'" | tee -a "$tmp"
PYTHONPATH=./ ./bin/snap-updates-available --usn-db='./tests/test-usn-budgie-2.db' --snap='./tests/test-snapcraft-manifest_0_amd64.snap' 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

echo "Running: snap-updates-available --usn-db='./tests/test-usn-core-with-dpkg-list.db' --snap='./tests/test-core_16-2.37.2_amd64.snap'" | tee -a "$tmp"
PYTHONPATH=./ ./bin/snap-updates-available --usn-db='./tests/test-usn-core-with-dpkg-list.db' --snap='./tests/test-core_16-2.37.2_amd64.snap' 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

echo "Running: snap-updates-available --with-cves --usn-db='./tests/test-usn-core-with-dpkg-list.db' --snap='./tests/test-core_16-2.37.2_amd64.snap'" | tee -a "$tmp"
PYTHONPATH=./ ./bin/snap-updates-available --with-cves --usn-db='./tests/test-usn-core-with-dpkg-list.db' --snap='./tests/test-core_16-2.37.2_amd64.snap' 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

echo "Running: snap-updates-available --usn-db='./tests/test-usn-core-with-dpkg-list.db' --snap='./tests/test-dpkg-list-app_1.0_amd64.snap'" | tee -a "$tmp"
PYTHONPATH=./ ./bin/snap-updates-available --usn-db='./tests/test-usn-core-with-dpkg-list.db' --snap='./tests/test-dpkg-list-app_1.0_amd64.snap' 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

echo "Running: snap-updates-available --with-cves --usn-db='./tests/test-usn-core-with-dpkg-list.db' --snap='./tests/test-dpkg-list-app_1.0_amd64.snap'" | tee -a "$tmp"
PYTHONPATH=./ ./bin/snap-updates-available --with-cves --usn-db='./tests/test-usn-core-with-dpkg-list.db' --snap='./tests/test-dpkg-list-app_1.0_amd64.snap' 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

for i in gke-kernel_4.15.0-1027.28~16.04.1_amd64.snap linux-generic-bbb_4.4.0-140-1_armhf.snap pc-kernel_4.15.0-44.46_i386.snap pc-kernel_4.4.0-141.167_amd64.snap ; do
    # kernel USNs only
    echo "Running: snap-updates-available --with-cves --usn-db='./tests/test-usn-kernel.db' --snap='./tests/$i'" | tee -a "$tmp"
    PYTHONPATH=./ ./bin/snap-updates-available --with-cves --usn-db='./tests/test-usn-kernel.db' --snap="./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
    # kernel and build-packages USNs
    echo "Running: snap-updates-available --with-cves --usn-db='./tests/test-usn-kernel-and-build-pkgs.db' --snap='./tests/$i'" | tee -a "$tmp"
    PYTHONPATH=./ ./bin/snap-updates-available --with-cves --usn-db='./tests/test-usn-kernel-and-build-pkgs.db' --snap="./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
    # build-packages USNs only
    echo "Running: snap-updates-available --with-cves --usn-db='./tests/test-usn-unittest-build-pkgs-only.db' --snap='./tests/$i'" | tee -a "$tmp"
    PYTHONPATH=./ ./bin/snap-updates-available --with-cves --usn-db='./tests/test-usn-unittest-build-pkgs-only.db' --snap="./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
    # build-packages and stage-packages USNs - no kernel USN
    echo "Running: snap-updates-available --with-cves --usn-db='./tests/test-usn-unittest-build-pkgs.db' --snap='./tests/$i'" | tee -a "$tmp"
    PYTHONPATH=./ ./bin/snap-updates-available --with-cves --usn-db='./tests/test-usn-unittest-build-pkgs.db' --snap="./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
done

# Test bad store db
echo "Running: ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-1.db' --store-db='./tests/test-store-unittest-bad-1.db'" | tee -a "$tmp"
PYTHONPATH=./ ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-1.db' --store-db='./tests/test-store-unittest-bad-1.db' 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

# Test build and staged packages updates
echo "Running: ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-build-pkgs.db' --store-db='./tests/test-store-unittest-1.db'" | tee -a "$tmp"
PYTHONPATH=./ ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-build-pkgs.db' --store-db='./tests/test-store-unittest-1.db' 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

# Test staged packages updates only - no updates for build packages
echo "Running: ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-build-pkgs.db' --store-db='./tests/test-store-unittest-2.db'" | tee -a "$tmp"
PYTHONPATH=./ ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-build-pkgs.db' --store-db='./tests/test-store-unittest-2.db' 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

# Test build packages updates only
echo "Running: ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-build-pkgs-only.db' --store-db='./tests/test-store-unittest-1.db'" | tee -a "$tmp"
PYTHONPATH=./ ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-build-pkgs-only.db' --store-db='./tests/test-store-unittest-1.db' 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

# Test build packages updates - update override
echo "Running: ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-build-pkgs.db' --store-db='./tests/test-store-unittest-3.db'" | tee -a "$tmp"
PYTHONPATH=./ ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-build-pkgs.db' --store-db='./tests/test-store-unittest-3.db' 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

# Test bad  version for snapcraft in store db
echo "Running: ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-build-pkgs.db' --store-db='./tests/test-store-unittest-invalid-snapcraft-version.db'" | tee -a "$tmp"
PYTHONPATH=./ ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-build-pkgs.db' --store-db='./tests/test-store-unittest-invalid-snapcraft-version.db' 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

# Test bad  version for snapcraft in store db - kernel
echo "Running: ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-build-pkgs.db' --store-db='./tests/test-store-kernel-invalid-snapcraft-version.db'" | tee -a "$tmp"
PYTHONPATH=./ ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-build-pkgs.db' --store-db='./tests/test-store-kernel-invalid-snapcraft-version.db' 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

## LP: #1841848
for i in test-check-notices_0.1_amd64.snap test-check-notices-needed_0.1_amd64.snap test-check-notices-primed-stage-packages_0.1_amd64.snap test-check-notices-primed-stage-packages-needed_0.1_amd64.snap test-check-notices-primed-stage-packages-needed_0.2_amd64.snap; do
    echo "Running: snap-updates-available --usn-db='./tests/test-usn-unittest-lp1841848.db' --snap='./tests/$i'" | tee -a "$tmp"
    PYTHONPATH=./ ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-lp1841848.db' --snap="./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
    echo "Running: snap-updates-available --with-cves --usn-db='./tests/test-usn-unittest-lp1841848.db' --snap='./tests/$i'" | tee -a "$tmp"
    PYTHONPATH=./ ./bin/snap-updates-available --with-cves --usn-db='./tests/test-usn-unittest-lp1841848.db' --snap="./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
done
for i in test-store-unittest-lp1841848.db test-store-unittest-lp1841848-needed.db ; do
    echo "Running: ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-lp1841848.db' --store-db='./tests/$i'" | tee -a "$tmp"
    PYTHONPATH=./ ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-lp1841848.db' --store-db="./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
done

# Test collaborators store db
echo "Running: ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-1.db' --store-db='./tests/test-store-collaborators.db'" | tee -a "$tmp"
PYTHONPATH=./ ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-1.db' --store-db='./tests/test-store-collaborators.db' 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

# Test snap-check-notices
## app
echo "Running: snap-check-notices --no-fetch ./tests/test-snapcraft-manifest_0_amd64.snap" | tee -a "$tmp"
PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-budgie-2.db' ./bin/snap-check-notices --no-fetch "./tests/test-snapcraft-manifest_0_amd64.snap" 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"
echo "Running: snap-check-notices --no-fetch --with-cves ./tests/test-snapcraft-manifest_0_amd64.snap" | tee -a "$tmp"
PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-budgie-2.db' ./bin/snap-check-notices --no-fetch --with-cves "./tests/test-snapcraft-manifest_0_amd64.snap" 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"
echo "Running: USNDB='./tests/test-usn-budgie-3.db' snap-check-notices --no-fetch --with-cves ./tests/test-snapcraft-manifest-snapcraft-version_0_amd64.snap" | tee -a "$tmp"
PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-budgie-3.db' ./bin/snap-check-notices --no-fetch --with-cves "./tests/test-snapcraft-manifest-snapcraft-version_0_amd64.snap" 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"
echo "Running: USNDB='./tests/test-usn-unittest-build-pkgs.db' snap-check-notices --no-fetch --with-cves ./tests/test-snapcraft-manifest-snapcraft-version-needed_0_amd64.snap" | tee -a "$tmp"
PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-unittest-build-pkgs.db' ./bin/snap-check-notices --no-fetch --with-cves "./tests/test-snapcraft-manifest-snapcraft-version-needed_0_amd64.snap" 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"
echo "Running: USNDB='./tests/test-usn-unittest-build-pkgs.db' snap-check-notices --no-fetch --with-cves ./tests/test-snapcraft-manifest-package-in-installed-snaps_0_amd64.snap" | tee -a "$tmp"
PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-unittest-build-pkgs.db' ./bin/snap-check-notices --no-fetch --with-cves "./tests/test-snapcraft-manifest-package-in-installed-snaps_0_amd64.snap" 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"
echo "Running: USNDB='./tests/test-usn-unittest-build-pkgs.db' snap-check-notices --no-fetch --with-cves ./tests/test-snapcraft-manifest-snapcraft-updated_0_amd64.snap" | tee -a "$tmp"
PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-unittest-build-pkgs.db' ./bin/snap-check-notices --no-fetch --with-cves "./tests/test-snapcraft-manifest-snapcraft-updated_0_amd64.snap" 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

## core
echo "Running: snap-check-notices --no-fetch ./tests/test-core_16-2.37.2_amd64.snap" | tee -a "$tmp"
PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-core-with-dpkg-list.db' ./bin/snap-check-notices --no-fetch "./tests/test-core_16-2.37.2_amd64.snap" 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"
echo "Running: snap-check-notices --no-fetch --with-cves ./tests/test-core_16-2.37.2_amd64.snap" | tee -a "$tmp"
PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-core-with-dpkg-list.db' ./bin/snap-check-notices --no-fetch --with-cves "./tests/test-core_16-2.37.2_amd64.snap" 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

## kernel
for i in gke-kernel_4.15.0-1027.28~16.04.1_amd64.snap linux-generic-bbb_4.4.0-140-1_armhf.snap pc-kernel_4.15.0-44.46_i386.snap pc-kernel_4.4.0-141.167_amd64.snap gke-kernel_4.15.0-1069.72_amd64.snap; do
    # kernel USN only
    echo "Running: snap-check-notices --no-fetch ./tests/$i" | tee -a "$tmp"
    PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-kernel.db' ./bin/snap-check-notices --no-fetch "./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
    echo "Running: snap-check-notices --no-fetch --with-cves ./tests/$i" | tee -a "$tmp"
    PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-kernel.db' ./bin/snap-check-notices --no-fetch --with-cves "./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
    # kernel and build-packages USN
    echo "Running: USNDB='./tests/test-usn-kernel-and-build-pkgs.db' snap-check-notices --no-fetch ./tests/$i" | tee -a "$tmp"
    PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-kernel-and-build-pkgs.db' ./bin/snap-check-notices --no-fetch "./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
    echo "Running: USNDB='./tests/test-usn-kernel-and-build-pkgs.db' snap-check-notices --no-fetch --with-cves ./tests/$i" | tee -a "$tmp"
    PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-kernel-and-build-pkgs.db' ./bin/snap-check-notices --no-fetch --with-cves "./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
    # build-packages and stage-packages USN
    echo "Running: USNDB='./tests/test-usn-unittest-build-pkgs.db' snap-check-notices --no-fetch ./tests/$i" | tee -a "$tmp"
    PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-unittest-build-pkgs.db' ./bin/snap-check-notices --no-fetch "./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
    echo "Running: USNDB='./tests/test-usn-unittest-build-pkgs.db' snap-check-notices --no-fetch --with-cves ./tests/$i" | tee -a "$tmp"
    PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-unittest-build-pkgs.db' ./bin/snap-check-notices --no-fetch --with-cves "./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
    # build-packages USN only
    echo "Running: USNDB='./tests/test-usn-unittest-build-pkgs-only.db' snap-check-notices --no-fetch ./tests/$i" | tee -a "$tmp"
    PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-unittest-build-pkgs-only.db' ./bin/snap-check-notices --no-fetch "./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
    echo "Running: USNDB='./tests/test-usn-unittest-build-pkgs-only.db' snap-check-notices --no-fetch --with-cves ./tests/$i" | tee -a "$tmp"
    PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-unittest-build-pkgs-only.db' ./bin/snap-check-notices --no-fetch --with-cves "./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
done

## LP: #1841848
for i in test-check-notices_0.1_amd64.snap test-check-notices-needed_0.1_amd64.snap test-check-notices-primed-stage-packages_0.1_amd64.snap test-check-notices-primed-stage-packages-needed_0.1_amd64.snap test-check-notices-primed-stage-packages-needed_0.2_amd64.snap ; do
    echo "Running: snap-check-notices --no-fetch ./tests/$i" | tee -a "$tmp"
    PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-unittest-lp1841848.db' ./bin/snap-check-notices --no-fetch "./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
    echo "Running: snap-check-notices --no-fetch --with-cves ./tests/$i" | tee -a "$tmp"
    PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-unittest-lp1841848.db' ./bin/snap-check-notices --no-fetch --with-cves "./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
done

echo
echo "Checking for differences in output..."
diff -Naur ./tests/test-updates-available.sh.expected "$tmp" || {
   echo "Found unexpected differences between './tests/test-updates-available.sh.expected' and '$tmp'"
   exit 1
}

rm -f "$tmp" "$tmp_seen"
echo "Done"
