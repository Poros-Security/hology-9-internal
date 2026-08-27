#!/usr/bin/env python3
"""ILusion - end-to-end solver.

Inputs: dist/ILusion.exe and dist/core.bin. Nothing else, nothing hardcoded.

  1. The decompiler shows a tidy XOR-0x42 `LegacyCheck`. It is a decoy: it is
     only reachable under ILUSION_LEGACY=1 and it encodes a different flag.
     The real check lives in a second assembly that never touches disk.

  2. ILusion.Program.Gate AES-decrypts core.bin and Assembly.Load()s the
     result. The key is SHA256 over Gate's own IL:

         key = SHA256( GetILAsByteArray(Gate) || "ILusion/v1" || Poison() )

     Poison() is 0x5A with a debugger attached, 0x00 otherwise - and Poison
     is a separate method whose IL is *not* hashed, so it can be stubbed to
     `return 0` and the key still derives. Offline we simply use 0x00.

     GetILAsByteArray returns the body only, so the method header (tiny =
     1 byte, fat = 12) must be stripped. That is the whole trick of step 1.

  3. Decrypt core.bin -> Core.dll, in memory.

  4. Core.Machine.Verify is a stack VM. Its SBOX / K / TARGET / CODE tables
     are static array initialisers, so they sit in .sdata behind FieldRVA
     entries; Roslyn names each blob's type `__StaticArrayInitTypeSize=<n>`,
     which gives the length straight from metadata. The initial VM state is
     recovered from Verify's own IL prologue.

  5. Re-implement the VM, and recover the input a byte at a time. The check
     never early-exits, so this is not an oracle on the *binary* - it is an
     oracle on our own local copy of the bytecode, which is the point.

  usage: python3 solve.py [dist-dir]
  deps : pip install -r requirements.txt
"""
import hashlib
import os
import struct
import sys

import dnfile
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

SALT = b"ILusion/v1"
POISON_NO_DEBUGGER = b"\x00"

# opcodes, read straight off the switch in Machine.Verify
PUSH_IMM, PUSH_IN, PUSH_ST = 0x11, 0x12, 0x13
XOR, ADD, ROL, SBOX_OP = 0x21, 0x22, 0x23, 0x24
STORE_ST, CMP, LEN, HALT = 0x31, 0x32, 0x41, 0xFF


# ===========================================================================
# CLI metadata
# ===========================================================================

def _s(item):
    return item.value if hasattr(item, "value") else item


def _find_method(pe, name, type_name):
    for td in pe.net.mdtables.TypeDef.rows:
        ns, tn = _s(td.TypeNamespace), _s(td.TypeName)
        full = "{}.{}".format(ns, tn) if ns else tn
        if full != type_name:
            continue
        for ref in td.MethodList:
            if ref.row is not None and _s(ref.row.Name) == name:
                return ref.row
    raise LookupError("{}.{} not found".format(type_name, name))


def method_il(pe, name, type_name):
    """Exactly what MethodBody.GetILAsByteArray() returns: body, no header."""
    md = _find_method(pe, name, type_name)
    off = pe.get_offset_from_rva(md.Rva)
    data = pe.__data__
    first = data[off]
    if first & 0x03 == 0x02:                 # CorILMethod_TinyFormat
        return bytes(data[off + 1:off + 1 + (first >> 2)])
    if first & 0x03 == 0x03:                 # CorILMethod_FatFormat
        size = struct.unpack_from("<I", data, off + 4)[0]
        return bytes(data[off + 12:off + 12 + size])
    raise ValueError("bad method header 0x{:02X}".format(first))


def _decompress_uint(buf, pos):
    b = buf[pos]
    if b & 0x80 == 0:
        return b, pos + 1
    if b & 0x40 == 0:
        return ((b & 0x3F) << 8) | buf[pos + 1], pos + 2
    return (((b & 0x1F) << 24) | (buf[pos + 1] << 16)
            | (buf[pos + 2] << 8) | buf[pos + 3]), pos + 4


