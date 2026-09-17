#!/bin/sh
set -eu

# Pointer-compressed V8 reserves a 4 GiB virtual cage during startup. The
# Docker cgroup below still limits resident memory; leave enough address space
# for that cage plus the executable and shared libraries.
ulimit -v 16777216 2>/dev/null || true
# dash (Ubuntu's /bin/sh) does not expose the process-count limit; xinetd and
# the container pids limit still bound the process, while other shells can
# apply this extra guard.
ulimit -u 64 2>/dev/null || true
ulimit -n 64 2>/dev/null || true
ulimit -f 1024 2>/dev/null || true

cd /home/ctf

echo "SuiCar Star-Drive Telemetry Console"
echo "Send dashboard JavaScript. End with EOF"

TMP="$(mktemp /tmp/suicar.XXXXXX.js)"
trap 'rm -f "$TMP"' EXIT

while IFS= read -r line; do
    [ "$line" = "EOF" ] && break
    printf '%s\n' "$line" >> "$TMP"
    if [ "$(wc -c < "$TMP")" -gt 262144 ]; then
        echo "script too large"
        exit 1
    fi
done

timeout -k 2s 60s /home/ctf/d8 \
    --allow-natives-syntax --predictable --random-seed=1 \
    /home/ctf/wrapper.js "$TMP" 2>&1 | head -c 65536
