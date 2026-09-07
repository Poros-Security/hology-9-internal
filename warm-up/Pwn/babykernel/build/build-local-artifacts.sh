#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
KVER="${KVER:-$(uname -r)}"
KDIR="${KDIR:-/lib/modules/$KVER/build}"
VMLINUX="${VMLINUX:-/boot/vmlinuz-$KVER}"
NETMOD="${NETMOD:-$(modinfo -F filename e1000 2>/dev/null || true)}"

if [ ! -d "$KDIR" ]; then
    echo "Missing kernel build dir: $KDIR" >&2
    echo "Install matching headers or set KDIR=/path/to/linux-build." >&2
    exit 1
fi
if [ ! -f "$VMLINUX" ]; then
    echo "Missing kernel image: $VMLINUX" >&2
    echo "Set VMLINUX=/path/to/bzImage or /boot/vmlinuz-*" >&2
    exit 1
fi

make -C "$ROOT/src" KDIR="$KDIR" clean
make -C "$ROOT/src" KDIR="$KDIR" all
mkdir -p "$ROOT/assets"
cp "$ROOT/src/hackitbraw.ko" "$ROOT/assets/hackitbraw.ko"
cp "$VMLINUX" "$ROOT/assets/bzImage"
if [ -n "$NETMOD" ] && [ -f "$NETMOD" ]; then
    case "$NETMOD" in
        *.xz) xz -dc "$NETMOD" > "$ROOT/assets/qemu-net.ko" ;;
        *.gz) gzip -dc "$NETMOD" > "$ROOT/assets/qemu-net.ko" ;;
        *) cp "$NETMOD" "$ROOT/assets/qemu-net.ko" ;;
    esac
else
    echo "Warning: missing e1000 module; VM networking may not come up." >&2
fi

echo "Built assets:" >&2
ls -lh "$ROOT/assets/bzImage" "$ROOT/assets/hackitbraw.ko" "$ROOT/assets/qemu-net.ko" 2>/dev/null >&2
