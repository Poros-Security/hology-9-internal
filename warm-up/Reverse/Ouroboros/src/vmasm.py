"""Assembler + reference model for the Ouroboros stage-2 stack VM.

Author-side only. Nothing here is shipped; the players get the assembled
`PROG` bytes buried inside an encrypted code object.

The machine is 32-bit. It has an operand stack, one index register `B`
(used to walk the input/target arrays), a chained SplitMix64 generator, and a
sticky `ok` accumulator that `CMP` folds comparisons into.
"""

M32 = 0xFFFFFFFF
M64 = 0xFFFFFFFFFFFFFFFF

# --- opcode table -----------------------------------------------------------
# deliberately shuffled and non-sequential; the operand width is the second
# element (0 = no operand, 1 = one immediate byte, 4 = one LE dword)
OPS = {
    "HALT":   (0x1D, 0),
    "PUSHI":  (0x4A, 1),
    "PUSHW":  (0x9F, 4),
    "LOADIN": (0x22, 1),
    "LOADT":  (0x93, 1),
    "XOR":    (0x6E, 0),
    "ADD":    (0xB1, 0),
    "SUB":    (0x07, 0),
    "MUL":    (0x55, 0),
    "ROTL":   (0xC4, 1),
    "ROTR":   (0x39, 1),
    "SHR":    (0x64, 1),
    "RNG":    (0x8C, 0),
    "DUP":    (0xE0, 0),
    "SWAP":   (0x71, 0),
    "POP":    (0xAB, 0),
    "CMP":    (0x16, 0),
    "JNZ":    (0xD2, 1),
    "PUSHB":  (0x3E, 0),
    "SETB":   (0xF7, 0),
}

BY_CODE = {code: (name, width) for name, (code, width) in OPS.items()}

# --- flag-check parameters --------------------------------------------------
SEED = 0x1D872B41A17F2E6D
ODD_CONST = 0x9E3779B1          # odd => invertible mod 2**32
ROUNDS = (7, 11, 17, 5)         # rotate amount per round
XORSHIFT = 13


def splitmix64(state):
    state = (state + 0x9E3779B97F4A7C15) & M64
    z = state
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & M64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & M64
    return state, (z ^ (z >> 31)) & M64


def rotl(v, n):
    n &= 31
    return ((v << n) | (v >> (32 - n))) & M32 if n else v


def assemble(nblocks):
    """Emit the VM program: one loop iteration per 4-byte block."""
    prog = bytearray()

    def emit(name, arg=None):
        code, width = OPS[name]
        prog.append(code)
        if width == 1:
            prog.append(arg & 0xFF)
        elif width == 4:
            prog.extend((arg & M32).to_bytes(4, "little"))
        elif arg is not None:
            raise ValueError("%s takes no operand" % name)

    top = len(prog)
    emit("LOADIN", 0)                       # b = input[B]
    for r in ROUNDS:
        emit("RNG")                         # b ^= rng_next()
        emit("XOR")
        emit("ROTL", r)                     # b = rotl(b, r)
        emit("PUSHW", ODD_CONST)            # b = (b * ODD_CONST) & M32
        emit("MUL")
        emit("DUP")                         # b ^= b >> 13
        emit("SHR", XORSHIFT)
        emit("XOR")
    emit("LOADT", 0)                        # ok &= (b == target[B])
    emit("CMP")
    emit("PUSHB")                           # B += 1
    emit("PUSHI", 1)
    emit("ADD")
    emit("SETB")
    emit("PUSHB")                           # loop while B - nblocks != 0
    emit("PUSHI", nblocks)
    emit("SUB")
    back = top - (len(prog) + 2)
    if not -128 <= back <= 127:
        raise ValueError("loop body too large for a signed byte branch")
    emit("JNZ", back)
    emit("HALT")
    return bytes(prog)


def blocks_of(raw):
    raw = raw + b"\x00" * (-len(raw) % 4)
    return [int.from_bytes(raw[i:i + 4], "little") for i in range(0, len(raw), 4)]


def target_for(text):
    """Reference forward transform -- what the VM must reproduce."""
    state = SEED
    out = []
    for b in blocks_of(text.encode("utf-8")):
        for r in ROUNDS:
            state, rv = splitmix64(state)
            b ^= rv & M32
            b = rotl(b, r)
            b = (b * ODD_CONST) & M32
            b ^= b >> XORSHIFT
        out.append(b)
    return tuple(out)


def execute(prog, inp, target, seed=SEED):
    """Independent model of the stage-2 interpreter, used to verify `assemble`."""
    st = []
    ok = 1
    base = 0
    state = seed
    pc = 0
    while True:
        op = prog[pc]
        pc += 1
        name, width = BY_CODE[op]
        if width == 1:
            arg = prog[pc]
            pc += 1
        elif width == 4:
            arg = int.from_bytes(prog[pc:pc + 4], "little")
            pc += 4
        else:
            arg = None

        if name == "HALT":
            break
        elif name == "PUSHI" or name == "PUSHW":
            st.append(arg)
        elif name == "LOADIN":
            st.append(inp[base + arg])
        elif name == "LOADT":
            st.append(target[base + arg])
        elif name == "XOR":
            b = st.pop(); st.append(st.pop() ^ b)
        elif name == "ADD":
            b = st.pop(); st.append((st.pop() + b) & M32)
        elif name == "SUB":
            b = st.pop(); st.append((st.pop() - b) & M32)
        elif name == "MUL":
            b = st.pop(); st.append((st.pop() * b) & M32)
        elif name == "ROTL":
            st.append(rotl(st.pop(), arg))
        elif name == "ROTR":
            st.append(rotl(st.pop(), 32 - (arg & 31)))
        elif name == "SHR":
            st.append(st.pop() >> arg)
        elif name == "RNG":
            state, rv = splitmix64(state)
            st.append(rv & M32)
        elif name == "DUP":
            st.append(st[-1])
        elif name == "SWAP":
            st[-1], st[-2] = st[-2], st[-1]
        elif name == "POP":
            st.pop()
        elif name == "CMP":
            b = st.pop(); ok &= int(st.pop() == b)
        elif name == "JNZ":
            if st.pop():
                pc += arg - 256 if arg > 127 else arg
        elif name == "PUSHB":
            st.append(base)
        elif name == "SETB":
            base = st.pop()
        else:
            raise ValueError("bad opcode %#x" % op)
    return ok


def disasm(prog):
    """Human-readable listing (used in the writeup)."""
    lines = []
    pc = 0
    while pc < len(prog):
        at = pc
        name, width = BY_CODE[prog[pc]]
        pc += 1
        if width == 1:
            val = prog[pc]
            if name == "JNZ":
                val = val - 256 if val > 127 else val
                text = "%-7s %+d   -> %d" % (name, val, pc + 1 + val)
            else:
                text = "%-7s %d" % (name, val)
            pc += 1
        elif width == 4:
            text = "%-7s %#010x" % (name, int.from_bytes(prog[pc:pc + 4], "little"))
            pc += 4
        else:
            text = name
        lines.append("%04d  %s" % (at, text))
    return "\n".join(lines)


if __name__ == "__main__":
    demo = "HIBCHB26{demo}"
    prog = assemble(len(blocks_of(demo.encode())))
    print(disasm(prog))
    print()
    tgt = target_for(demo)
    assert execute(prog, blocks_of(demo.encode()), tgt) == 1
    assert execute(prog, blocks_of(b"x" * len(demo)), tgt) == 0
    print("self-test ok (%d bytes of VM program)" % len(prog))
