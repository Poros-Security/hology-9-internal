#!/usr/bin/env bash
# Ouroboros - build the player-facing artifact from src/.
# dist/ is generated; never hand-edit it.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

PYVER="3.12"
IMAGE="python:${PYVER}-slim"

rm -rf build
rm -f dist/ouroboros.zip
mkdir -p dist

RUN=()
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "[*] building inside ${IMAGE}"
    RUN=(docker run --rm -i -v "$PWD":/w -w /w "$IMAGE" python)
else
    PY="$(command -v "python${PYVER}" || true)"
    if [ -z "$PY" ]; then
        echo "[!] docker is unavailable and python${PYVER} is not on PATH" >&2
        exit 1
    fi
    "$PY" -c "import sys; raise SystemExit(0 if sys.version_info[:2]==(${PYVER/./,}) else 'need CPython ${PYVER}')"
    echo "[*] docker unavailable, falling back to $PY"
    RUN=("$PY")
fi

"${RUN[@]}" src/gen.py

# --- shipped-artifact sanity checks -----------------------------------------
test -f dist/ouroboros.zip || { echo "[!] dist/ouroboros.zip missing" >&2; exit 1; }

if grep -r -a -q 'HIBCHB26' dist/; then
    echo "[!] plaintext flag leaked into dist/" >&2
    exit 1
fi

leak=0
for f in build/ouroboros.pyc build/README.txt; do
    n="$(grep -c -a 'HIBCHB26' "$f" || true)"
    [ "$n" = "0" ] || { echo "[!] plaintext flag in $f" >&2; leak=1; }
done
[ "$leak" = "0" ] || exit 1

FLAG="$(tr -d '\n' < src/flag.txt)"

check() { # label expected actual
    if [ "$2" = "$3" ]; then
        echo "[+] $1: $3"
    else
        echo "[!] $1: expected '$2', got '$3'" >&2
        exit 1
    fi
}

got="$(printf '%s\n' "$FLAG" | "${RUN[@]}" build/ouroboros.pyc | tail -c 9)"
check "correct flag" "Correct!" "$got"

got="$(printf 'HIBCHB26{aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa}\n' | "${RUN[@]}" build/ouroboros.pyc | tail -c 6)"
check "wrong flag" "Nope." "$got"

got="$(printf '\n' | "${RUN[@]}" build/ouroboros.pyc | tail -c 6)"
check "empty input" "Nope." "$got"

# the anti-tamper invariant: _boot's co_code must survive the constant splice,
# and the real flag must be rejected the moment a tracer is attached
"${RUN[@]}" - "$FLAG" <<'PYEOF'
import io, marshal, sys, types

flag = sys.argv[1]
module = marshal.loads(open("build/ouroboros.pyc", "rb").read()[16:])


def find(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            hit = find(const, name)
            if hit is not None:
                return hit
    return None


boot = find(module, "_boot")
assert boot is not None, "_boot missing from the shipped pyc"
assert boot.co_filename == "<frozen importlib._bootstrap>", boot.co_filename
assert boot.co_linetable == b"", "line table not blanked"
assert set(boot.co_varnames) <= set("lI1") | {""} or all(
    set(v) <= set("lI1") for v in boot.co_varnames), boot.co_varnames

buf = io.StringIO()
saved_out, saved_in = sys.stdout, sys.stdin
sys.stdout, sys.stdin = buf, io.StringIO(flag + "\n")
sys.settrace(lambda *a: None)
try:
    exec(module, {"__name__": "__main__"})
finally:
    sys.settrace(None)
    sys.stdout, sys.stdin = saved_out, saved_in
assert buf.getvalue().strip().endswith("Nope."), "traced run accepted the real flag"
print("[+] traced run rejects the real flag (decoy stage 2 engaged)")

# patching a single byte of _boot must break decryption
patched = bytearray(boot.co_code)
patched[0] = 0x09  # NOP over RESUME


def repatch(code):
    consts = []
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            consts.append(const.replace(co_code=bytes(patched))
                          if const.co_name == "_boot" else repatch(const))
        else:
            consts.append(const)
    return code.replace(co_consts=tuple(consts))


sys.stdout, sys.stdin = io.StringIO(), io.StringIO(flag + "\n")
try:
    exec(repatch(module), {"__name__": "__main__"})
except Exception:
    ok = True
else:
    ok = False
finally:
    sys.stdout, sys.stdin = saved_out, saved_in
assert ok, "patched _boot still decrypted the payload"
print("[+] patching _boot.co_code breaks decryption")
PYEOF

echo "[+] dist/ouroboros.zip"
unzip -l dist/ouroboros.zip 2>/dev/null || true
