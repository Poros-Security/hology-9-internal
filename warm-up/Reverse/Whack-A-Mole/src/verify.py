#!/usr/bin/env python3
"""
Ship gate for `Whack a Mole` -- every invariant from spec section 8.

Runs against a *fresh extraction of dist/handout.tar.gz*, not the build tree,
so it validates exactly what a player downloads. Author-side facts (the path)
come from src/build/path.json, which is never shipped.

    python3 verify.py        # exits non-zero if any invariant fails
"""
import hashlib
import json
import math
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
import tarfile
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from molecrypt import (  # noqa: E402
    HOLE_SIZE, MAGIC, NUM_HOLES, PATH_LEN, SEED,
    carve_fragment, has_magic, mole_advance, mole_crypt,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TARBALL = os.path.join(ROOT, "dist", "handout.tar.gz")
PATH_JSON = os.path.join(HERE, "build", "path.json")
SOLVER = os.path.join(ROOT, "solver", "solve.py")
FLAG_TXT = os.path.join(HERE, "flag.txt")

WRONG_PATH_TRIALS = 1000

# A 256-byte sample drawn from 256 symbols cannot reach 8 bits/byte -- the
# empirical ceiling is ~7.28 (see README, "entropy invariant"). The real test
# is that on-path and off-path holes are drawn from the same distribution.
ENTROPY_FLOOR = 6.80

_fails = []


def check(name, ok, detail=""):
    print("  [%s] %s%s" % ("ok" if ok else "FAIL", name,
                           ("  -- " + detail) if detail and not ok else ""))
    if not ok:
        _fails.append(name)
    return ok


def strings(path, minlen=4):
    with open(path, "rb") as f:
        data = f.read()
    return data, re.findall(rb"[ -~]{%d,}" % minlen, data)


def entropy(buf):
    counts = [0] * 256
    for b in buf:
        counts[b] += 1
    n = float(len(buf))
    return -sum((c / n) * math.log2(c / n) for c in counts if c)


def main():
    if not os.path.exists(TARBALL):
        raise SystemExit("missing %s -- run `make dist` first" % TARBALL)

    with open(FLAG_TXT, "rb") as f:
        flag = f.read().strip()
    with open(PATH_JSON) as f:
        meta = json.load(f)
    path = meta["path"]

    tmp = tempfile.mkdtemp(prefix="wam-verify-")
    try:
        extract = os.path.join(tmp, "extract")
        os.makedirs(extract)
        with tarfile.open(TARBALL) as tf:
            names = tf.getnames()
            tf.extractall(extract)

        mallet = os.path.join(extract, "mallet")
        holes_dir = os.path.join(extract, "holes")

        print("\n== handout ==")
        want = ({"mallet", "README.txt", "holes"} |
                {"holes/hole_%02d.bin" % i for i in range(NUM_HOLES)})
        got = {n for n in names if n not in (".", "./")}
        check("handout contains exactly mallet + README.txt + 100 holes",
              got == want, "unexpected: %s" % sorted(got - want)[:5])
        check("no author artefacts shipped",
              not any("path.json" in n or n.endswith(".c") or n.endswith(".py")
                      for n in names))

        data, strs = strings(mallet)

        print("\n== binary ==")
        check("strings mallet has no HIBCHB26",
              not [s for s in strs if b"hibchb26" in s.lower()])
        check("strings mallet has no M0LE",
              not [s for s in strs if b"m0le" in s.lower()])
        check("flag bytes absent from binary image", flag not in data)
        check("path bytes absent from binary image",
              bytes(path) not in data and
              bytes(reversed(path)) not in data)
        check("binary is stripped",
              b"debug_info" not in data and
              subprocess.run(["file", mallet], capture_output=True
                             ).stdout.find(b"not stripped") < 0)

        holes = []
        for i in range(NUM_HOLES):
            with open(os.path.join(holes_dir, "hole_%02d.bin" % i), "rb") as f:
                holes.append(f.read())

        print("\n== holes ==")
        check("all %d holes are exactly %d bytes" % (NUM_HOLES, HOLE_SIZE),
              all(len(h) == HOLE_SIZE for h in holes))
        digests = [hashlib.sha256(h).hexdigest() for h in holes]
        check("100 unique sha256 digests, no duplicates",
              len(set(digests)) == NUM_HOLES,
              "%d unique" % len(set(digests)))

        on = [entropy(holes[p]) for p in path]
        off = [entropy(holes[i]) for i in range(NUM_HOLES) if i not in path]
        mu, sd = statistics.mean(off), statistics.stdev(off)
        check("all holes above entropy floor %.2f b/B" % ENTROPY_FLOOR,
              min(on + off) >= ENTROPY_FLOOR, "min %.4f" % min(on + off))
        check("on-path entropy indistinguishable from off-path",
              abs(statistics.mean(on) - mu) <= 2 * sd and
              min(on) >= min(off) - sd and max(on) <= max(off) + sd,
              "on %.4f vs off %.4f (sd %.4f)" % (statistics.mean(on), mu, sd))

        print("\n== path / oracle ==")
        check("path contains %d distinct holes" % PATH_LEN,
              len(set(path)) == PATH_LEN == len(path))

        state, unique = SEED, True
        for r, pick in enumerate(path):
            hits = [p for p in range(NUM_HOLES)
                    if has_magic(mole_crypt(holes[p], state, p))]
            if hits != [pick]:
                unique = False
                print("      round %d: %s" % (r, hits))
            state = mole_advance(state, pick,
                                 mole_crypt(holes[pick], state, pick))
        check("exactly one hole carries the magic at every round", unique)

        rng = random.Random(0xB00B1E5)
        leaks = 0
        for _ in range(WRONG_PATH_TRIALS):
            first = rng.choice([p for p in range(NUM_HOLES) if p != path[0]])
            picks = [first] + [rng.randrange(NUM_HOLES)
                               for _ in range(PATH_LEN - 1)]
            s, haul = SEED, bytearray()
            for pick in picks:
                plain = mole_crypt(holes[pick], s, pick)
                haul += carve_fragment(plain)
                s = mole_advance(s, pick, plain)
            if b"HIBCHB26{" in bytes(haul):
                leaks += 1
        check("%d wrong paths leak no HIBCHB26{" % WRONG_PATH_TRIALS,
              leaks == 0, "%d leaks" % leaks)

        print("\n== solver ==")
        src = open(SOLVER).read()
        check("solve.py imports nothing from the build tree",
              not re.search(r"^\s*(import|from)\s+(molecrypt|gen)\b",
                            src, re.M))

        # The sandbox holds solve.py and the extracted holes and nothing else,
        # so a successful run *is* the proof that dist/ artefacts suffice.
        sandbox = os.path.join(tmp, "sandbox")
        os.makedirs(sandbox)
        shutil.copy(SOLVER, sandbox)
        shutil.copytree(holes_dir, os.path.join(sandbox, "holes"))
        check("solver sandbox holds only handout artefacts",
              sorted(os.listdir(sandbox)) == ["holes", "solve.py"])
        out = subprocess.run([sys.executable, "solve.py"], cwd=sandbox,
                             capture_output=True, text=True)
        check("solve.py recovers the flag from handout artefacts only",
              out.returncode == 0 and ("flag: " + flag.decode()) in out.stdout,
              out.stdout.strip().splitlines()[-1] if out.stdout else out.stderr)

        print("\n== binary end-to-end ==")
        stdin = "".join("%d,%d\n" % (p // 10, p % 10) for p in path)
        out = subprocess.run(["./mallet"], cwd=extract, input=stdin,
                             capture_output=True, text=True)
        check("mallet along the correct path prints the flag",
              ("Your haul: " + flag.decode()) in out.stdout)
        check("mallet never issues a verdict",
              not re.search(r"\b(correct|wrong|incorrect|nice|well done|"
                            r"good|bad|miss(ed)?|hit|found|congrat\w*)\b",
                            out.stdout, re.I))
        check("mallet ran exactly %d rounds" % PATH_LEN,
              out.stdout.count("Round ") == PATH_LEN)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("")
    if _fails:
        print("FAILED: %s" % ", ".join(_fails))
        return 1
    print("all invariants pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
