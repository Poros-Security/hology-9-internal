#!/usr/bin/env python3
"""
Build-time generator for `Whack a Mole`.

Emits the 100 hole files and records the layout. Also contains a pure-Python
reference player (`--play`) that walks the correct path and prints the flag,
so the whole mechanic is provable without touching C.

    python3 gen.py            # generate into ../src/build/handout/holes
    python3 gen.py --play     # regenerate nothing, replay the recorded path
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from molecrypt import (  # noqa: E402
    HOLE_SIZE, MAGIC, NUM_HOLES, PATH_LEN, SEED,
    build_plaintext, carve_fragment, has_magic, mole_advance, mole_crypt,
    split_flag,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(HERE, "build")
HANDOUT = os.path.join(BUILD, "handout")
HOLES_DIR = os.path.join(HANDOUT, "holes")
PATH_JSON = os.path.join(BUILD, "path.json")
FLAG_TXT = os.path.join(HERE, "flag.txt")

MAX_REROLLS = 64


def read_flag():
    with open(FLAG_TXT, "rb") as f:
        return f.read().strip()


def build_layout(flag, rng):
    """
    One attempt at a layout. Returns (holes, path, fragments, states) or None
    if a second hole collides with the magic under some reachable state.
    """
    frags = split_flag(flag, PATH_LEN)
    path = rng.sample(range(NUM_HOLES), PATH_LEN)
    assert len(set(path)) == PATH_LEN, "path must contain distinct holes"

    holes = [bytearray(os.urandom(HOLE_SIZE)) for _ in range(NUM_HOLES)]

    state = SEED
    states = []
    for r, pick in enumerate(path):
        states.append(state)
        plain = build_plaintext(r, frags[r], os.urandom(HOLE_SIZE))
        holes[pick] = bytearray(mole_crypt(plain, state, pick))
        state = mole_advance(state, pick, plain)

    # Invariant: at every round exactly one hole carries the magic. A second
    # match is an alternate solution -- reject the whole layout and re-roll.
    for r, s in enumerate(states):
        matches = [p for p in range(NUM_HOLES)
                   if has_magic(mole_crypt(bytes(holes[p]), s, p))]
        if matches != [path[r]]:
            return None

    return holes, path, frags, states


def generate():
    flag = read_flag()
    rng = random.SystemRandom()

    for attempt in range(MAX_REROLLS):
        layout = build_layout(flag, rng)
        if layout is not None:
            break
        print("[!] magic collision, re-rolling (attempt %d)" % (attempt + 1))
    else:
        raise SystemExit("could not find a collision-free layout")

    holes, path, frags, states = layout

    os.makedirs(HOLES_DIR, exist_ok=True)
    for i, h in enumerate(holes):
        assert len(h) == HOLE_SIZE
        with open(os.path.join(HOLES_DIR, "hole_%02d.bin" % i), "wb") as f:
            f.write(bytes(h))

    with open(PATH_JSON, "w") as f:
        json.dump({
            "flag": flag.decode(),
            "path": path,
            "fragments": [fr.decode() for fr in frags],
            "states": ["%016x" % s for s in states],
        }, f, indent=2)

    print("[+] %d holes written to %s" % (NUM_HOLES, HOLES_DIR))
    print("[+] path: %s" % path)
    print("[+] layout recorded in %s (author-only, never shipped)" % PATH_JSON)

    haul = play(path, quiet=True)
    if haul != flag:
        raise SystemExit("reference player did not recover the flag: %r" % haul)
    print("[+] reference player recovered: %s" % haul.decode())


def load_holes(holes_dir=HOLES_DIR):
    out = []
    for i in range(NUM_HOLES):
        with open(os.path.join(holes_dir, "hole_%02d.bin" % i), "rb") as f:
            out.append(f.read())
    return out


def play(path, quiet=False):
    """
    Pure-Python reference player: exactly what `mallet` does, no magic checks,
    no verdicts -- dig, decrypt, carve at the fragment offset, advance.
    """
    holes = load_holes()
    state = SEED
    haul = bytearray()
    for r, pick in enumerate(path):
        plain = mole_crypt(holes[pick], state, pick)
        frag = carve_fragment(plain)
        haul += frag
        if not quiet:
            print("round %2d/%d  hole %02d  -> %r%s" % (
                r + 1, PATH_LEN, pick, bytes(frag),
                "" if not has_magic(plain) else "  [magic]"))
        state = mole_advance(state, pick, plain)
    return bytes(haul)


def solve_offline():
    """
    The intended offline solve, done here as a build-time sanity check: at each
    round try all 100 holes and keep the one that decrypts to the magic.
    """
    holes = load_holes()
    state = SEED
    path, haul = [], bytearray()
    for _ in range(PATH_LEN):
        hits = []
        for pick in range(NUM_HOLES):
            plain = mole_crypt(holes[pick], state, pick)
            if has_magic(plain):
                hits.append((pick, plain))
        if len(hits) != 1:
            raise SystemExit("expected exactly 1 magic hole, got %d" % len(hits))
        pick, plain = hits[0]
        path.append(pick)
        haul += carve_fragment(plain)
        state = mole_advance(state, pick, plain)
    return path, bytes(haul)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--play", action="store_true",
                    help="replay the recorded correct path")
    ap.add_argument("--solve", action="store_true",
                    help="run the intended offline solve against build/")
    args = ap.parse_args()

    if args.play:
        with open(PATH_JSON) as f:
            meta = json.load(f)
        haul = play(meta["path"])
        print("Your haul: %s" % haul.decode(errors="replace"))
        return
    if args.solve:
        path, haul = solve_offline()
        print("path: %s" % path)
        print("flag: %s" % haul.decode(errors="replace"))
        return

    generate()


if __name__ == "__main__":
    main()