def rva_arrays(pe):
    """All .sdata-backed static array blobs, sized from metadata."""
    marker = "__StaticArrayInitTypeSize="
    sizes = {}
    for i, td in enumerate(pe.net.mdtables.TypeDef.rows):
        tn = _s(td.TypeName) or ""
        if tn.startswith(marker):
            sizes[i + 1] = int(tn[len(marker):])

    out = []
    for row in pe.net.mdtables.FieldRva.rows:
        field = row.Field.row
        if field is None:
            continue
        sig = bytes(_s(field.Signature))
        if len(sig) < 3 or sig[0] != 0x06:
            continue
        pos = 1
        while sig[pos] in (0x1F, 0x20):
            pos += 1
            _, pos = _decompress_uint(sig, pos)
        if sig[pos] not in (0x11, 0x12):      # VALUETYPE / CLASS
            continue
        coded, _ = _decompress_uint(sig, pos + 1)
        if coded & 0x03:
            continue
        size = sizes.get(coded >> 2)
        if size:
            out.append(bytes(pe.get_data(row.Rva, size)))
    return out


def initial_state(il):
    """Recover `byte state = <imm>` from Verify's prologue.

    The prologue is a run of `ldc.i4* <const>; stloc*` pairs, ending at the
    unconditional `br` into the dispatch loop. Every local seeded there holds
    0 or 1 (sp, pc, fail, running) except the VM state.
    """
    stloc_short = {0x0A, 0x0B, 0x0C, 0x0D}
    pos = 0
    seen = []
    while pos < len(il):
        op = il[pos]
        if 0x16 <= op <= 0x1E:               # ldc.i4.0 .. ldc.i4.8
            value, nxt = op - 0x16, pos + 1
        elif op == 0x1F:                     # ldc.i4.s
            value, nxt = il[pos + 1], pos + 2
        elif op == 0x20:                     # ldc.i4
            value, nxt = struct.unpack_from("<i", il, pos + 1)[0], pos + 5
        elif op in (0x2B, 0x38):             # br.s / br - the loop entry
            break
        else:
            pos += 1
            continue

        if nxt < len(il) and (il[nxt] in stloc_short or il[nxt] == 0x13):
            seen.append(value)
        pos = nxt

    candidates = [v for v in seen if v > 1]
    if len(candidates) != 1:
        raise ValueError("cannot pin down the initial state: {}".format(seen))
    return candidates[0] & 0xFF


# ===========================================================================
# the VM
# ===========================================================================

def run(code, sbox, target, data, stop_after=None):
    """Interpret CODE. Returns the per-index comparison results.

    `stop_after` halts once index `stop_after` has been compared, which keeps
    the byte search cheap.
    """
    stack, sp, pc = [0] * 64, 0, 0
    state = data["state0"]
    results = {}
    while pc < len(code):
        op = code[pc]
        pc += 1
        if op == PUSH_IMM:
            stack[sp] = code[pc]; sp += 1; pc += 1
        elif op == PUSH_IN:
            idx = code[pc]; pc += 1
            stack[sp] = data["input"][idx] & 0xFF; sp += 1
        elif op == PUSH_ST:
            stack[sp] = state; sp += 1
        elif op == XOR:
            sp -= 1; b = stack[sp]; sp -= 1; a = stack[sp]
            stack[sp] = a ^ b; sp += 1
        elif op == ADD:
            sp -= 1; b = stack[sp]; sp -= 1; a = stack[sp]
            stack[sp] = (a + b) & 0xFF; sp += 1
        elif op == ROL:
            n = code[pc] & 7; pc += 1
            sp -= 1; b = stack[sp]
            stack[sp] = ((b << n) | (b >> (8 - n))) & 0xFF if n else b
            sp += 1
        elif op == SBOX_OP:
            sp -= 1; stack[sp] = sbox[stack[sp]]; sp += 1
        elif op == STORE_ST:
            sp -= 1; state = stack[sp]
        elif op == CMP:
            sp -= 1; b = stack[sp]
            idx = code[pc]; pc += 1
            results[idx] = (b == target[idx])
            if stop_after is not None and idx == stop_after:
                return results
        elif op == LEN:
            want = code[pc]; pc += 1
            if len(data["input"]) != want:
                results["len"] = False
                return results
        elif op == HALT:
            break
        else:
            raise ValueError("unknown opcode 0x{:02X} at {}".format(op, pc - 1))
    return results


