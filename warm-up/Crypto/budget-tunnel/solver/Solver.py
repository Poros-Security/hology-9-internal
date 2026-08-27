#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
import math
import socket
import sys
from pathlib import Path

from Chall import determinant, stream_xor, transition_rows


def load_instance() -> dict:
    if len(sys.argv) == 3:
        with socket.create_connection((sys.argv[1], int(sys.argv[2])), timeout=30) as sock:
            chunks = []
            while chunk := sock.recv(65536):
                chunks.append(chunk)
        return json.loads(b"".join(chunks))
    if len(sys.argv) == 2:
        return json.loads(Path(sys.argv[1]).read_text())
    raise SystemExit("usage: python3 Solver.py HOST PORT | instance.json")


def null_vector_mod(rows: list[list[int]], modulus: int) -> list[int]:
    work = [[value % modulus for value in row] for row in rows]
    pivot_columns = []
    pivot_row = 0
    for col in range(4):
        selected = next((r for r in range(pivot_row, len(work)) if work[r][col]), None)
        if selected is None:
            continue
        work[pivot_row], work[selected] = work[selected], work[pivot_row]
        scale = pow(work[pivot_row][col], -1, modulus)
        work[pivot_row] = [(value * scale) % modulus for value in work[pivot_row]]
        for row in range(len(work)):
            if row != pivot_row and work[row][col]:
                factor = work[row][col]
                work[row] = [(a - factor * b) % modulus for a, b in zip(work[row], work[pivot_row])]
        pivot_columns.append(col)
        pivot_row += 1

    free_columns = [col for col in range(4) if col not in pivot_columns]
    if len(free_columns) != 1:
        raise RuntimeError("projective system does not have a unique one-dimensional nullspace")
    vector = [0] * 4
    vector[free_columns[0]] = 1
    for row, col in reversed(list(enumerate(pivot_columns))):
        vector[col] = -sum(work[row][j] * vector[j] for j in free_columns) % modulus
    return vector


def recover(instance: dict) -> tuple[int, list[int], int]:
    states = [int(value) for value in instance["states"]]
    rows = transition_rows(states)
    modulus = 0
    for chosen in itertools.combinations(rows[:8], 4):
        modulus = math.gcd(modulus, abs(determinant([list(row) for row in chosen])))
    if modulus.bit_length() != int(instance["modulus_bits"]):
        raise RuntimeError("unexpected determinant GCD; instance violates its published bit length")

    a, b, c, d = null_vector_mod(rows, modulus)
    current = states[0]
    for _ in range(int(instance["drop"])):
        current = (b - d * current) * pow(c * current - a, -1, modulus) % modulus
    return modulus, [a, b, c, d], current


def main() -> None:
    instance = load_instance()
    modulus, _, seed = recover(instance)
    plaintext = stream_xor(bytes.fromhex(instance["ciphertext_hex"]), modulus, seed)
    print(plaintext.decode())


if __name__ == "__main__":
    main()
