"""Marshmallow build script.

Compiles src/chall.py (with TARGET spliced in from src/flag.txt) to a 3.11
.pyc, zeroes the 16-byte pyc header, and emits the player-facing artifact.

Run through build.sh, not directly.
"""

import marshal
import os
import py_compile
import shutil
import sys
import types
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
BUILD = os.path.join(ROOT, "build")
DIST = os.path.join(ROOT, "dist")

KEY = b"t04st3d"
README = "Feed me the flag.\n\n  python marshmallow.pyc <flag>\n"
# fixed timestamp so the zip is byte-reproducible
ZIP_DATE = (1980, 1, 1, 0, 0, 0)


def toast(flag):
    """Reference implementation of the checker transform."""
    out = []
    for i, ch in enumerate(flag):
        x = ord(ch)
        x ^= KEY[i % len(KEY)]
        x = ((x << 3) | (x >> 5)) & 0xFF
        x = (x + i * 7) & 0xFF
        out.append(x)
    return bytes(out)


def walk_consts(code, seen=None):
    if seen is None:
        seen = []
    for const in code.co_consts:
        seen.append(const)
        if isinstance(const, types.CodeType):
            walk_consts(const, seen)
    return seen


def main():
    if sys.version_info[:2] != (3, 11):
        sys.exit("Marshmallow must be built with CPython 3.11, got %s" % sys.version)

    with open(os.path.join(SRC, "flag.txt"), "r", encoding="utf-8") as fh:
        flag = fh.read().strip()
    if not flag.startswith("HIBCHB26{") or not flag.endswith("}"):
        sys.exit("bad flag format in src/flag.txt")

    target = toast(flag)

    with open(os.path.join(SRC, "chall.py"), "r", encoding="utf-8") as fh:
        source = fh.read()
    if 'TARGET = b"__TARGET__"' not in source:
        sys.exit("TARGET placeholder missing from src/chall.py")
    source = source.replace('TARGET = b"__TARGET__"', "TARGET = %r" % (target,))
    if "HIBCHB26" in source:
        sys.exit("generated source still contains the plaintext flag")

    shutil.rmtree(BUILD, ignore_errors=True)
    os.makedirs(BUILD)
    os.makedirs(DIST, exist_ok=True)

    gen_py = os.path.join(BUILD, "marshmallow_gen.py")
    with open(gen_py, "w", encoding="utf-8") as fh:
        fh.write(source)

    pyc = os.path.join(BUILD, "marshmallow.pyc")
    # dfile keeps the original filename out of co_filename
    py_compile.compile(gen_py, cfile=pyc, dfile="marshmallow.py", doraise=True)
    os.unlink(gen_py)

    with open(pyc, "rb") as fh:
        blob = fh.read()

    code = marshal.loads(blob[16:])
    consts = walk_consts(code)
    if target not in consts:
        sys.exit("TARGET did not survive as a literal in co_consts")
    if KEY not in consts:
        sys.exit("KEY did not survive as a literal in co_consts")
    if code.co_filename != "marshmallow.py":
        sys.exit("unexpected co_filename: %r" % code.co_filename)

    # burn the top off: zero the 16-byte pyc header
    blob = b"\x00" * 16 + blob[16:]
    with open(pyc, "wb") as fh:
        fh.write(blob)

    readme = os.path.join(BUILD, "README.txt")
    with open(readme, "w", encoding="utf-8") as fh:
        fh.write(README)

    zip_path = os.path.join(DIST, "marshmallow.zip")
    if os.path.exists(zip_path):
        os.unlink(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in ("marshmallow.pyc", "README.txt"):
            info = zipfile.ZipInfo(name, date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(os.path.join(BUILD, name), "rb") as fh:
                zf.writestr(info, fh.read())

    print("[+] flag length      : %d" % len(flag))
    print("[+] TARGET           : %d bytes" % len(target))
    print("[+] dist/marshmallow.zip written (%d bytes)" % os.path.getsize(zip_path))


if __name__ == "__main__":
    main()
