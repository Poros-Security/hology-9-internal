#!/bin/sh
set -eu

BZIMAGE=/challenge/assets/bzImage
INITRD=/tmp/rootfs.cpio.gz

if [ ! -f "$BZIMAGE" ]; then
    echo "missing $BZIMAGE; copy your challenge kernel to assets/bzImage" >&2
    exit 1
fi
if [ ! -f "$INITRD" ]; then
    echo "missing $INITRD; entrypoint did not pack initramfs" >&2
    exit 1
fi

ACCEL=""
CPU="qemu64"
if [ -e /dev/kvm ] && [ "${USE_KVM:-0}" = "1" ]; then
    ACCEL="-enable-kvm"
    CPU="host"
fi

echo "[babykernel] Starting VM; the shell can take 20-45 seconds to appear..."
echo

exec timeout -k 5 "${SESSION_TIMEOUT:-300}" \
    qemu-system-x86_64 \
    $ACCEL \
    -m "${QEMU_MEM:-128M}" \
    -cpu "$CPU" \
    -machine acpi=off \
    -kernel "$BZIMAGE" \
    -initrd "$INITRD" \
    -append "console=ttyS0 root=/dev/ram rdinit=/init quiet nokaslr nosmep nosmap panic=1 oops=panic loglevel=3" \
    -nographic \
    -monitor none \
    -serial stdio \
    -no-reboot \
    -netdev user,id=net0 \
    -device e1000,netdev=net0
