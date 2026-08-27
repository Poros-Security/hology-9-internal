"""Ouroboros build script.

Order of operations matters -- see the module docstring of obfuscate.py:

    apply source-level obfuscation
      -> compile stage 1
      -> read the FINAL _boot.co_code
      -> derive the key
      -> encrypt both stage-2 variants
      -> code.replace(co_consts=...)
      -> metadata-only obfuscation
      -> marshal + emit

Run through build.sh, not directly.
"""

import importlib.util
import marshal
import os
import shutil
import sys
import types
import zipfile

sys.dont_write_bytecode = True   # keep __pycache__ out of src/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import obfuscate                                                   # noqa: E402
import vmasm                                                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
BUILD = os.path.join(ROOT, "build")
DIST = os.path.join(ROOT, "dist")

M64 = 0xFFFFFFFFFFFFFFFF
DECOY_CORE = "n0t_th3_r34l_0n3_k33p_g01ng"
FILLER_SEED = 0x7A6F4C1E93B5D820
ALT_SEED = 0x2BD4E9317C0A85F6
README = (
    "ouroboros\n"
    "\n"
    "  python ouroboros.pyc\n"
    "\n"
    "then paste the flag on stdin.\n"
)
ZIP_DATE = (1980, 1, 1, 0, 0, 0)


# --- primitives (must match stage1.py byte for byte) ------------------------
def fnv1a(data):
    h = 0xCBF29CE484222325
    for octet in data:
        h ^= octet
        h = (h * 0x100000001B3) & M64
    return h


def keystream(seed, count):
    out = bytearray()
    state = seed
    while len(out) < count:
        state, z = vmasm.splitmix64(state)
        out.extend(z.to_bytes(8, "little"))
    return bytes(out[:count])


def xor(data, seed):
    return bytes(a ^ b for a, b in zip(data, keystream(seed, len(data))))


def filler(seed, count):
    return keystream(seed, count)


