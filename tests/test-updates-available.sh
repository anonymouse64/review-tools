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
    PYTHONPATH=./ ./bin/snap-updates-available --seen-db="$seen" --usn-db="$usn" --store-db="$store" | tee -a "$tmp"
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

comment "= Test --seen-db updated ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-1.db test-store-1.db
run "$tmp_seen" test-usn-1.db test-store-1.db

comment "= Test multiple USNs with --seen-db updated ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-2.db test-store-1.db
run "$tmp_seen" test-usn-2.db test-store-1.db

comment "= Test previous USNs not reported with --seen-db updated ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-2.db test-store-2.db
run "$tmp_seen" test-usn-2.db test-store-2.db

comment "= Test up to date with --seen-db updated ="
reset_seen "$tmp_seen"
run "$tmp_seen" test-usn-2.db test-store-3.db
run "$tmp_seen" test-usn-2.db test-store-3.db

comment "= Test real world ="
reset_seen "$tmp_seen"
comment "== one USN affects snap =="
run "$tmp_seen" test-usn-1.db test-store-1.db
run "$tmp_seen" test-usn-1.db test-store-1.db

comment "== two USNs affect snap =="
run "$tmp_seen" test-usn-2.db test-store-1.db
run "$tmp_seen" test-usn-2.db test-store-1.db

comment "== no USNs affect snap (snap updated) =="
run "$tmp_seen" test-usn-2.db test-store-3.db
run "$tmp_seen" test-usn-2.db test-store-3.db

comment "== two USNs affect snap (snap reverted) =="
run "$tmp_seen" test-usn-2.db test-store-1.db
run "$tmp_seen" test-usn-2.db test-store-1.db

comment "== no USNs affect snap (snap updated again) =="
run "$tmp_seen" test-usn-2.db test-store-3.db
run "$tmp_seen" test-usn-2.db test-store-3.db

echo
echo "Checking for differences in output..."
diff -Naur ./tests/test-updates-available.sh.expected "$tmp" || {
   echo "Found unexpected differences between './tests/test-updates-available.sh.expected' and '$tmp'"
   exit 1
}

rm -f "$tmp" "$tmp_seen"
echo "Done"