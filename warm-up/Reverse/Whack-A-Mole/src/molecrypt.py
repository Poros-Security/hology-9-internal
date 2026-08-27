#!/usr/bin/env python3
"""
molecrypt -- Python mirror of molecrypt.c.

Every routine here must behave byte-identically to its C counterpart.
`make check-parity` feeds both the same inputs and diffs the output.

This module is the single source of truth for the challenge parameters, and is
shared by gen.py (build time) and, by re-implementation, by solver/solve.py
(which must stand alone from dist/ artifacts only).
"""

MASK64 = (1 << 64) - 1

# --- parameters (spec section 4) --------------------------------------------
GRID = 10
PATH_LEN = 12
HOLE_SIZE = 256
SEED = 0x5EEDCAFEB00B1E5F
SALT = b"M0LEH1LL"
MAGIC = b"M0LE"

NUM_HOLES = GRID * GRID

# --- plaintext layout (spec section 5) --------------------------------------
OFF_MAGIC = 0
OFF_ROUND = 4
OFF_FRAGLEN = 5
OFF_FRAG = 6


def mole_mix64(x: int) -> int:
    """splitmix64-style finalizer."""
    x &= MASK64
    x ^= x >> 30
    x = (x * 0xBF58476D1CE4E5B9) & MASK64
    x ^= x >> 27
    x = (x * 0x94D049BB133111EB) & MASK64
    x ^= x >> 31
    return x


def mole_keystream(state: int, pick: int, n: int = HOLE_SIZE) -> bytes:
    """n keystream bytes derived from (state, pick, SALT)."""
    x = (state ^ ((0x9E3779B97F4A7C15 * (pick + 1)) & MASK64)) & MASK64
    for i in range(8):
        x ^= SALT[i] << (i * 8)
    x &= MASK64

    out = bytearray(n)
    i = 0
    while i < n:
        x = mole_mix64(x)
        take = min(8, n - i)
        out[i:i + take] = x.to_bytes(8, "little")[:take]
        i += 8
    return bytes(out)


def mole_crypt(data: bytes, state: int, pick: int) -> bytes:
    """XOR with the keystream. Encrypt and decrypt are the same operation."""
    ks = mole_keystream(state, pick, len(data))
    return bytes(a ^ b for a, b in zip(data, ks))


def mole_advance(state: int, pick: int, plain: bytes) -> int:
    """FNV-1a over pick + whatever the dig produced, correct or garbage."""
    h = (state ^ 0xCBF29CE484222325) & MASK64
    h ^= pick
    h = (h * 0x100000001B3) & MASK64
    for b in plain:
        h ^= b
        h = (h * 0x100000001B3) & MASK64
    return h


# --- plaintext helpers ------------------------------------------------------

def split_flag(flag: bytes, parts: int = PATH_LEN) -> list:
    """
    Split the flag into `parts` fragments as evenly as possible.

    Derived entirely from len(flag): the first (len % parts) fragments get one
    extra byte. Each hole records its own fragment length, so nothing needs to
    be padded to a common size and the flag length can change freely.
    """
    if len(flag) < parts:
        raise ValueError("flag must be at least PATH_LEN bytes long")
    base, extra = divmod(len(flag), parts)
    out, off = [], 0
    for i in range(parts):
        n = base + (1 if i < extra else 0)
        out.append(flag[off:off + n])
        off += n
    assert off == len(flag)
    assert b"".join(out) == flag
    return out


def build_plaintext(rnd: int, frag: bytes, pad: bytes) -> bytes:
    """MAGIC | round | frag_len | frag | random pad, exactly HOLE_SIZE bytes."""
    if len(frag) > 0xFF or OFF_FRAG + len(frag) > HOLE_SIZE:
        raise ValueError("fragment too large for a hole")
    body = MAGIC + bytes([rnd & 0xFF, len(frag)]) + frag
    need = HOLE_SIZE - len(body)
    if len(pad) < need:
        raise ValueError("not enough pad bytes")
    return body + pad[:need]


def carve_fragment(plain: bytes) -> bytes:
    """
    Pull the fragment out of a decrypted hole the way `mallet` does: trust the
    length byte, clamp to the buffer. No magic check -- the binary does not know
    what a correct hole looks like.
    """
    n = plain[OFF_FRAGLEN]
    if OFF_FRAG + n > HOLE_SIZE:
        n = HOLE_SIZE - OFF_FRAG
    return plain[OFF_FRAG:OFF_FRAG + n]


def has_magic(plain: bytes) -> bool:
    return plain[OFF_MAGIC:OFF_MAGIC + len(MAGIC)] == MAGIC


# --- parity harness ---------------------------------------------------------

def _parity_vectors():
    """Deterministic (state, pick) pairs exercising the whole surface."""
    st = SEED
    for pick in (0, 1, 7, 42, 99, 255):
        yield st, pick
        st = mole_advance(st, pick, mole_keystream(st, pick, HOLE_SIZE))
    for i in range(8):
        yield (0xFFFFFFFFFFFFFFFF >> (i * 7)) & MASK64, (i * 13) % 100
    yield 0, 0
    yield MASK64, 99


def _parity_dump():
    lines = []
    for state, pick in _parity_vectors():
        ks = mole_keystream(state, pick, HOLE_SIZE)
        lines.append("state=%016x pick=%3d mix=%016x adv=%016x" % (
            state, pick, mole_mix64(state), mole_advance(state, pick, ks)))
        lines.append("  ks=%s" % ks.hex())
    for n in (1, 7, 8, 9, 15, 16, 255, 256):
        lines.append("short n=%3d ks=%s" % (n, mole_keystream(SEED, n % 100, n).hex()))
    return "\n".join(lines)


if __name__ == "__main__":
    print(_parity_dump())
