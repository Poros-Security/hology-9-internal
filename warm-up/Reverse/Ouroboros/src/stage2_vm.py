"""Ouroboros stage 2 -- the hand-rolled stack VM that actually checks the flag.

This module is compiled by gen.py; only the code object of `_run` is kept, it
is marshalled, encrypted with the key derived from stage 1's own bytecode, and
spliced into stage 1 as a bytes constant. The source is never shipped.

`_run` is rebuilt at runtime with `types.FunctionType(code, globals())`, so it
may only rely on builtins -- no imports, no closures, no module globals.
"""


def _run(candidate):
    PROG = b"__PROG__"
    TGT = __TARGET__
    STATE = __SEED__
    NEED = __FLAGLEN__
    M32 = 0xFFFFFFFF
    M64 = 0xFFFFFFFFFFFFFFFF

    raw = candidate.encode("utf-8", "replace")
    if len(raw) != NEED:
        print("Nope.")
        return
    raw = raw + b"\x00" * (-len(raw) % 4)
    IN = [int.from_bytes(raw[i:i + 4], "little") for i in range(0, len(raw), 4)]

    st = []
    ok = 1
    base = 0
    pc = 0
    while True:
        op = PROG[pc]
        pc += 1
        if op == 0x1D:
            break
        elif op == 0x4A:
            st.append(PROG[pc])
            pc += 1
        elif op == 0x9F:
            st.append(int.from_bytes(PROG[pc:pc + 4], "little"))
            pc += 4
        elif op == 0x22:
            st.append(IN[base + PROG[pc]])
            pc += 1
        elif op == 0x93:
            st.append(TGT[base + PROG[pc]])
            pc += 1
        elif op == 0x6E:
            v = st.pop()
            st.append(st.pop() ^ v)
        elif op == 0xB1:
            v = st.pop()
            st.append((st.pop() + v) & M32)
        elif op == 0x07:
            v = st.pop()
            st.append((st.pop() - v) & M32)
        elif op == 0x55:
            v = st.pop()
            st.append((st.pop() * v) & M32)
        elif op == 0xC4:
            n = PROG[pc] & 31
            pc += 1
            v = st.pop()
            st.append(((v << n) | (v >> (32 - n))) & M32 if n else v)
        elif op == 0x39:
            n = PROG[pc] & 31
            pc += 1
            v = st.pop()
            st.append(((v >> n) | (v << (32 - n))) & M32 if n else v)
        elif op == 0x64:
            n = PROG[pc]
            pc += 1
            st.append(st.pop() >> n)
        elif op == 0x8C:
            STATE = (STATE + 0x9E3779B97F4A7C15) & M64
            z = STATE
            z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & M64
            z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & M64
            st.append((z ^ (z >> 31)) & M32)
        elif op == 0xE0:
            st.append(st[-1])
        elif op == 0x71:
            st[-1], st[-2] = st[-2], st[-1]
        elif op == 0xAB:
            st.pop()
        elif op == 0x16:
            v = st.pop()
            ok &= int(st.pop() == v)
        elif op == 0xD2:
            n = PROG[pc]
            pc += 1
            if st.pop():
                pc += n - 256 if n > 127 else n
        elif op == 0x3E:
            st.append(base)
        elif op == 0xF7:
            base = st.pop()
        else:
            print("Nope.")
            return

    print("Correct!" if ok else "Nope.")