# --- helpers ----------------------------------------------------------------
def find_code(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            found = find_code(const, name)
            if found is not None:
                return found
    return None


def build_stage2(prog, target, flaglen):
    """Compile stage2_vm.py with the tables spliced in; return marshalled _run."""
    with open(os.path.join(SRC, "stage2_vm.py"), "r", encoding="utf-8") as fh:
        source = fh.read()
    for marker in ('b"__PROG__"', "__TARGET__", "__SEED__", "__FLAGLEN__"):
        if marker not in source:
            sys.exit("placeholder %s missing from stage2_vm.py" % marker)
    source = source.replace('b"__PROG__"', repr(prog))
    source = source.replace("__TARGET__", repr(target))
    source = source.replace("__SEED__", hex(vmasm.SEED))
    source = source.replace("__FLAGLEN__", str(flaglen))

    module = compile(source, "<ouroboros>", "exec")
    run = find_code(module, "_run")
    if run is None:
        sys.exit("_run not found in compiled stage2")
    return marshal.dumps(run)


def main():
    if sys.version_info[:2] != (3, 12):
        sys.exit("Ouroboros must be built with CPython 3.12, got %s" % sys.version)

    with open(os.path.join(SRC, "flag.txt"), "r", encoding="utf-8") as fh:
        flag = fh.read().strip()
    if not flag.startswith("HIBCHB26{") or not flag.endswith("}"):
        sys.exit("bad flag format in src/flag.txt")

    # the decoy must be indistinguishable in shape: same length, same block count
    pad = len(flag) - len("HIBCHB26{%s}" % DECOY_CORE)
    if pad < 0:
        sys.exit("real flag is shorter than the decoy core; lengthen src/flag.txt")
    decoy = "HIBCHB26{%s%s}" % (DECOY_CORE, "_" * pad)
    assert len(decoy) == len(flag)

    # --- stage 2 -----------------------------------------------------------
    nblocks = len(vmasm.blocks_of(flag.encode()))
    prog = vmasm.assemble(nblocks)
    tgt_real = vmasm.target_for(flag)
    tgt_decoy = vmasm.target_for(decoy)

    # the assembled program must agree with the reference transform
    assert vmasm.execute(prog, vmasm.blocks_of(flag.encode()), tgt_real) == 1
    assert vmasm.execute(prog, vmasm.blocks_of(decoy.encode()), tgt_real) == 0
    assert vmasm.execute(prog, vmasm.blocks_of(decoy.encode()), tgt_decoy) == 1
    assert tgt_real != tgt_decoy

    blob_real = build_stage2(prog, tgt_real, len(flag))
    blob_decoy = build_stage2(prog, tgt_decoy, len(flag))

    # both halves must be the same size; marshal.loads ignores trailing bytes
    span = max(len(blob_real), len(blob_decoy))
    span += -span % 8
    blob_real += filler(FILLER_SEED, span - len(blob_real))
    blob_decoy += filler(FILLER_SEED ^ M64, span - len(blob_decoy))
    assert len(blob_real) == len(blob_decoy) == span
    assert marshal.loads(blob_real).co_name == "_run"
    assert marshal.loads(blob_decoy).co_name == "_run"

    # --- stage 1 -----------------------------------------------------------
    with open(os.path.join(SRC, "stage1.py"), "r", encoding="utf-8") as fh:
        source = fh.read()
    for marker in ('b"__PAYLOAD__"', 'b"__PAYLOAD_ALT__"'):
        if marker not in source:
            sys.exit("placeholder %s missing from stage1.py" % marker)

    placeholder = b"\x00" * (2 * span)
    # bigger than the real payload on purpose: "grep the largest bytes const"
    # is a dead end
    payload_alt = filler(ALT_SEED, 2 * span + 96)
    source = source.replace('b"__PAYLOAD__"', repr(placeholder))
    source = source.replace('b"__PAYLOAD_ALT__"', repr(payload_alt))
    if "HIBCHB26" in source:
        sys.exit("generated stage-1 source still contains the plaintext flag")

    module = compile(source, "ouroboros.py", "exec")

    boot = find_code(module, "_boot")
    if boot is None:
        sys.exit("_boot not found in compiled stage1")
    co_code_before = boot.co_code
    key = fnv1a(co_code_before)

    # --- encrypt: real half at index key&1, decoy half at index (key^1)&1 ---
    sel = key & 1
    cipher_real = xor(blob_real, key)
    cipher_decoy = xor(blob_decoy, key ^ 1)
    halves = [None, None]
    halves[sel] = cipher_real
    halves[sel ^ 1] = cipher_decoy
    payload = halves[0] + halves[1]
    assert len(payload) == len(placeholder)

    # --- splice the ciphertext in without touching any co_code -------------
    consts = list(module.co_consts)
    hits = [i for i, c in enumerate(consts) if c == placeholder]
    if len(hits) != 1:
        sys.exit("expected exactly one PAYLOAD placeholder const, found %d" % len(hits))
    consts[hits[0]] = payload
    module = module.replace(co_consts=tuple(consts))

    before = obfuscate.code_map(module)
    module = obfuscate.scrub(module, drop_doc=True)
    after = obfuscate.code_map(module)
    if before != after:
        sys.exit("obfuscation desynchronised co_code -- the key would be wrong")

    boot = find_code(module, "_boot")
    if boot.co_code != co_code_before:
        sys.exit("_boot.co_code changed after the constant splice")
    if fnv1a(boot.co_code) != key:
        sys.exit("re-derived key differs from the encryption key")

    # --- emit ---------------------------------------------------------------
    shutil.rmtree(BUILD, ignore_errors=True)
    os.makedirs(BUILD)
    os.makedirs(DIST, exist_ok=True)

    header = importlib.util.MAGIC_NUMBER + b"\x00" * 12
    pyc = os.path.join(BUILD, "ouroboros.pyc")
    with open(pyc, "wb") as fh:
        fh.write(header + marshal.dumps(module))

    readme = os.path.join(BUILD, "README.txt")
    with open(readme, "w", encoding="utf-8") as fh:
        fh.write(README)

    zip_path = os.path.join(DIST, "ouroboros.zip")
    if os.path.exists(zip_path):
        os.unlink(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in ("ouroboros.pyc", "README.txt"):
            info = zipfile.ZipInfo(name, date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(os.path.join(BUILD, name), "rb") as fh:
                zf.writestr(info, fh.read())

    print("[+] flag length      : %d (%d blocks)" % (len(flag), nblocks))
    print("[+] VM program       : %d bytes" % len(prog))
    print("[+] stage-2 half     : %d bytes" % span)
    print("[+] _boot co_code    : %d bytes" % len(co_code_before))
    print("[+] derived key      : %#018x (real half at index %d)" % (key, sel))
    print("[+] PAYLOAD          : %d bytes, PAYLOAD_ALT %d bytes"
          % (len(payload), len(payload_alt)))
    print("[+] dist/ouroboros.zip written (%d bytes)" % os.path.getsize(zip_path))


if __name__ == "__main__":
    main()
