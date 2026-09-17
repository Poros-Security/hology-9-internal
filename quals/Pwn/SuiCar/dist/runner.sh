#!/bin/sh
set -eu

ulimit -v 16777216 2>/dev/null || true

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
