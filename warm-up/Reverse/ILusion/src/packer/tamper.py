#!/usr/bin/env python3
"""Build-time proof that the anti-tamper does what the challenge claims.

Two properties, asserted on throwaway copies of the built exe:

  1. Flip any byte inside Gate's IL  -> the derived key changes.
     (Patching or stubbing the loader destroys the key.)

  2. Stub Poison to `ldc.i4.0; ret`  -> the derived key is unchanged.
     (Poison's IL is deliberately not hashed. This is the fair escape hatch:
     a player who neutralises the debugger check can attach dnSpy and the
     core module still decrypts.)

  usage: tamper.py <ILusion.exe> <workdir> <expected-key-hex>
"""
import os
import shutil
import struct
import sys

import dnfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ilmeta import find_methoddef  # noqa: E402
from pack import derive_key  # noqa: E402

NOP = 0x00
LDC_I4_0 = 0x16
RET = 0x2A


def body_range(path, method, type_name):
    """(file offset, length) of the method's IL body, header excluded."""
    pe = dnfile.dnPE(path)
    md = find_methoddef(pe, method, type_name)
    off = pe.get_offset_from_rva(md.Rva)
    first = pe.__data__[off]
    if first & 0x03 == 0x02:
        return off + 1, first >> 2
    return off + 12, struct.unpack_from("<I", pe.__data__, off + 4)[0]


def main():
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    exe, work, expected = sys.argv[1], sys.argv[2], sys.argv[3].strip()

    os.makedirs(work, exist_ok=True)
    rc = 0

    # --- 1. tampering with Gate must break the key ------------------------
    for offset_in_body in (0, 4, -1):
        patched = os.path.join(work, "tamper_gate.exe")
        shutil.copyfile(exe, patched)
        start, length = body_range(patched, "Gate", "ILusion.Program")
        pos = start + (offset_in_body % length)
        with open(patched, "r+b") as fh:
            fh.seek(pos)
            orig = fh.read(1)[0]
            fh.seek(pos)
            fh.write(bytes([orig ^ 0x01]))
        key, _ = derive_key(patched)
        if key.hex() == expected:
            print("[!] patching Gate byte {} did NOT change the key".format(offset_in_body))
            rc = 1
    if rc == 0:
        print("[+] anti-tamper: every patched Gate byte changes the key")

    # --- 2. stubbing Poison must NOT break the key ------------------------
    patched = os.path.join(work, "tamper_poison.exe")
    shutil.copyfile(exe, patched)
    start, length = body_range(patched, "Poison", "ILusion.Program")
    # `ldc.i4.0; ret`, padded with nops and closed with a second ret: .NET
    # Framework's IL importer rejects a body that falls off the end, so the
    # stub has to stay well-formed even though the tail is unreachable.
    stub = bytes([LDC_I4_0, RET] + [NOP] * (length - 4) + [LDC_I4_0, RET])
    with open(patched, "r+b") as fh:
        fh.seek(start)
        fh.write(stub)
    key, _ = derive_key(patched)
    if key.hex() != expected:
        print("[!] stubbing Poison changed the key - the escape hatch is broken")
        rc = 1
    else:
        print("[+] escape hatch: Poison can be stubbed to `return 0` and the key holds")

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
