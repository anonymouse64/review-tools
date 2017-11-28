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

testtype="click-review"
if [ "$1" = "system" ]; then
   testtype="snap-review"
   if ! which review-tools.snap-review >/dev/null 2>&1 ; then
       echo "Could not find snap-review. Is the review-tools snap installed?"
       exit 1
   fi
elif [ -n "$1" ]; then
    help
    exit 1
fi

tmp=$(mktemp)
tmpjson=$(mktemp)

for i in ./tests/*.click ./tests/*.snap ; do
    for j in "" "--sdk" "--json" ; do
        snap=$(basename "$i")
        echo "= $j $snap ="
        if [ "$testtype" = "snap-review" ]; then
            review-tools.snap-review $j "$i" 2>&1 | sed -e 's#./tests/##g' -e 's/"text": "SKIPPED (could not import apt_pkg)"/"text": "OK"/' -e 's/"text": "checksums do not match. Please ensure the snap .*"/"text": "OK"/' | tee "$tmpjson"
        else
            PYTHONPATH=./ ./bin/click-review $j "$i" 2>&1 | sed -e 's#./tests/##g' -e 's/"text": "checksums do not match. Please ensure the snap .*"/"text": "OK"/' | tee "$tmpjson"
        fi

        if [ "$j" = "--json" ]; then
            jq '.' "$tmpjson" >/dev/null || {
                echo "'jq . $tmpjson' failed"
                cat "$tmpjson"
                exit 1
            }
        fi
        echo
    done
done | tee "$tmp"

for i in ./tests/test-classic*.snap ; do
    for j in "" "--sdk" "--json" ; do
        snap=$(basename "$i")
        echo "= --allow-classic $j $snap ="
        if [ "$testtype" = "snap-review" ]; then
            review-tools.snap-review --allow-classic $j "$i" 2>&1 | sed -e 's#./tests/##g' -e 's/"text": "SKIPPED (could not import apt_pkg)"/"text": "OK"/' -e 's/"text": "checksums do not match. Please ensure the snap .*"/"text": "OK"/' | tee "$tmpjson"
        else
            PYTHONPATH=./ ./bin/click-review --allow-classic $j "$i" 2>&1 | sed -e 's#./tests/##g' -e 's/"text": "checksums do not match. Please ensure the snap .*"/"text": "OK"/' | tee "$tmpjson"
        fi

        if [ "$j" = "--json" ]; then
            jq '.' "$tmpjson" >/dev/null || {
                echo "'jq . $tmpjson' failed"
                exit 1
            }
        fi
        echo
    done
done | tee -a "$tmp"

echo
echo "Checking for differences in output..."
diff -Naur ./tests/test.sh.expected "$tmp" || {
   echo "Found unexpected differences between './tests/test.sh.expected' and '$tmp'"
   exit 1
}

rm -f "$tmp" "$tmpjson"
echo "Done ($testtype)"
