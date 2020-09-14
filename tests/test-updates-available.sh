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
comment "= Test --seen-db updated for linux-generic-bbb ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-kernel.db test-store-kernel.db
run "$tmp_seen" test-usn-kernel.db test-store-kernel.db

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
    echo "Running: snap-updates-available --usn-db='./tests/test-usn-kernel.db' --snap='./tests/$i'" | tee -a "$tmp"
    PYTHONPATH=./ ./bin/snap-updates-available --with-cves --usn-db='./tests/test-usn-kernel.db' --snap="./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
done

# Test bad store db
echo "Running: ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-1.db' --store-db='./tests/test-store-unittest-bad-1.db'" | tee -a "$tmp"
PYTHONPATH=./ ./bin/snap-updates-available --usn-db='./tests/test-usn-unittest-1.db' --store-db='./tests/test-store-unittest-bad-1.db' 2>&1 | tee -a "$tmp"
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

## core
echo "Running: snap-check-notices --no-fetch ./tests/test-core_16-2.37.2_amd64.snap" | tee -a "$tmp"
PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-core-with-dpkg-list.db' ./bin/snap-check-notices --no-fetch "./tests/test-core_16-2.37.2_amd64.snap" 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"
echo "Running: snap-check-notices --no-fetch --with-cves ./tests/test-core_16-2.37.2_amd64.snap" | tee -a "$tmp"
PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-core-with-dpkg-list.db' ./bin/snap-check-notices --no-fetch --with-cves "./tests/test-core_16-2.37.2_amd64.snap" 2>&1 | tee -a "$tmp"
echo "" | tee -a "$tmp"

## kernel
for i in gke-kernel_4.15.0-1027.28~16.04.1_amd64.snap linux-generic-bbb_4.4.0-140-1_armhf.snap pc-kernel_4.15.0-44.46_i386.snap pc-kernel_4.4.0-141.167_amd64.snap gke-kernel_174.snap; do
    echo "Running: snap-check-notices --no-fetch ./tests/$i" | tee -a "$tmp"
    PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-kernel.db' ./bin/snap-check-notices --no-fetch "./tests/$i" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
    echo "Running: snap-check-notices --no-fetch --with-cves ./tests/$i" | tee -a "$tmp"
    PYTHONPATH=./ SNAP=./ SNAP_USER_COMMON=./ USNDB='./tests/test-usn-kernel.db' ./bin/snap-check-notices --no-fetch --with-cves "./tests/$i" 2>&1 | tee -a "$tmp"
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
