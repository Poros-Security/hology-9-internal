#!/bin/sh
set -eu

version=v0.10.0
archive_name=xollvm-linux-Release.tar.zst
expected=4307e5a64e9e437287c9d1bb64a7e44ec63cc24eaf73f8aebe8653433567f9c3
root=${1:-.tools/xollvm-v0.10.0}
cache=${XOLLVM_CACHE_DIR:-.tools/cache}
archive="$cache/$archive_name"

if [ -x "$root/bin/clang" ]; then
    exit 0
fi

mkdir -p "$cache" "$root"
if [ ! -f "$archive" ]; then
    curl --fail --location --progress-bar \
        "https://github.com/und3ath/xollvm/releases/download/$version/$archive_name" \
        --output "$archive"
fi

printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --status || {
    echo "xollvm archive checksum mismatch: $archive" >&2
    exit 1
}

tar --zstd -xf "$archive" -C "$root" --strip-components=1
test -x "$root/bin/clang" || {
    echo "xollvm clang was not found after extraction" >&2
    exit 1
}
echo "xollvm $version installed at $root"
