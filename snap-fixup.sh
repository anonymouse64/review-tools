#!/bin/sh
set -e
set -x

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
ln -s fakeroot-sysv fakeroot

echo "Patching fakeroot-sysv for snappy paths"
SNAPTMP=$(mktemp -d)
cd "$SNAPTMP"
sed -e 's#^FAKEROOT_PREFIX=#FAKEROOT_PREFIX=$SNAP#' \
    -e 's#^FAKEROOT_BINDIR=#FAKEROOT_BINDIR=$SNAP#' \
    -e 's#^PATHS=#PATHS=$SNAP#' \
    "$SNAPDIR"/usr/bin/fakeroot-sysv > ./fakeroot-sysv
mv -f ./fakeroot-sysv "$SNAPDIR"/usr/bin/fakeroot-sysv
chmod 755 "$SNAPDIR"/usr/bin/fakeroot-sysv

rmdir "$SNAPTMP"
