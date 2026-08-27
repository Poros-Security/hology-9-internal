#!/usr/bin/env python3
"""Encrypt Core.dll under the key that ILusion.exe will derive from itself.

The key is SHA256 over the *live IL* of ILusion.Program.Gate, so this has to
run after the exe is compiled and the exe can never be patched afterwards.

    key = SHA256( GetILAsByteArray(Gate) || b"ILusion/v1" || b"\\x00" )

The trailing byte is Poison(): 0x00 with no debugger attached, 0x5A with one.
Poison lives in its own method and its IL is *not* hashed, so stubbing it out
to `return 0` is a legitimate way in.

  usage: pack.py <ILusion.exe> <Core.dll> <core.bin> [--print-key]
"""
import hashlib
import os
import sys

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

import dnfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ilmeta import method_il  # noqa: E402

SALT = b"ILusion/v1"
POISON_CLEAN = b"\x00"


def derive_key(exe_path):
    pe = dnfile.dnPE(exe_path)
    il = method_il(pe, "Gate", "ILusion.Program")
    return hashlib.sha256(il + SALT + POISON_CLEAN).digest(), il


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if len(args) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    exe_path, dll_path, out_path = args

    key, il = derive_key(exe_path)
    print("[*] Gate IL: {} bytes, sha256 {}".format(
        len(il), hashlib.sha256(il).hexdigest()))
    print("[*] key    : {}".format(key.hex()))

    if "--print-key" in flags:
        return 0

    with open(dll_path, "rb") as fh:
        plain = fh.read()

    iv = os.urandom(16)
    ct = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(plain, AES.block_size))
    with open(out_path, "wb") as fh:
        fh.write(iv + ct)

    print("[+] wrote {} ({} bytes = 16 IV + {} ct)".format(
        out_path, 16 + len(ct), len(ct)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
