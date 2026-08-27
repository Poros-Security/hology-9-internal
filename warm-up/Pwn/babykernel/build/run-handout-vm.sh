#!/bin/sh
set -eu

DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
echo "[babykernel] Starting VM; the shell can take 20-45 seconds to appear..."
echo
exec qemu-system-x86_64 \
    -m 128M \
    -cpu qemu64 \
    -machine acpi=off \
    -kernel "$DIR/bzImage" \
    -initrd "$DIR/rootfs.cpio.gz" \
    -append "console=ttyS0 root=/dev/ram rdinit=/init quiet nokaslr nosmep nosmap panic=1 oops=panic loglevel=3" \
    -nographic \
    -monitor none \
    -serial stdio \
    -no-reboot \
    -netdev user,id=net0 \
    -device e1000,netdev=net0
