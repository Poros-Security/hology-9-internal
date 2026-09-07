from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import socketserver

from Crypto.Util.number import getPrime, getRandomRange, inverse

FLAG = os.environ.get("FLAG", "HOLOGY9{f4k3_fl4g").encode()
P_BITS = int(os.environ.get("P_BITS", "113"))
DROP = int(os.environ.get("DROP", "10"))
SAMPLES = int(os.environ.get("SAMPLES", "14"))
PORT = int(os.environ.get("PORT", "31341"))


def determinant(matrix: list[list[int]]) -> int:
    work = [row[:] for row in matrix]
    n = len(work)
    sign, previous = 1, 1
    for col in range(n - 1):
        pivot_row = next((r for r in range(col, n) if work[r][col]), None)
        if pivot_row is None:
            return 0
        if pivot_row != col:
            work[col], work[pivot_row] = work[pivot_row], work[col]
            sign *= -1
        pivot = work[col][col]
        for row in range(col + 1, n):
            for j in range(col + 1, n):
                work[row][j] = (work[row][j] * pivot - work[row][col] * work[col][j]) // previous
            work[row][col] = 0
        previous = pivot
    return sign * work[-1][-1]


def transition_rows(states: list[int]) -> list[list[int]]:
    return [[x, 1, -x * y, -y] for x, y in zip(states, states[1:])]


def rank_mod(rows: list[list[int]], modulus: int) -> int:
    work = [[value % modulus for value in row] for row in rows]
    rank = 0
    for col in range(len(work[0])):
        pivot = next((r for r in range(rank, len(work)) if work[r][col]), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        scale = pow(work[rank][col], -1, modulus)
        work[rank] = [(value * scale) % modulus for value in work[rank]]
        for row in range(len(work)):
            if row != rank and work[row][col]:
                factor = work[row][col]
                work[row] = [(a - factor * b) % modulus for a, b in zip(work[row], work[rank])]
        rank += 1
    return rank


def apply_mobius(x: int, coefficients: tuple[int, int, int, int], modulus: int) -> int:
    a, b, c, d = coefficients
    return ((a * x + b) * inverse(c * x + d, modulus)) % modulus


def shared_projective_divisor(states: list[int]) -> int:
    rows = transition_rows(states)
    common = 0
    for chosen in itertools.combinations(rows[:8], 4):
        common = math.gcd(common, abs(determinant([list(row) for row in chosen])))
    return common


def stream_xor(msg: bytes, modulus: int, seed: int) -> bytes:
    width = (modulus.bit_length() + 7) // 8
    material = modulus.to_bytes(width, "big") + seed.to_bytes(width, "big")
    stream = hashlib.shake_256(b"slipstream-v4|" + material).digest(len(msg))
    return bytes(a ^ b for a, b in zip(msg, stream))


def make_instance() -> dict:
    while True:
        modulus = getPrime(P_BITS)
        coefficients = tuple(getRandomRange(0, modulus) for _ in range(4))
        a, b, c, d = coefficients
        if (a * d - b * c) % modulus == 0:
            continue
        seed = getRandomRange(0, modulus)

        try:
            sequence = [seed]
            while len(sequence) < DROP + SAMPLES:
                sequence.append(apply_mobius(sequence[-1], coefficients, modulus))
        except ValueError:
            continue

        states = sequence[DROP:DROP + SAMPLES]
        rows = transition_rows(states)
        if rank_mod(rows, modulus) != 3:
            continue
        if shared_projective_divisor(states) != modulus:
            continue
        break

    return {
        "drop": DROP,
        "modulus_bits": P_BITS,
        "states": states,
        "ciphertext_hex": stream_xor(FLAG, modulus, seed).hex(),
    }


class Handler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        self.wfile.write(json.dumps(make_instance(), indent=2).encode() + b"\n")
        self.wfile.flush()


if __name__ == "__main__":
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), Handler) as server:
        server.serve_forever()
