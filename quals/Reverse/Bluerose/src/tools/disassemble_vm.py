#!/usr/bin/env python3
"""Decode and print the Rose VM program (optional deep-reversing aid)."""

from pathlib import Path
import re
import struct

NAMES = {
    0x91: "LDC", 0xD3: "LDMOVE", 0x48: "LDBOARD", 0xB5: "LDMETA",
    0x0C: "LDINDEX", 0xE1: "LDSTATE", 0x63: "STSTATE", 0x37: "LDSIDE",
    0xAD: "LDDEBUG", 0x54: "XOR", 0xC7: "ADD", 0x82: "MUL",
    0xF0: "ROL", 0x3B: "ROR", 0xA4: "BRBIT", 0x11: "JNZ",
    0xDE: "JMP", 0x40: "HALT", 0x75: "MIX", 0xCA: "KEYSTEP", 0x24: "OUTPUT",
}


def rol8(x, n):
    return ((x << n) | (x >> (8 - n))) & 255


def ror8(x, n):
    return ((x >> n) | (x << (8 - n))) & 255


def load_blob():
    source = (Path(__file__).resolve().parents[1] / "src/bytecode.c").read_text()
    body = re.search(r"garden\[\]\s*=\s*\{(.*?)\};", source, re.S).group(1)
    return bytes(int(x, 16) for x in re.findall(r"0x([0-9a-fA-F]{2})", body))


def decode():
    key, plain = 0xC7, bytearray()
    for i, encoded in enumerate(load_blob()):
        value = ror8(encoded ^ ((i * 0x17 + 0x5A) & 255), i % 7 + 1) ^ key
        plain.append(value)
        key = rol8((key + value + i * 0x3D) & 255, 3) ^ 0xA7
    constants = [struct.unpack_from("<Q", plain, 8 + i * 8)[0] for i in range(plain[2])]
    start = 8 + 8 * plain[2]
    insns = [tuple(plain[start + i * 4:start + i * 4 + 4]) for i in range(plain[3])]
    return tuple(plain[4:7]), constants, insns


def disassemble():
    entries, constants, insns = decode()
    labels = dict(zip(entries, ("init", "step", "final")))
    lines = ["constants: " + " ".join(f"{x:016x}" for x in constants)]
    for pc, (op, a, b, imm) in enumerate(insns):
        if pc in labels: lines.append(labels[pc] + ":")
        name = NAMES.get(op, f"OP_{op:02x}")
        if name == "LDC": args = f"r{a}, const[{imm}]"
        elif name.startswith("LD") and name not in ("LDSTATE",): args = f"r{a}"
        elif name in ("LDSTATE", "STSTATE"): args = f"r{a}, s{imm & 3}"
        elif name == "MIX": args = f"r{a}, r{b}, {imm}"
        elif name == "KEYSTEP": args = f"r{a}, r{b}, {imm}"
        elif name == "JNZ": args = f"r{a}, {struct.unpack('b', bytes([imm]))[0]:+d}"
        else: args = ""
        lines.append(f"{pc:04x}  {name:<9} {args}".rstrip())
    return "\n".join(lines)


if __name__ == "__main__":
    print(disassemble())
