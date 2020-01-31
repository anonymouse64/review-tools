#!/bin/sh
set -e

help() {
    cat <<EOM
$ $(basename "$0")
EOM
}

if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    help
    exit
fi

tmpdir=$(mktemp -d)
tmp="$tmpdir/out"
orig_dir=$(pwd)

run() {
    echo "Running: dump-tool $*" | tee -a "$tmp"
    run_no_header "$@" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
}

run_no_header() {
    PYTHONPATH="$orig_dir" "$orig_dir"/bin/dump-tool "$@"
}

comment() {
    echo "$@" | tee -a "$tmp"
}

# --file
comment "= Test --file ="
run --file "./tests/test-store-dump.1"
run --file "./tests/test-store-dump.2"
run_no_header --file "./tests/test-store-dump.1" --output=stdout > "$tmpdir/tst.file.stdout"
diff "./tests/test-store-dump.1.json" "$tmpdir/tst.file.stdout"
run_no_header --file "./tests/test-store-dump.1" --output="$tmpdir/tst.file.out"
diff "./tests/test-store-dump.1.json" "$tmpdir/tst.file.out"

# --file (bad)
comment "= Test --file (bad) ="
cd "$tmpdir"
echo bad > "./bad"
run --file "./bad" --output=stdout
cd "$orig_dir"

# --file --progress
comment "= Test --file --progress ="
run --progress --file "./tests/test-store-dump.1"

# --file --warn-if-empty
comment "= Test --file --warn-if-empty ="
run --warn-if-empty --file "./tests/test-store-dump.1"

# --db-file
comment "= Test --db-file ="
run --db-file "./tests/test-store-dump.1.json"
run --db-file "./tests/test-store-dump.2.json"
run_no_header --db-file "./tests/test-store-dump.1.json" --output=stdout > "$tmpdir/tst.db-file.stdout"
diff "./tests/test-store-dump.1.json" "$tmpdir/tst.db-file.stdout"
run_no_header --db-file "./tests/test-store-dump.1.json" --output="$tmpdir/tst.db-file.out"
diff "./tests/test-store-dump.1.json" "$tmpdir/tst.db-file.out"

# --db-file (bad)
comment "= Test --db-file (bad) ="
cd "$tmpdir"
echo bad > "./bad"
run --db-file "./bad" --output=stdout
cd "$orig_dir"

# --file --db-file (merge)
comment "= Test --file --db-file (merge) ="
run --force-merge --db-file "./tests/test-store-dump.1.json" --file "./tests/test-store-dump.2"
run_no_header --force-merge --db-file "./tests/test-store-dump.1.json" --file "./tests/test-store-dump.2" --output="$tmpdir/tst.merge.out"
diff "./tests/test-store-dump.2.json" "$tmpdir/tst.merge.out"

echo
echo "Checking for differences in output..."
diff -Naur ./tests/test-dump-tool.sh.expected "$tmp" || {
   echo "Found unexpected differences between './tests/test-dump-tool.sh.expected' and '$tmp'"
   exit 1
}

rm -f "$tmp" "$tmpdir"/tst* "$tmpdir"/bad*
rmdir "$tmpdir"
echo "Done"
