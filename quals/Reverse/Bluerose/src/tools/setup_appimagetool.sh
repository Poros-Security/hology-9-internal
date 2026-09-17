#!/bin/sh
set -eu

destination=${1:-.tools/appimagetool-x86_64.AppImage}
version=1.9.1
expected=ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0
url="https://github.com/AppImage/appimagetool/releases/download/${version}/appimagetool-x86_64.AppImage"

if [ -f "$destination" ]; then
    actual=$(sha256sum "$destination" | awk '{print $1}')
    [ "$actual" = "$expected" ] && chmod +x "$destination" && exit 0
    rm -f "$destination"
fi

mkdir -p "$(dirname "$destination")"
temporary="${destination}.download"
rm -f "$temporary"
curl -fL --retry 3 -o "$temporary" "$url"
actual=$(sha256sum "$temporary" | awk '{print $1}')
if [ "$actual" != "$expected" ]; then
    rm -f "$temporary"
    echo "appimagetool checksum mismatch" >&2
    exit 1
fi
chmod +x "$temporary"
mv "$temporary" "$destination"
