#!/bin/sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
ROOT=/tmp/babykernel-rootfs
OUT=/tmp/rootfs.cpio.gz
FLAG_VALUE="${GZCTF_FLAG:-HIBCHB26{local_test_flag_change_me}}"

rm -rf "$ROOT"
mkdir -p "$ROOT"
cp -a "$ROOT_DIR/rootfs/." "$ROOT/"
mkdir -p "$ROOT/bin" "$ROOT/sbin" "$ROOT/proc" "$ROOT/sys" "$ROOT/dev" "$ROOT/dev/pts" "$ROOT/tmp" "$ROOT/root" "$ROOT/home/ctf"

BUSYBOX="${BUSYBOX:-/bin/busybox}"
if [ ! -x "$BUSYBOX" ]; then
    echo "Missing static busybox at $BUSYBOX. Set BUSYBOX=/path/to/static/busybox." >&2
    exit 1
fi
if file "$BUSYBOX" | grep -q 'dynamically linked'; then
    echo "BusyBox must be statically linked: $BUSYBOX" >&2
    echo "Install busybox-static or set BUSYBOX=/path/to/static/busybox." >&2
    exit 1
fi
cp "$BUSYBOX" "$ROOT/bin/busybox"
for app in sh ash cat chmod chown cp echo id insmod ls mkdir mount poweroff ps su \
           setsid cttyhack dmesg uname mknod grep cut sleep base64 tar gzip dd \
           printf stty ifconfig route ip wget; do
    ln -sf /bin/busybox "$ROOT/bin/$app"
done
ln -sf /bin/busybox "$ROOT/sbin/insmod"

cp "$ROOT_DIR/assets/hackitbraw.ko" "$ROOT/hackitbraw.ko"
if [ -f "$ROOT_DIR/assets/qemu-net.ko" ]; then
    cp "$ROOT_DIR/assets/qemu-net.ko" "$ROOT/qemu-net.ko"
fi
printf '%s\n' "$FLAG_VALUE" > "$ROOT/flag"
chmod 0400 "$ROOT/flag"
chmod +x "$ROOT/init"

(
    cd "$ROOT"
    find . -print0 | cpio --null -ov --format=newc 2>/dev/null | gzip -9
) > "$OUT"

echo "packed $OUT"
