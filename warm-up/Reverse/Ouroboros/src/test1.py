#!/usr/bin/env python3
"""
VM simulator to trace the transformation applied to each input integer.
Usage: python3 vm_trace.py ouroboros.pyc
"""
import marshal
import struct
import sys

MASK64 = 0xFFFFFFFFFFFFFFFF
M32 = 0xFFFFFFFF

def fnv1a(data):
    h = 0xcbf29ce484222325
    for b in data:
        h = ((h ^ b) * 0x100000001B3) & MASK64
    return h

def splitmix64_full(seed):
    state = seed
    while True:
        state = (state + 0x9E3779B97F4A7C15) & MASK64
        z = state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
        z ^= (z >> 31)
        yield z

# ---------- VM implementation ----------
def run_vm(IN, TGT, PROG, init_state):
    st = []
    ok = 1
    base = 0
    pc = 0
    STATE = init_state
    # PRNG function
    def rand():
        nonlocal STATE
        STATE = (STATE + 0x9E3779B97F4A7C15) & MASK64
        z = STATE
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
        z ^= (z >> 31)
        return z & M32

    while True:
        op = PROG[pc]
        pc += 1
        if op == 29:  # END
            break
        elif op == 74:  # PUSH_IMM8
            v = PROG[pc]; pc += 1
            st.append(v)
        elif op == 159:  # PUSH_IMM32
            v = int.from_bytes(PROG[pc:pc+4], 'little'); pc += 4
            st.append(v)
        elif op == 34:  # PUSH_IN
            idx = PROG[pc]; pc += 1
            st.append(IN[base + idx])
        elif op == 147:  # PUSH_TGT
            idx = PROG[pc]; pc += 1
            st.append(TGT[base + idx])
        elif op == 110:  # XOR
            b = st.pop(); a = st.pop()
            st.append((a ^ b) & M32)
        elif op == 177:  # ADD
            b = st.pop(); a = st.pop()
            st.append((a + b) & M32)
        elif op == 7:  # SUB
            b = st.pop(); a = st.pop()
            st.append((a - b) & M32)
        elif op == 85:  # MUL
            b = st.pop(); a = st.pop()
            st.append((a * b) & M32)
        elif op == 196:  # ROTL
            n = PROG[pc] & 31; pc += 1
            v = st.pop()
            if n:
                v = ((v << n) | (v >> (32 - n))) & M32
            st.append(v)
        elif op == 57:  # ROTR
            n = PROG[pc] & 31; pc += 1
            v = st.pop()
            if n:
                v = ((v >> n) | (v << (32 - n))) & M32
            st.append(v)
        elif op == 100:  # SHR
            n = PROG[pc]; pc += 1
            v = st.pop()
            st.append(v >> n)
        elif op == 140:  # RAND
            st.append(rand())
        elif op == 224:  # DUP
            st.append(st[-1])
        elif op == 113:  # SWAP
            st[-2], st[-1] = st[-1], st[-2]
        elif op == 171:  # DROP
            st.pop()
        elif op == 22:  # EQ
            b = st.pop(); a = st.pop()
            ok &= int(a == b)
        elif op == 210:  # JMP_IF_TRUE
            n = PROG[pc]; pc += 1
            if st.pop():
                # sign extend
                if n > 127: n -= 256
                pc += n
        elif op == 62:  # PUSH_BASE
            st.append(base)
        elif op == 247:  # POP_BASE
            base = st.pop()
        else:
            raise ValueError(f"Unknown opcode {op}")
    return ok

def main(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        top = marshal.load(f)
    PAYLOAD = top.co_consts[3]
    boot_co = top.co_consts[7]
    Il = fnv1a(boot_co.co_code)
    half = PAYLOAD[len(PAYLOAD)//2:] if (Il & 1) else PAYLOAD[:len(PAYLOAD)//2]
    prng = splitmix64_full(Il)
    res = bytearray(half)
    pos = 0
    while pos < len(res):
        w = next(prng)
        for j in range(8):
            if pos+j >= len(res): break
            res[pos+j] ^= (w >> (j*8)) & 0xFF
        pos += 8
    hidden = marshal.loads(bytes(res))
    PROG = hidden.co_consts[1]
    TGT = hidden.co_consts[2]
    INIT_STATE = hidden.co_consts[3]

    # Test with zero input
    IN = [0] * 12
    ok = run_vm(IN, TGT, PROG, INIT_STATE)
    print("Ok:", ok)
    # Now we need to capture the transformed values. We can modify run_vm to print.
    # Or we can run a modified version that prints before EQ.
    print("Add prints inside run_vm to see values.")

if __name__ == '__main__':
    main(sys.argv[1])
