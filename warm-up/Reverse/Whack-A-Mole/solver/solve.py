#!/usr/bin/env python3
"""
Reference solver for `Whack a Mole` -- works from the handout ONLY.

It imports nothing from src/ and never reads the generator's layout. Everything
below was recovered by reversing `mallet`:

  * SEED and SALT are the only two secrets baked into the binary. SALT is
    stored XORed with 0x5A in .data and unmasked byte-by-byte at the top of the
    keystream routine.
  * The keystream is splitmix64's finalizer run as a counter-free generator,
    seeded from state ^ (GOLDEN * (pick+1)) ^ SALT, emitting 8 little-endian
    bytes per iteration for HOLE_SIZE bytes.
  * The state advances by FNV-1a over (pick || decrypted plaintext) after
    *every* dig, so a wrong pick silently poisons every later round.

That last property is the whole challenge: there is no per-file key, so you
cannot decrypt hole N without knowing the exact sequence of digs that got you
there. But the search is only 100 wide per round, and correct plaintexts start
with the magic "M0LE" -- so a greedy round-by-round sweep of 12 x 100 = 1200
trial decryptions walks straight down the path.

    python3 solve.py [path/to/extracted/handout]
"""
import os
import sys

MASK64 = (1 << 64) - 1

SEED = 0x5EEDCAFEB00B1E5F
SALT = b"M0LEH1LL"
MAGIC = b"M0LE"

GRID = 10
NUM_HOLES = GRID * GRID
PATH_LEN = 12
HOLE_SIZE = 256

OFF_FRAGLEN = 5
OFF_FRAG = 6


def mix64(x):
    x &= MASK64
    x ^= x >> 30
    x = (x * 0xBF58476D1CE4E5B9) & MASK64
    x ^= x >> 27
    x = (x * 0x94D049BB133111EB) & MASK64
    x ^= x >> 31
    return x


def keystream(state, pick, n=HOLE_SIZE):
    x = (state ^ ((0x9E3779B97F4A7C15 * (pick + 1)) & MASK64)) & MASK64
    for i in range(8):
        x ^= SALT[i] << (i * 8)
    x &= MASK64
    out = bytearray()
    while len(out) < n:
        x = mix64(x)
        out += x.to_bytes(8, "little")
    return bytes(out[:n])


def decrypt(hole, state, pick):
    return bytes(a ^ b for a, b in zip(hole, keystream(state, pick, len(hole))))


def advance(state, pick, plain):
    h = (state ^ 0xCBF29CE484222325) & MASK64
    h ^= pick
    h = (h * 0x100000001B3) & MASK64
    for b in plain:
        h ^= b
        h = (h * 0x100000001B3) & MASK64
    return h


def load(root):
    holes = []
    for i in range(NUM_HOLES):
        with open(os.path.join(root, "holes", "hole_%02d.bin" % i), "rb") as f:
            data = f.read()
        assert len(data) == HOLE_SIZE, "hole_%02d.bin is %d bytes" % (i, len(data))
        holes.append(data)
    return holes


def solve(root):
    holes = load(root)
    state = SEED
    path, flag = [], bytearray()

    for rnd in range(PATH_LEN):
        hits = [(p, d) for p in range(NUM_HOLES)
                for d in (decrypt(holes[p], state, p),) if d[:4] == MAGIC]
        if len(hits) != 1:
            raise SystemExit("round %d: expected 1 mole, found %d" % (rnd, len(hits)))

        pick, plain = hits[0]
        n = plain[OFF_FRAGLEN]
        frag = plain[OFF_FRAG:OFF_FRAG + n]
        path.append(pick)
        flag += frag

        print("round %2d/%d  ->  %s%d (hole %02d)  %r"
              % (rnd + 1, PATH_LEN, chr(ord('A') + pick % GRID), pick // GRID,
                 pick, bytes(frag)))
        state = advance(state, pick, plain)

    return path, bytes(flag)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    path, flag = solve(root)
    print()
    print("dig order: %s" % " ".join(
        "%s%d" % (chr(ord('A') + p % GRID), p // GRID) for p in path))
    print("flag: %s" % flag.decode())


if __name__ == "__main__":
    main()