def program_length(code):
    if code[0] != LEN:
        raise ValueError("program does not start with LEN")
    return code[1]


def recover(code, sbox, target, state0):
    """Solve the input one index at a time using our own copy of the VM."""
    n = program_length(code)
    flag = bytearray(n)
    for i in range(n):
        for candidate in range(32, 127):     # printable first, it always is
            flag[i] = candidate
            res = run(code, sbox, target,
                      {"input": flag, "state0": state0}, stop_after=i)
            if res.get(i):
                break
        else:
            for candidate in range(256):
                flag[i] = candidate
                res = run(code, sbox, target,
                          {"input": flag, "state0": state0}, stop_after=i)
                if res.get(i):
                    break
            else:
                raise ValueError("no byte satisfies index {}".format(i))
    return bytes(flag)


# ===========================================================================

def classify(blobs, code_len_hint=None):
    """Name the four .sdata blobs by shape rather than by order."""
    sbox = next((b for b in blobs
                 if len(b) == 256 and sorted(b) == list(range(256))), None)
    code = next((b for b in blobs
                 if b and b[0] == LEN and b[-1] == HALT and len(b) > 16), None)
    if sbox is None or code is None:
        raise LookupError("could not identify SBOX / CODE among "
                          "{}".format([len(b) for b in blobs]))
    n = program_length(code)
    target = next((b for b in blobs if len(b) == n and b is not code), None)
    if target is None:
        raise LookupError("no TARGET blob of length {}".format(n))
    return sbox, code, target


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    dist = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(
        os.path.join(here, os.pardir, "dist"))
    exe_path = os.path.join(dist, "ILusion.exe")
    bin_path = os.path.join(dist, "core.bin")

    # --- 1. key from the loader's own IL ---------------------------------
    pe = dnfile.dnPE(exe_path)
    il = method_il(pe, "Gate", "ILusion.Program")
    key = hashlib.sha256(il + SALT + POISON_NO_DEBUGGER).digest()
    print("[1] Gate IL  : {} bytes".format(len(il)))
    print("[1] AES key  : {}".format(key.hex()))

    # --- 2. decrypt stage 2 ----------------------------------------------
    with open(bin_path, "rb") as fh:
        blob = fh.read()
    dll = unpad(AES.new(key, AES.MODE_CBC, blob[:16]).decrypt(blob[16:]),
                AES.block_size)
    if dll[:2] != b"MZ":
        raise ValueError("decryption produced garbage - wrong key")
    print("[2] core.bin -> Core.dll, {} bytes".format(len(dll)))

    # --- 3. tables --------------------------------------------------------
    core = dnfile.dnPE(data=dll)
    sbox, code, target = classify(rva_arrays(core))
    state0 = initial_state(method_il(core, "Verify", "Core.Machine"))
    print("[3] SBOX {}  CODE {}  TARGET {}  state0 0x{:02X}".format(
        len(sbox), len(code), len(target), state0))

    # --- 4. invert --------------------------------------------------------
    flag = recover(code, sbox, target, state0)

    check = run(code, sbox, target, {"input": flag, "state0": state0})
    assert all(check.values()) and len(check) == len(flag), "VM rejects the answer"
    print("[4] VM accepts, all {} comparisons pass".format(len(check)))

    print(flag.decode())


if __name__ == "__main__":
    main()
