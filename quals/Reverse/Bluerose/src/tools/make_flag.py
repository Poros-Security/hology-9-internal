#!/usr/bin/env python3

import hashlib
from pathlib import Path
import struct
import sys

from solve_reference import derive_key, stream_xor


def main():
    if len(sys.argv) != 2 or not (1 <= len(sys.argv[1].encode()) <= 4096):
        raise SystemExit(f"usage: {sys.argv[0]} 'flag{{...}}'")
    plaintext = sys.argv[1].encode()
    master, _ = derive_key()
    enc = hashlib.blake2s(b"BRSE-ENC-v1", key=master).digest()
    mac = hashlib.blake2s(b"BRSE-MAC-v1", key=master).digest()
    nonce = hashlib.blake2s(b"BRSE-NONCE-v1" + plaintext, key=master, digest_size=12).digest()
    ciphertext = stream_xor(plaintext, enc, nonce)
    header = b"BRSE" + struct.pack("<HHI", 1, 0, len(ciphertext)) + nonce
    tag = hashlib.blake2s(header + ciphertext, key=mac).digest()
    output = Path(__file__).resolve().parents[1] / "flag.enc"
    output.write_bytes(header + ciphertext + tag)
    print(f"wrote {output} ({len(plaintext)} encrypted bytes)")


if __name__ == "__main__":
    main()
