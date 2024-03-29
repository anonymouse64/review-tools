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

# TODO: figure out a different way to determine if performing system tests
testtype="click-review"
if [ "$1" = "system" ]; then
   testtype="snap-review"
   # shellcheck disable=SC2230
   if ! which review-tools.snap-review >/dev/null 2>&1 ; then
       echo "Could not find snap-review. Is the review-tools snap installed?"
       exit 1
   fi
   if ! snap connections review-tools | grep -Eq 'review-tools:home +:home' ; then
       echo "Please connect the home interface with: sudo snap connect review-tools:home"
       exit 1
   fi
elif [ -n "$1" ]; then
    help
    exit 1
fi

tmp=$(mktemp)
tmpjson=$(mktemp)

for i in ./tests/*.snap ; do
    echo "$i" | grep -q "/test-resquash_" && continue  # test these elsewhere
    for j in "" "--sdk" "--json" ; do
        snap=$(basename "$i")
        echo "= $j $snap ="
        if [ "$testtype" = "snap-review" ]; then
            review-tools.snap-review $j "$i" 2>&1 | sed -e 's#./tests/##g' -e 's/"text": "SKIPPED (could not import apt_pkg)"/"text": "OK"/' | tee "$tmpjson"
        else
            PYTHONPATH=./ ./bin/click-review $j "$i" 2>&1 | sed -e 's#./tests/##g' | tee "$tmpjson"
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
            review-tools.snap-review --allow-classic $j "$i" 2>&1 | sed -e 's#./tests/##g' -e 's/"text": "SKIPPED (could not import apt_pkg)"/"text": "OK"/' | tee "$tmpjson"
        else
            PYTHONPATH=./ ./bin/click-review --allow-classic $j "$i" 2>&1 | sed -e 's#./tests/##g' | tee "$tmpjson"
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

# test-resquash_0.snap takes forever. Just test it with --json
for i in ./tests/test-resquash_*.snap ; do
    snap=$(basename "$i")
    echo "= --json $snap ="
    if [ "$testtype" = "snap-review" ]; then
        review-tools.snap-review --json "$i" 2>&1 | sed -e 's#./tests/##g' -e 's/"text": "SKIPPED (could not import apt_pkg)"/"text": "OK"/' > "$tmpjson"
    else
        PYTHONPATH=./ ./bin/click-review --json "$i" 2>&1 | sed -e 's#./tests/##g' > "$tmpjson"
    fi

    jq '.' "$tmpjson" >/dev/null || {
        echo "'jq . $tmpjson' failed"
        exit 1
    }

    # now show all the output that with the deleted error text
    jq 'del(."snap.v2_security"."error"."security-snap-v2:squashfs_files"."text")' "$tmpjson"

    # now show the error text in a more easily diffable form
    jq '."snap.v2_security"."error"."security-snap-v2:squashfs_files"."text"' "$tmpjson" | sed -e 's/^"//' -e 's/"$//' -e 's/, /\n/g' | sort
done | tee -a "$tmp"

# test RT_EXTRAS_PATH
testsnap="./tests/hello-world_25.snap"
rtpath="./tests/review-tools-extras"
for j in "" "--sdk" "--json" ; do
    snap=$(basename "$testsnap")
    echo "= RT_EXTRAS_PATH with $j $testsnap ="
    if [ "$testtype" = "snap-review" ]; then
        RT_EXTRAS_PATH="$rtpath" review-tools.snap-review $j "$testsnap" 2>&1 | sed -e 's#./tests/##g' -e 's/"text": "SKIPPED (could not import apt_pkg)"/"text": "OK"/' | tee "$tmpjson"
    else
        RT_EXTRAS_PATH="$rtpath" PYTHONPATH=./ ./bin/click-review $j "$testsnap" 2>&1 | sed -e 's#./tests/##g' | tee "$tmpjson"
    fi

    if [ "$j" = "--json" ]; then
        jq '.' "$tmpjson" >/dev/null || {
            echo "'jq . $tmpjson' failed"
            cat "$tmpjson"
            exit 1
        }
    fi
    echo
done | tee -a "$tmp"

echo
echo "Checking for differences in output..."
diff -Naur ./tests/test.sh.expected "$tmp" || {
   echo "Found unexpected differences between './tests/test.sh.expected' and '$tmp'"
   exit 1
}

rm -f "$tmp" "$tmpjson"
echo "Done ($testtype)"
