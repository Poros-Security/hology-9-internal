#!/usr/bin/env python3
"""Ouroboros solver -- standard library only, CPython 3.12.

  1. unmarshal the shipped .pyc
  2. find the code object whose FNV-1a(co_code) decrypts one half of a bytes
     constant into another code object -- that is _boot, and that is the key
  3. pull PROG / TARGET / SEED out of the decrypted stage-2 code object
  4. symbolically disassemble the VM program to recover the round structure
  5. invert the rounds, replaying the chained SplitMix64 block by block

Nothing is hardcoded: the key, the opcode semantics, the rotate amounts, the
odd multiplier and the seed all come out of the artifact.
"""

import marshal
import os
import sys
import types
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

M32 = 0xFFFFFFFF
M64 = 0xFFFFFFFFFFFFFFFF

# opcode -> (mnemonic, operand width); recovered by reading the stage-2 dis
OPS = {
    0x1D: ("HALT", 0), 0x4A: ("PUSHI", 1), 0x9F: ("PUSHW", 4),
    0x22: ("LOADIN", 1), 0x93: ("LOADT", 1), 0x6E: ("XOR", 0),
    0xB1: ("ADD", 0), 0x07: ("SUB", 0), 0x55: ("MUL", 0),
    0xC4: ("ROTL", 1), 0x39: ("ROTR", 1), 0x64: ("SHR", 1),
    0x8C: ("RNG", 0), 0xE0: ("DUP", 0), 0x71: ("SWAP", 0),
    0xAB: ("POP", 0), 0x16: ("CMP", 0), 0xD2: ("JNZ", 1),
    0x3E: ("PUSHB", 0), 0xF7: ("SETB", 0),
}


# --- primitives -------------------------------------------------------------
def fnv1a(data):
    h = 0xCBF29CE484222325
    for octet in data:
        h ^= octet
        h = (h * 0x100000001B3) & M64
    return h


def splitmix64(state):
    state = (state + 0x9E3779B97F4A7C15) & M64
    z = state
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & M64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & M64
    return state, (z ^ (z >> 31)) & M64


def keystream(seed, count):
    out = bytearray()
    state = seed
    while len(out) < count:
        state, z = splitmix64(state)
        out.extend(z.to_bytes(8, "little"))
    return bytes(out[:count])


def rotl(v, n):
    n &= 31
    return ((v << n) | (v >> (32 - n))) & M32 if n else v


