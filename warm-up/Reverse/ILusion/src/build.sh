#!/usr/bin/env bash
# Build ILusion and stage the player artifacts into ../dist/.
#
#   ./build.sh
#
# Requires: dotnet SDK (targets net48 via Microsoft.NETFramework.ReferenceAssemblies),
#           python3 with dnfile + pycryptodome.
#
# Order matters. The AES key is SHA256 over the compiled IL of
# ILusion.Program.Gate, so ILusion.exe has to exist before Core.dll can be
# encrypted, and ILusion.exe can never be touched afterwards.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SRC")"
DIST="$ROOT/dist"
WORK="$SRC/.build"

EXE="$SRC/outer/bin/Release/net48/ILusion.exe"
DLL="$SRC/core/bin/Release/net48/Core.dll"

rm -rf "$WORK" "$SRC/outer/bin" "$SRC/outer/obj" \
       "$SRC/core/bin" "$SRC/core/obj" \
       "$SRC/packer/keydump/bin" "$SRC/packer/keydump/obj"
mkdir -p "$WORK"

# ---------------------------------------------------------------- stage 3 ---
echo "[*] emitting VM tables from flag.txt"
python3 "$SRC/packer/emit.py" "$SRC/flag.txt" "$SRC/core/Tables.cs"

echo "[*] building Core.dll (stage 2, never written to disk by the player)"
dotnet build "$SRC/core/Core.csproj" -c Release --nologo -v minimal

# ---------------------------------------------------------------- stage 1 ---
echo "[*] building ILusion.exe (loader)"
dotnet build "$SRC/outer/ILusion.csproj" -c Release --nologo -v minimal

[ -f "$EXE" ] && [ -f "$DLL" ] || { echo "[!] build produced no artifacts"; exit 1; }

# --------------------------------------------------------- key parity gate ---
# pack.py parses the method header by hand. KeyDump asks a real CLR the same
# question through reflection. If they disagree, core.bin ships undecryptable.
echo "[*] building KeyDump (verification only - never shipped)"
dotnet build "$SRC/packer/keydump/KeyDump.csproj" -c Release --nologo -v minimal

KD48="$SRC/packer/keydump/bin/Release/net48/KeyDump.exe"
if command -v mono >/dev/null 2>&1; then
    KEYDUMP_HOST="mono / net48"
    keydump() { mono "$KD48" "$EXE"; }
elif [ -n "${WSL_DISTRO_NAME:-}" ] && [ -d /mnt/c/Windows/Microsoft.NET/Framework64/v4.0.30319 ]; then
    # Under WSL the real target runtime is right here; prefer it over any
    # emulation. Windows can only see the files on a drvfs path.
    KDWIN="$(mktemp -d -p /mnt/c/Users/Public keydump.XXXXXX)"
    trap 'rm -rf "$KDWIN"' EXIT
    cp "$KD48" "$EXE" "$KDWIN/"
    KEYDUMP_HOST="Windows .NET Framework 4.8 (WSL interop)"
    # The argument is consumed by Windows, so it has to be a Windows path -
    # a /mnt/c path comes back to it as a \\wsl.localhost UNC and Assembly
    # .LoadFrom refuses to load from the remote zone.
    KDWIN_ARG="$(wslpath -w "$KDWIN/$(basename "$EXE")")"
    keydump() { "$KDWIN/KeyDump.exe" "$KDWIN_ARG" | tr -d '\r'; }
else
    # Same source, same reflection API; .NET loads the net48 assembly fine for
    # metadata and method bodies. Used when neither of the above is available.
    KEYDUMP_HOST="dotnet / net8.0 (no mono, no Windows runtime)"
    keydump() { dotnet "$SRC/packer/keydump/bin/Release/net8.0/KeyDump.dll" "$EXE"; }
fi
echo "[*] ground truth via ${KEYDUMP_HOST}"

read -r RT_LEN RT_ILHASH RT_KEY < <(keydump)
PACK_KEY="$(python3 "$SRC/packer/pack.py" "$EXE" "$DLL" /dev/null --print-key \
            | sed -n 's/^\[\*\] key    : //p')"

echo "    runtime : $RT_KEY  (Gate = $RT_LEN bytes, il sha256 $RT_ILHASH)"
echo "    pack.py : $PACK_KEY"
if [ "$RT_KEY" != "$PACK_KEY" ]; then
    echo "[!] KEY MISMATCH - pack.py's method-header parsing is wrong. Refusing to ship."
    exit 1
fi
echo "[+] key parity OK"

# ------------------------------------------------- anti-tamper self-checks ---
echo "[*] asserting a patched Gate breaks the key"
python3 "$SRC/packer/tamper.py" "$EXE" "$WORK" "$PACK_KEY"

# ----------------------------------------------------------------- packing ---
echo "[*] encrypting Core.dll -> core.bin"
python3 "$SRC/packer/pack.py" "$EXE" "$DLL" "$WORK/core.bin"

# ------------------------------------------------------------- ship checks ---
for f in "$EXE" "$WORK/core.bin"; do
    if grep -aq 'HIBCHB26' "$f"; then
        echo "[!] flag marker present in $(basename "$f")"; exit 1
    fi
done
if grep -aq 'HIBCHB26' "$DLL"; then
    echo "[!] flag marker present in Core.dll (TARGET is not transformed)"; exit 1
fi
echo "[+] no HIBCHB26 marker in any artifact"

echo "[*] staging dist/"
find "$DIST" -mindepth 1 ! -name '.gitignore' -delete
cp "$EXE" "$DIST/ILusion.exe"
cp "$WORK/core.bin" "$DIST/core.bin"

ls -l "$DIST"
echo "[+] done"
