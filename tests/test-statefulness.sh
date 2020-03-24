#!/bin/sh
#set -e

help() {
    cat <<EOM
$ $(basename "$0") [system]
EOM
}

if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    help
    exit
fi

tmpdir=$(mktemp -d)
tmp="$tmpdir/report"
orig_dir=$(pwd)
in="./in"
out="./out"

run() {
    snap="$orig_dir/tests/$1"
    shift 1
    echo "Running: snap-review $*" | tee -a "$tmp"
    PYTHONPATH="$orig_dir" "$orig_dir"/bin/snap-review "$@" "$snap" 2>&1 | sed -s "s#$orig_dir#.#" | tee -a "$tmp"
    for f in "$in" "$out" ; do
        if [ -r "$f" ]; then
            bn=$(basename "$f")
            echo "$bn:" | tee -a "$tmp"
            tee -a "$tmp" < "$f"
        fi
        test -e "$f" && rm -f "$f"
    done
    echo "" | tee -a "$tmp"
}

comment() {
    echo "$@" | tee -a "$tmp"
}

cd "$tmpdir" || exit 1

for args in "" "--json" "--sdk" ; do
    # --state-output
    comment "= Test --state-output"
    run hello-world_25.snap $args --state-output="$out"

    # --state-input/--state-output
    printf '{\n  "format": 1\n}\n' > "$in"
    comment "= Test --state-input/--state-output"
    run hello-world_25.snap $args --state-input="$in" --state-output="$out"

    # EXFAILs
    # --state-input
    comment "= Test --state-input only"
    printf '{\n  "format": 1\n}\n' > "$in"
    run hello-world_25.snap $args --state-input="$in"

    # --state-input=nonexistent/--state-output
    comment "= Test --state-input=nonexistent/--state-output"
    run hello-world_25.snap $args --state-input="/nonexistent" --state-output="$out"

    # --state-input=invalid/--state-output
    printf '{\n  "format": 0\n}\n' > "$in"
    comment "= Test --state-input=<invalid>/--state-output"
    run hello-world_25.snap $args --state-input="$in" --state-output="$out"

    # --state-input=eperm/--state-output
    printf '{\n  "format": 1\n}\n' > "$in"
    chmod 0222 "$in"
    comment "= Test --state-input=<eperm>/--state-output"
    run hello-world_25.snap $args --state-input="$in" --state-output="$out"

    # --state-output=eperm
    test -d "$tmpdir/not-allowed" || mkdir "$tmpdir/not-allowed"
    chmod 0555 "$tmpdir/not-allowed"
    comment "= Test --state-output=<eperm>"
    run hello-world_25.snap $args --state-output="./not-allowed/out"
done

cd "$orig_dir" || exit 1

echo
echo "Checking for differences in output..."
diff -Naur ./tests/test-statefulness.sh.expected "$tmp" || {
   echo "Found unexpected differences between './tests/test-statefulness.sh.expected' and '$tmp'"
   exit 1
}

rm -rf "$tmpdir"
echo "Done"