def unxorshr(y, n):
    """Invert y = x ^ (x >> n) over 32 bits."""
    x = y
    for _ in range(-(-32 // n)):
        x = y ^ (x >> n)
    return x & M32


# --- artifact loading -------------------------------------------------------
def load_pyc_bytes():
    loose = os.path.join(ROOT, "dist", "ouroboros.pyc")
    if os.path.exists(loose):
        with open(loose, "rb") as fh:
            return fh.read()
    for archive in (os.path.join(ROOT, "dist", "ouroboros.zip"),
                    os.path.join(HERE, "ouroboros.zip")):
        if os.path.exists(archive):
            with zipfile.ZipFile(archive) as zf:
                return zf.read("ouroboros.pyc")
    staged = os.path.join(ROOT, "build", "ouroboros.pyc")
    if os.path.exists(staged):
        with open(staged, "rb") as fh:
            return fh.read()
    sys.exit("cannot find ouroboros.pyc / ouroboros.zip")


def walk_codes(code, out=None):
    if out is None:
        out = [code]
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            out.append(const)
            walk_codes(const, out)
    return out


def walk_consts(code, out=None):
    if out is None:
        out = []
    for const in code.co_consts:
        out.append(const)
        if isinstance(const, types.CodeType):
            walk_consts(const, out)
    return out


def xor(data, seed):
    return bytes(a ^ b for a, b in zip(data, keystream(seed, len(data))))


def try_unmarshal(blob):
    try:
        obj = marshal.loads(blob)
    except Exception:
        return None
    return obj if isinstance(obj, types.CodeType) else None


def unpack_stage2(module):
    """Find (key, real stage-2, decoy stage-2) without trusting any name."""
    blobs = [c for c in walk_consts(module) if isinstance(c, bytes) and len(c) > 64]
    for code in walk_codes(module):
        key = fnv1a(code.co_code)
        for blob in blobs:
            span = len(blob) >> 1
            head = (key & 1) * span
            real = try_unmarshal(xor(blob[head:head + span], key))
            if real is None:
                continue
            alt_head = ((key ^ 1) & 1) * span
            decoy = try_unmarshal(xor(blob[alt_head:alt_head + span], key ^ 1))
            return code, key, real, decoy
    sys.exit("no code object hashes to a working decryption key")


# --- VM program analysis ----------------------------------------------------
def decode(prog):
    out = []
    pc = 0
    while pc < len(prog):
        at = pc
        name, width = OPS[prog[pc]]
        pc += 1
        if width == 1:
            arg = prog[pc]
            if name == "JNZ" and arg > 127:
                arg -= 256
            pc += 1
        elif width == 4:
            arg = int.from_bytes(prog[pc:pc + 4], "little")
            pc += 4
        else:
            arg = None
        out.append((at, name, arg))
    return out


def disasm(prog):
    lines = []
    for at, name, arg in decode(prog):
        lines.append("%04d  %s" % (at, name if arg is None else "%-7s %s" % (name, arg)))
    return "\n".join(lines)


SYM = ("sym",)
RNG = ("rng",)


def pipeline(prog):
    """Symbolically execute one loop body: LOADIN ... LOADT -> list of ops."""
    ops = []
    stack = []
    started = False
    for _at, name, arg in decode(prog):
        if name == "LOADIN":
            stack.append(SYM)
            started = True
            continue
        if not started:
            continue
        if name == "LOADT":
            break
        if name == "RNG":
            stack.append(RNG)
        elif name in ("PUSHI", "PUSHW"):
            stack.append(("const", arg))
        elif name == "DUP":
            stack.append(stack[-1])
        elif name == "SWAP":
            stack[-1], stack[-2] = stack[-2], stack[-1]
        elif name == "POP":
            stack.pop()
        elif name == "SHR":
            top = stack.pop()
            assert top == SYM, "unexpected SHR operand"
            stack.append(("shr", arg))
        elif name in ("ROTL", "ROTR"):
            assert stack.pop() == SYM
            ops.append((name.lower(), arg))
            stack.append(SYM)
        elif name == "XOR":
            b, a = stack.pop(), stack.pop()
            pair = {a[0], b[0]}
            if pair == {"sym", "rng"}:
                ops.append(("xorrng", None))
            elif pair == {"sym", "shr"}:
                shift = a[1] if a[0] == "shr" else b[1]
                ops.append(("xorshr", shift))
            else:
                raise AssertionError("unexpected XOR operands %r %r" % (a, b))
            stack.append(SYM)
        elif name in ("MUL", "ADD", "SUB"):
            b, a = stack.pop(), stack.pop()
            const = a if a[0] == "const" else b
            assert const[0] == "const", "unexpected %s operands" % name
            ops.append((name.lower(), const[1]))
            stack.append(SYM)
        else:
            raise AssertionError("unexpected opcode %s inside the block pipeline" % name)
    return ops


def invert_block(value, ops, rngs):
    """Undo one block. `rngs` holds this block's RNG outputs in forward order."""
    feed = list(rngs)
    for name, arg in reversed(ops):
        if name == "xorrng":
            value ^= feed.pop()
        elif name == "xorshr":
            value = unxorshr(value, arg)
        elif name == "rotl":
            value = rotl(value, 32 - (arg & 31)) if arg & 31 else value
        elif name == "rotr":
            value = rotl(value, arg)
        elif name == "mul":
            value = (value * pow(arg, -1, 1 << 32)) & M32
        elif name == "add":
            value = (value - arg) & M32
        elif name == "sub":
            value = (value + arg) & M32
        else:
            raise AssertionError("cannot invert %s" % name)
    return value & M32


def recover(target, ops, seed):
    draws = sum(1 for name, _ in ops if name == "xorrng")
    state = seed
    raw = bytearray()
    for word in target:
        rngs = []
        for _ in range(draws):
            state, z = splitmix64(state)
            rngs.append(z & M32)
        raw.extend(invert_block(word, ops, rngs).to_bytes(4, "little"))
    return bytes(raw).rstrip(b"\x00")


# --- driver -----------------------------------------------------------------
def solve_stage2(stage2, label):
    consts = list(stage2.co_consts)
    prog = max((c for c in consts if isinstance(c, bytes)), key=len)
    targets = [c for c in consts if isinstance(c, tuple) and c
               and all(isinstance(v, int) for v in c)]
    target = max(targets, key=len)
    ops = pipeline(prog)

    # the seed is just another int constant; identify it by what it produces
    for cand in sorted({c for c in consts if isinstance(c, int) and c > M32},
                       reverse=True):
        raw = recover(target, ops, cand)
        try:
            text = raw.decode("ascii")
        except UnicodeDecodeError:
            continue
        if text.startswith("HIBCHB26{") and text.endswith("}"):
            return prog, ops, cand, text
    sys.exit("could not recover a flag from %s" % label)


def main():
    if sys.version_info[:2] != (3, 12):
        sys.exit("run me with CPython 3.12 -- marshal is version locked")

    module = marshal.loads(load_pyc_bytes()[16:])
    boot, key, stage2, decoy = unpack_stage2(module)

    print("[+] loader code object : %s (%d bytes of co_code)"
          % (boot.co_name, len(boot.co_code)))
    print("[+] FNV-1a key         : %#018x" % key)
    print("[+] stage 2            : %s, half index %d" % (stage2.co_name, key & 1))

    prog, ops, seed, flag = solve_stage2(stage2, "stage 2")

    print("[+] VM program         : %d bytes" % len(prog))
    print("[+] block pipeline     : %s" % " -> ".join(
        n if a is None else "%s(%s)" % (n, a if n != "mul" else hex(a)) for n, a in ops))
    print("[+] SplitMix64 seed    : %#018x" % seed)
    print("[+] FLAG               : %s" % flag)

    if decoy is not None:
        try:
            _, _, _, fake = solve_stage2(decoy, "decoy")
            print("[+] decoy (traced run) : %s" % fake)
        except SystemExit:
            pass

    reference = os.path.join(ROOT, "src", "flag.txt")
    if os.path.exists(reference):
        with open(reference, "r", encoding="utf-8") as fh:
            expected = fh.read().strip()
        assert flag == expected, "recovered %r != src/flag.txt %r" % (flag, expected)
        print("[+] matches src/flag.txt")

    if "-v" in sys.argv:
        print("\n--- VM program ---")
        print(disasm(prog))


if __name__ == "__main__":
    main()
