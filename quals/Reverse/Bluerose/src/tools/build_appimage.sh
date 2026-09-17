#!/bin/sh
set -eu

binary=${1:-bluerose-obfuscated}
flag_file=${2:-flag.enc}
appimagetool=${3:-.tools/appimagetool-x86_64.AppImage}
output=${4:-Bluerose-x86_64.AppImage}
cc=${CC:-gcc}
appdir=build/Bluerose.AppDir

rm -rf "$appdir"
mkdir -p "$appdir/usr/bin" "$appdir/usr/lib" "$appdir/usr/share/bluerose"

install -m 0755 "$binary" "$appdir/usr/bin/bluerose"
install -m 0644 "$flag_file" "$appdir/usr/share/bluerose/flag.enc"
install -m 0644 tools/bluerose.desktop "$appdir/bluerose.desktop"
install -m 0644 assets/cburnett_chess_pieces.png "$appdir/bluerose.png"

loader=$($cc -print-file-name=ld-linux-x86-64.so.2)
libc=$($cc -print-file-name=libc.so.6)
libm=$($cc -print-file-name=libm.so.6)
for dependency in "$loader" "$libc" "$libm"; do
    if [ ! -f "$dependency" ]; then
        echo "unable to locate runtime dependency: $dependency" >&2
        exit 1
    fi
done
install -m 0755 "$loader" "$appdir/usr/lib/ld-linux-x86-64.so.2"
install -m 0755 "$libc" "$appdir/usr/lib/libc.so.6"
install -m 0755 "$libm" "$appdir/usr/lib/libm.so.6"

$cc -std=c11 -O2 -Wall -Wextra -Werror -static -s \
    tools/appimage_launcher.c -o "$appdir/AppRun"

ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$appimagetool" "$appdir" "$output"
chmod +x "$output"
