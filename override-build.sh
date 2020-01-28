#!/bin/sh
set -e

#
# Run tests
#

# needed when run from snapcraft
export PYTHONPATH=./
SNAPDIR="$(pwd)"
export MAGIC="$SNAPDIR/../install/usr/share/misc/magic"

RT_IGNORE_TESTS=
if [ -z "$RT_IGNORE_TESTS" ]; then
    # eventually
    #make check
    make functest-updates

    make coverage
    make coverage-report
    make syntax-check
    # eventually
    #make style-check
fi

# eventually
#make check-names

#
# Now fixup
#

# https://insights.ubuntu.com/2017/02/02/run-scripts-during-snapcraft-builds-with-scriptlets/
SNAPDIR="$(pwd)/../install"

# avoid enumerating the architecture by letting the shell find it and going up
#cd "$SNAPDIR"/usr/lib
#echo "Symlinking fakeroot libs to $(pwd)"
#for i in */libfakeroot/*.so ; do
#    ln -s "$i" .
#done

cd "$SNAPDIR"/usr/bin
echo "Symlinking fakeroot-sysv to fakeroot"
ln -sf fakeroot-sysv fakeroot

echo "Patching fakeroot-sysv for snappy paths"
SNAPTMP=$(mktemp -d)
cd "$SNAPTMP"
#shellcheck disable=SC2016
sed -e 's#^FAKEROOT_PREFIX=#FAKEROOT_PREFIX=$SNAP#' \
    -e 's#^FAKEROOT_BINDIR=#FAKEROOT_BINDIR=$SNAP#' \
    -e 's#^PATHS=#PATHS=$SNAP#' \
    "$SNAPDIR"/usr/bin/fakeroot-sysv > ./fakeroot-sysv
mv -f ./fakeroot-sysv "$SNAPDIR"/usr/bin/fakeroot-sysv
chmod 755 "$SNAPDIR"/usr/bin/fakeroot-sysv
cd "$SNAPDIR"

echo "Symlinking libmagic.so (LP: #1861026)"
libmagic=$(find "$SNAPDIR"/usr/lib -name libmagic.so.1.0.0)
libdir=$(dirname "$libmagic")
cd "$libdir"
ln -sf libmagic.so.1.0.0 libmagic.so
cd "$SNAPDIR"

rmdir "$SNAPTMP"
