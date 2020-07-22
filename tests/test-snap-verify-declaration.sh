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
    echo "Running: snap-verify-declaration $*" | tee -a "$tmp"
    run_no_header "$@" 2>&1 | tee -a "$tmp"
    echo "" | tee -a "$tmp"
}

run_no_header() {
    PYTHONPATH="$orig_dir" "$orig_dir"/bin/snap-verify-declaration "$@"
}

comment() {
    echo "$@" | tee -a "$tmp"
}

origdir="$(pwd)"
cd "$tmpdir"

# -h
comment "= Test -h ="
run "-h"

# plugs
cat > "./plugs" <<EOM
{
  "home": {
    "allow-auto-connection": "true",
    "allow-connection": "true",
    "allow-installation": "true"
  }
}
EOM
run --plugs="./plugs"
run --json --plugs="./plugs"

# slots
cat > "./slots" <<EOM
{
  "mir": {
    "allow-auto-connection": "true",
    "allow-connection": "true",
    "allow-installation": "true"
  }
}
EOM
run --slots="./slots"
run --json --slots="./slots"

# now do both
run --plugs="./plugs" --slots="./slots"
run --json --plugs="./plugs" --slots="./slots"

# empty is ok
cat > "./plugs" <<EOM
{}
EOM
run --plugs="./plugs"
run --json --plugs="./plugs"

# malformed
cat > "./plugs" <<EOM
{
EOM
run --plugs="./plugs"
run --json --plugs="./plugs"

# nonexistent interface
cat > "./plugs" <<EOM
{
  "nonexistent": {
    "allow-auto-connection": "true"
  }
}
EOM
run --plugs="./plugs"
run --json --plugs="./plugs"

# invalid (plug-publisher-id with plugs (should be slot-publisher-id))
cat > "./plugs" <<EOM
{
  "mir": {
    "allow-auto-connection": {
      "plug-publisher-id": [
        "aaaaaaaaaabbbbbbbbbbcccccccccc32"
      ]
    }
  }
}
EOM
run --plugs="./plugs"
run --json --plugs="./plugs"


cd "$origdir"
echo
echo "Checking for differences in output..."
diff -Naur ./tests/test-snap-verify-declaration.sh.expected "$tmp" || {
   echo "Found unexpected differences between './tests/test-snap-verify-declaration.sh.expected' and '$tmp'"
   exit 1
}

rm -f "$tmp" "$tmpdir"/plugs* "$tmpdir"/slots*
rmdir "$tmpdir"
echo "Done"
