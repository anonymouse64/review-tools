#!/bin/sh
#set -e

tmp=$(mktemp)
tmpjson=$(mktemp)

testtype="snap-review"
topdir=""
if [ -x "./bin/click-review" ]; then
    testtype="./bin/click-review"
    topdir="../click-reviewers-tools-test-packages/"
fi

for i in "$topdir"*.click "$topdir"*.snap ; do
    for j in "" "--sdk" "--json" ; do
        snap=$(basename "$i")
        echo "= $j $snap ="
        if [ "$testtype" = "snap-review" ]; then
            snap-review $j "$i" 2>&1 | sed -e 's/"text": "SKIPPED (could not import apt_pkg)"/"text": "OK"/' -e 's/"text": "checksums do not match. Please ensure the snap .*"/"text": "OK"/' | tee "$tmpjson"
        else
            PYTHONPATH=./ ./bin/click-review $j "$i" 2>&1 | sed -e 's#../click-reviewers-tools-test-packages/##g' -e 's/"text": "checksums do not match. Please ensure the snap .*"/"text": "OK"/' | tee "$tmpjson"
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

for i in "$topdir"test-classic*.snap ; do
    for j in "" "--sdk" "--json" ; do
        snap=$(basename "$i")
        echo "= --allow-classic $j $snap ="
        if [ "$testtype" = "snap-review" ]; then
            snap-review --allow-classic $j "$i" 2>&1 | sed -e 's/"text": "SKIPPED (could not import apt_pkg)"/"text": "OK"/' -e 's/"text": "checksums do not match. Please ensure the snap .*"/"text": "OK"/' | tee "$tmpjson"
        else
            PYTHONPATH=./ ./bin/click-review --allow-classic $j "$i" 2>&1 | sed -e 's#../click-reviewers-tools-test-packages/##g' -e 's/"text": "checksums do not match. Please ensure the snap .*"/"text": "OK"/' | tee "$tmpjson"
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
diff -Naur "$topdir"test.sh.expected "$tmp" || {
   echo "Found unexpected differences between 'test.sh.expected' and '$tmp'"
   exit 1
}

rm -f "$tmp" "$tmpjson"
echo "Done ($testtype)"
