#!/bin/sh
if [ -z "$1" ]; then
	cat <<EOF
Usage:	$0 VERSION
	Where VERSION is the version you want to package
	(typically one listed at http://omahaproxy.appspot.com/)
EOF
fi

MYDIR=$(realpath $(dirname $0))

rm -rf v8-tmp
mkdir v8-tmp
cd v8-tmp
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
cd depot_tools
ln -s /usr/bin/gtar tar
export PATH="$(pwd):$PATH"
cd ..
fetch v8
cd v8
git checkout "$1"
gclient sync -D
cd ..
mv v8 "v8-$1"
tar -c --exclude=build/linux --exclude third_party/icu --exclude third_party/binutils --exclude third_party/llvm-build -f "$MYDIR/v8-$1.tar" v8-$1
zstd --ultra -23 --rm "$MYDIR/v8-$1.tar"
