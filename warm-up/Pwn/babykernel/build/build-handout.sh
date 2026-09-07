#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DIST="$ROOT/dist"

if [ ! -f "$ROOT/assets/bzImage" ] || [ ! -f "$ROOT/assets/hackitbraw.ko" ]; then
    echo "Missing assets/bzImage or assets/hackitbraw.ko." >&2
    echo "Run build/build-local-artifacts.sh first, or copy matching files manually." >&2
    exit 1
fi

rm -rf "$DIST"
mkdir -p "$DIST"
cp "$ROOT/assets/bzImage" "$DIST/bzImage"
cp "$ROOT/assets/hackitbraw.ko" "$DIST/hackitbraw.ko"
cp "$ROOT/solver/exploit.c" "$DIST/exploit-template.c"
cp "$ROOT/build/run-handout-vm.sh" "$DIST/run.sh"
chmod +x "$DIST/run.sh"
cat > "$DIST/System.map.txt" <<'MAP'
ffffffff810d3960 T commit_creds
ffffffff810d3c10 T prepare_kernel_cred
ffffffff82a5bc80 D init_cred
MAP

GZCTF_FLAG='HIBCHB26{redacted_remote_is_dynamic}' /challenge/service/repack-rootfs.sh 2>/dev/null || \
    GZCTF_FLAG='HIBCHB26{redacted_remote_is_dynamic}' "$ROOT/service/repack-rootfs-local.sh"
cp /tmp/rootfs.cpio.gz "$DIST/rootfs.cpio.gz"
ls -lh "$DIST"
