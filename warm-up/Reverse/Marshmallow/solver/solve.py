#!/usr/bin/env python3
"""Marshmallow solver -- standard library only.

  1. read the shipped, header-less .pyc
  2. skip/repair the 16-byte header and marshal.loads the code object
  3. walk co_consts for the two bytes literals (KEY and TARGET)
  4. invert the per-index transform
"""

import marshal
import os
import sys
import types
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load_pyc_bytes():
    """Find the shipped artifact, whether it is loose or still zipped."""
    loose = os.path.join(ROOT, "dist", "marshmallow.pyc")
    if os.path.exists(loose):
        with open(loose, "rb") as fh:
            return fh.read()
    for archive in (
        os.path.join(ROOT, "dist", "marshmallow.zip"),
        os.path.join(HERE, "marshmallow.zip"),
    ):
        if os.path.exists(archive):
            with zipfile.ZipFile(archive) as zf:
                return zf.read("marshmallow.pyc")
    staged = os.path.join(ROOT, "build", "marshmallow.pyc")
    if os.path.exists(staged):
        with open(staged, "rb") as fh:
            return fh.read()
    sys.exit("cannot find marshmallow.pyc / marshmallow.zip")


def all_consts(code, out=None):
    if out is None:
        out = []
    for const in code.co_consts:
        out.append(const)
        if isinstance(const, types.CodeType):
            all_consts(const, out)
    return out


def forward(text, key):
    out = bytearray()
    for i, ch in enumerate(text):
        x = ord(ch) ^ key[i % len(key)]
        x = ((x << 3) | (x >> 5)) & 0xFF
        x = (x + i * 7) & 0xFF
        out.append(x)
    return bytes(out)


def invert(target, key):
    out = []
    for i, t in enumerate(target):
        x = (t - i * 7) & 0xFF
        x = ((x >> 3) | (x << 5)) & 0xFF
        x ^= key[i % len(key)]
        out.append(x)
    return bytes(out)


def main():
    blob = load_pyc_bytes()

    # the first 16 bytes were zeroed; the marshal payload starts right after
    code = marshal.loads(blob[16:])

    literals = [c for c in all_consts(code) if isinstance(c, bytes)]
    if len(literals) < 2:
        sys.exit("expected at least two bytes literals in co_consts")

    # do not guess which literal is which: try every ordered pair and keep the
    # one whose inverse is a well-formed flag
    flag = None
    for key in literals:
        for target in literals:
            if key is target:
                continue
            cand = invert(target, key)
            try:
                text = cand.decode("ascii")
            except UnicodeDecodeError:
                continue
            if text.startswith("HIBCHB26{") and text.endswith("}"):
                if forward(text, key) == target:
                    flag = text
                    print("[+] KEY    = %r" % (key,))
                    print("[+] TARGET = %r" % (target,))
                    break
        if flag:
            break

    if flag is None:
        sys.exit("failed to recover the flag")

    print("[+] FLAG   = %s" % flag)

    reference = os.path.join(ROOT, "src", "flag.txt")
    if os.path.exists(reference):
        with open(reference, "r", encoding="utf-8") as fh:
            expected = fh.read().strip()
        assert flag == expected, "recovered %r != src/flag.txt %r" % (flag, expected)
        print("[+] matches src/flag.txt")


if __name__ == "__main__":
    main()
