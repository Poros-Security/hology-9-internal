# Solver — Whack a Mole

```
tar xzf dist/handout.tar.gz -C /tmp/wam
cp solver/solve.py /tmp/wam
cd /tmp/wam && python3 solve.py
```

`solve.py` reads `holes/hole_00.bin .. hole_99.bin` from its working directory
(or from a directory passed as `argv[1]`) and nothing else. It does not import
`molecrypt.py`, does not read `src/`, and does not run `mallet`. `make verify`
enforces that by running it in a sandbox that contains only `solve.py` and the
extracted `holes/`.

Runtime: well under a second for the full 12 × 100 = 1200 trial decryptions.

## What a player has to work out

1. **There is no per-file key.** `mallet` derives the keystream from
   `(state, pick)`, and `state` starts at a hardcoded `SEED` and is stirred by
   *every* dig — including wrong ones. So hole 47's plaintext at round 3
   depends on the exact three digs before it. 100¹² paths, no per-round
   feedback.

2. **The oracle is in the plaintext, not the program.** A correctly-decrypted
   hole starts with `M0LE`. The binary never checks for it and never comments,
   but the hexdump puts it right in the ASCII column. That single observation
   collapses the search from 100¹² to 12 × 100.

3. **Greedy sweep.** At round `r`, decrypt all 100 holes under the current
   state, take the one that shows the magic, append its fragment, advance the
   state, repeat. Exactly one hole matches per round — the generator re-rolls
   the whole layout if a second one ever does.

## Alternate path (intentionally left open)

The state machine is fully observable through the binary, so a player can skip
the reversing entirely: at round 0 try all 100 holes, watch for `M0LE` in the
output, restart, replay the known prefix, brute the next round. ~1200 short
`mallet` runs under pwntools. Slower, and it rewards scripting instead of
reversing, but it is a legitimate solve. `mallet` runs unbuffered to keep it
comfortable.

Sanity check for that path, one round deep:

```sh
for i in $(seq 0 99); do
  printf '%d,%d\n' $((i/10)) $((i%10)) | ./mallet | head -30 | grep -q M0LE \
    && echo "round 0 mole: hole $i"
done
```
