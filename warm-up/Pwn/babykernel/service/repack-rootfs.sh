#!/bin/sh
set -eu

ROOT=/tmp/babykernel-rootfs
OUT=/tmp/rootfs.cpio.gz
FLAG_VALUE="${GZCTF_FLAG:-HIBCHB26{local_test_flag_change_me}}"

rm -rf "$ROOT"
mkdir -p "$ROOT"
cp -a /challenge/rootfs/. "$ROOT/"

mkdir -p "$ROOT/bin" "$ROOT/sbin" "$ROOT/proc" "$ROOT/sys" "$ROOT/dev" \
         "$ROOT/dev/pts" "$ROOT/tmp" "$ROOT/root" "$ROOT/home/ctf"

if [ ! -x "$ROOT/bin/busybox" ]; then
    cp /bin/busybox "$ROOT/bin/busybox"
fi

for app in sh ash cat chmod chown cp echo id insmod ls mkdir mount poweroff ps su \
           setsid cttyhack dmesg uname mknod grep cut sleep base64 tar gzip dd \
           printf stty ifconfig route ip wget; do
    ln -sf /bin/busybox "$ROOT/bin/$app"
done
ln -sf /bin/busybox "$ROOT/sbin/insmod"

if [ ! -f /challenge/assets/hackitbraw.ko ]; then
    echo "[entrypoint] missing /challenge/assets/hackitbraw.ko" >&2
    echo "[entrypoint] run build/build-local-artifacts.sh or copy a matching module into assets/." >&2
    exit 1
fi
cp /challenge/assets/hackitbraw.ko "$ROOT/hackitbraw.ko"
if [ -f /challenge/assets/qemu-net.ko ]; then
    cp /challenge/assets/qemu-net.ko "$ROOT/qemu-net.ko"
fi

printf '%s\n' "$FLAG_VALUE" > "$ROOT/flag"
chmod 0400 "$ROOT/flag"
chmod +x "$ROOT/init"
chown -R 1000:1000 "$ROOT/home/ctf" 2>/dev/null || true

(
    cd "$ROOT"
    find . -print0 | cpio --null -ov --format=newc 2>/dev/null | gzip -9
) > "$OUT"

chmod 0444 "$OUT"
echo "[entrypoint] packed $OUT with runtime flag"
