#!/usr/bin/env python3
"""Reference solve for Velvet Vault; Python standard library only."""

from __future__ import annotations

import base64
import hashlib
import http.cookiejar
import json
import random
import struct
import sys
import urllib.error
import urllib.request


MASK32 = 0xFFFFFFFF
STATE_WORDS = 624
FORECAST_WORDS = 47
CLAIM_WORDS = 8


def rotl32(value: int, amount: int) -> int:
    amount &= 31
    value &= MASK32
    if amount == 0:
        return value
    return ((value << amount) | (value >> (32 - amount))) & MASK32


def rotr32(value: int, amount: int) -> int:
    amount &= 31
    value &= MASK32
    if amount == 0:
        return value
    return ((value >> amount) | (value << (32 - amount))) & MASK32


def draw_mask(draw_index: int) -> int:
    linear = (0x9E3779B9 * (draw_index + 1) + 0x7F4A7C15) & MASK32
    return linear ^ rotl32(draw_index, 13) ^ 0xA5C31F27


def decode_word(draw_index: int, code: str) -> int:
    padded = code + "=" * (-len(code) % 4)
    shuffled = base64.urlsafe_b64decode(padded)
    if len(shuffled) != 4:
        raise ValueError(f"draw {draw_index} has an invalid code length")

    # Server sent raw bytes in order (r2,r0,r3,r1).
    raw = bytes((shuffled[1], shuffled[3], shuffled[0], shuffled[2]))
    mixed = struct.unpack("<I", raw)[0]
    return rotr32(mixed, 7 * draw_index + 11) ^ draw_mask(draw_index)


def collect_records(value: object, output: dict[int, int]) -> None:
    """Walk the interleaved JSON rather than depending on display order."""
    if isinstance(value, dict):
        if set(value) == {"draw", "code"}:
            draw = value["draw"]
            code = value["code"]
            if type(draw) is not int or type(code) is not str:
                raise ValueError("malformed forecast record")
            if draw in output:
                raise ValueError(f"duplicate draw index {draw}")
            output[draw] = decode_word(draw, code)
            return
        for child in value.values():
            collect_records(child, output)
    elif isinstance(value, list):
        for child in value:
            collect_records(child, output)


def undo_right_xor(value: int, shift: int) -> int:
    # Fixed-point inversion: high bits settle first.
    result = value
    for _ in range(8):
        result = value ^ (result >> shift)
    return result & MASK32


def undo_left_xor_mask(value: int, shift: int, mask: int) -> int:
    # Fixed-point inversion: low bits settle first.
    result = value
    for _ in range(8):
        result = value ^ ((result << shift) & mask)
    return result & MASK32


def untemper(value: int) -> int:
    """Invert CPython MT19937's four tempering operations."""
    value = undo_right_xor(value, 18)
    value = undo_left_xor_mask(value, 15, 0xEFC60000)
    value = undo_left_xor_mask(value, 7, 0x9D2C5680)
    value = undo_right_xor(value, 11)
    return value


def make_claim(words: list[int], first_draw: int) -> dict[str, object]:
    serial_number = (
        ((words[0] << 32) | words[3]) ^ 0xD6E8FEB86659FD93
    ) & 0xFFFFFFFFFFFFFFFF
    window = ((words[1] ^ rotr32(words[4], 9)) % 900_000) + 100_000
    nonce_parts = (
        words[2] ^ 0xC0DEC0DE,
        rotl32(words[5], first_draw),
        words[7],
    )
    nonce = base64.urlsafe_b64encode(
        struct.pack(">III", *nonce_parts)
    ).decode("ascii").rstrip("=")

    claim: dict[str, object] = {
        "role": "admin",
        "draw": first_draw,
        "serial": f"{serial_number:016x}",
        "window": window,
        "nonce": nonce,
    }
    canonical = (
        f"admin|{first_draw}|{claim['serial']}|{window}|{nonce}"
    ).encode("ascii")
    claim["proof"] = hashlib.sha256(
        b"forecast-fallout/admin/v1\x00"
        + struct.pack("<8I", *words)
        + b"\x00"
        + canonical
    ).hexdigest()
    return claim


class Client:
    def __init__(self, base_url: str) -> None:
        self.base = base_url.rstrip("/")
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(jar)
        )

    def json(self, path: str, body: object | None = None) -> dict:
        data = None
        headers = {"Accept": "application/json"}
        method = "GET"
        if body is not None:
            data = json.dumps(body, separators=(",", ":")).encode()
            headers["Content-Type"] = "application/json"
            method = "POST"
        request = urllib.request.Request(
            self.base + path, data=data, headers=headers, method=method
        )
        try:
            with self.opener.open(request, timeout=10) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise RuntimeError(f"HTTP {exc.code} from {path}: {detail}") from exc


def solve(base_url: str) -> str:
    client = Client(base_url)
    observed: dict[int, int] = {}

    # ceil(624 / 47) = 14 calls, yielding 658 visible words. The final 34 are
    # deliberate surplus that must be replayed after cloning the state.
    while len(observed) < STATE_WORDS:
        before = len(observed)
        response = client.json("/api/forecast")
        collect_records(response, observed)
        added = len(observed) - before
        if added != FORECAST_WORDS:
            raise RuntimeError(f"forecast returned {added}, not 47, records")
        print(
            f"[+] request {response['request']}: collected {len(observed)} words",
            file=sys.stderr,
        )

    indices = sorted(observed)
    if indices != list(range(indices[-1] + 1)) or indices[0] != 0:
        raise RuntimeError("expected a fresh, contiguous session beginning at draw 0")

    recovered_state = [untemper(observed[i]) for i in range(STATE_WORDS)]
    clone = random.Random()
    # CPython state is 624 untempered words followed by the current state index.
    clone.setstate((3, tuple(recovered_state + [STATE_WORDS]), None))

    # Move the clone from draw 624 to the live server cursor and verify every
    # surplus draw. This catches codec, ordering, and untemper mistakes safely.
    for draw in range(STATE_WORDS, indices[-1] + 1):
        predicted = clone.getrandbits(32)
        if predicted != observed[draw]:
            raise RuntimeError(
                f"state recovery failed at surplus draw {draw}: "
                f"{predicted:#x} != {observed[draw]:#x}"
            )

    status = client.json("/api/status")
    next_draw = indices[-1] + 1
    if status["next_draw"] != next_draw:
        raise RuntimeError("server cursor changed unexpectedly")
    print(
        f"[+] cloned MT state and aligned {next_draw - STATE_WORDS} surplus draws",
        file=sys.stderr,
    )

    future = [clone.getrandbits(32) for _ in range(CLAIM_WORDS)]
    claim = make_claim(future, next_draw)
    result = client.json("/api/claim", claim)
    flag = result.get("flag")
    if not isinstance(flag, str):
        raise RuntimeError(f"claim returned no flag: {result}")
    return flag


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:31342"
    print(solve(target))
