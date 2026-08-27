#!/usr/bin/env bash
# Marshmallow - build the player-facing artifact from src/.
# dist/ is generated; never hand-edit it.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

PYVER="3.11"
IMAGE="python:${PYVER}-slim"

rm -rf build
rm -f dist/marshmallow.zip
mkdir -p dist

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "[*] building inside ${IMAGE}"
    docker run --rm -v "$PWD":/w -w /w "$IMAGE" python src/gen.py
else
    PY="$(command -v "python${PYVER}" || true)"
    if [ -z "$PY" ]; then
        echo "[!] docker is unavailable and python${PYVER} is not on PATH" >&2
        exit 1
    fi
    "$PY" -c "import sys; raise SystemExit(0 if sys.version_info[:2]==(${PYVER/./,}) else 'need CPython ${PYVER}')"
    echo "[*] docker unavailable, falling back to $PY"
    "$PY" src/gen.py
fi

# --- shipped-artifact sanity checks -----------------------------------------
test -f dist/marshmallow.zip || { echo "[!] dist/marshmallow.zip missing" >&2; exit 1; }

if grep -r -a -q 'HIBCHB26' dist/; then
    echo "[!] plaintext flag leaked into dist/" >&2
    exit 1
fi

leak=0
for f in build/marshmallow.pyc build/README.txt; do
    n="$(grep -c -a 'HIBCHB26' "$f" || true)"
    [ "$n" = "0" ] || { echo "[!] plaintext flag in $f" >&2; leak=1; }
done
[ "$leak" = "0" ] || exit 1

# the header really is burned off
head -c 16 build/marshmallow.pyc | tr -d '\000' | wc -c | grep -qx '0' \
    || { echo "[!] pyc header is not zeroed" >&2; exit 1; }

echo "[+] dist/marshmallow.zip"
unzip -l dist/marshmallow.zip 2>/dev/null || true
