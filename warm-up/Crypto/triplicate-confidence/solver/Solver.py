#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import runpy
import sys
from pathlib import Path


def int_to_minimal_bytes(value: int) -> bytes:
    return value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")


def challenge_hash(R: int, msg: bytes, q: int) -> int:
    data = b"parabola-permit/e/v1\x00" + int_to_minimal_bytes(R) + b"\x00" + msg
    return int.from_bytes(hashlib.sha256(data).digest(), "big") % q


def solve_linear_mod(matrix: list[list[int]], target: list[int], q: int) -> list[int]:
    n = len(matrix)
    work = [
        [value % q for value in row] + [target[row_index] % q]
        for row_index, row in enumerate(matrix)
    ]
    for col in range(n):
        pivot = next(row for row in range(col, n) if work[row][col] % q)
        work[col], work[pivot] = work[pivot], work[col]
        inv = pow(work[col][col], -1, q)
        work[col] = [(value * inv) % q for value in work[col]]
        for row in range(n):
            if row == col:
                continue
            factor = work[row][col] % q
            if factor:
                work[row] = [
                    (a - factor * b) % q for a, b in zip(work[row], work[col])
                ]
    return [work[row][-1] for row in range(n)]


def recover_private_key(instance: dict) -> int:
    q = int(instance["q"])
    rows = []
    target = []
    for sig in instance["signatures"][:4]:
        i = int(sig["i"])
        msg = bytes.fromhex(sig["msg_hex"])
        e = challenge_hash(int(sig["R"]), msg, q)
        rows.append([(i * i) % q, i % q, 1, e])
        target.append(int(sig["s"]))

    alpha, beta, gamma, x = solve_linear_mod(rows, target, q)

    for sig in instance["signatures"]:
        i = int(sig["i"])
        msg = bytes.fromhex(sig["msg_hex"])
        e = challenge_hash(int(sig["R"]), msg, q)
        k = (alpha * i * i + beta * i + gamma) % q
        if (k + e * x) % q != int(sig["s"]):
            raise RuntimeError("signature equations did not verify")

    if pow(int(instance["g"]), x, int(instance["p"])) != int(instance["y"]):
        raise RuntimeError("recovered key does not match y")
    return x


def decrypt(instance: dict, x: int) -> bytes:
    q = int(instance["q"])
    width = (q.bit_length() + 7) // 8
    stream = hashlib.shake_256(
        b"parabola-permit-v1|" + x.to_bytes(width, "big")
    ).digest(len(bytes.fromhex(instance["ciphertext_hex"])))
    return bytes(a ^ b for a, b in zip(bytes.fromhex(instance["ciphertext_hex"]), stream))


def load_instance() -> dict:
    if len(sys.argv) == 2:
        path = Path(sys.argv[1])
    else:
        path = Path(__file__).resolve().parents[1] / "chall" / "chall.py"
    if path.suffix == ".py":
        return runpy.run_path(str(path))["INSTANCE"]
    return json.loads(path.read_text())


def main() -> None:
    instance = load_instance()
    x = recover_private_key(instance)
    print(decrypt(instance, x).decode())


if __name__ == "__main__":
    main()
