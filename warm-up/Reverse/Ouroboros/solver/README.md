# Ouroboros — writeup

**Category:** Reverse · **Difficulty:** Hard · **Flag:** `HIBCHB26{1t_e4ts_1ts_0wn_byt3c0d3_t0_st4y_w4rm}`

Players get `ouroboros.zip` containing `ouroboros.pyc` (CPython 3.12) and a
usage-only `README.txt`.

```
$ python ouroboros.pyc
flag: HIBCHB26{test}
Nope.
```

---

## Step 1 — the decompiler gives up

The header is valid this time (`cb 0d 0d 0a` = 3.12), so the file runs. But
3.12 is a dead zone for off-the-shelf decompilers: `uncompyle6` and
`decompyle3` do not support it at all, and `pycdc` bails halfway:

```
# Source Generated with Decompyle++
# File: ouroboros.pyc (Python 3.12)

__doc__ = None
import marshal
import sys
import types
PAYLOAD = b'\xfe\xb0\x9c*\xd9\xf4\xac\x90P\xe1...'
PAYLOAD_ALT = b'\xc2X\x17\xf64i\x10\xfb\x98G\xe8...'
MASK = 0xFFFFFFFFFFFFFFFF

def _fnv(l):
    I = 0xCBF29CE484222325
    for ll in l:
        I ^= ll
        I = I * 0x100000001B3 & MASK
    return I


def _boot(l):
    if len(sys.argv) * 0 + 1 == 2:
        I = PAYLOAD_ALT
        ll = _fnv(PAYLOAD_ALT) >> 7
    else:
        I = PAYLOAD
        ll = 0
    lI = ll
# WARNING: Decompyle incomplete
```

It dies exactly where the challenge starts. Note also:

- `co_filename` is `<frozen importlib._bootstrap>` and `co_linetable` is
  empty, so there are no line numbers anywhere and tracebacks are useless;
- every local is named out of `l`/`I`/`1`;
- `len(sys.argv) * 0 + 1 == 2` is an opaque predicate — that whole branch,
  including the `PAYLOAD_ALT` "key derivation", is dead. `PAYLOAD_ALT` is also
  the *larger* of the two blobs, so grabbing the biggest `bytes` constant is a
  trap.

So: `marshal` it yourself and read `dis`.

```python
import marshal, dis, types
mod = marshal.loads(open("ouroboros.pyc", "rb").read()[16:])
boot = next(c for c in mod.co_consts
            if isinstance(c, types.CodeType) and c.co_name == "_boot")
dis.dis(boot)
```

## Step 2 — the snake eats its tail

Past the dead branch, `_boot` checks whether it is being watched:

```
    140 LOAD_GLOBAL              3 (NULL + sys)
    150 LOAD_ATTR               12 (gettrace)
    170 CALL                     0
    178 POP_JUMP_IF_NONE         2 (to 184)
    180 LOAD_CONST               2 (1)
    182 STORE_FAST               3 (lI)
>>  184 LOAD_GLOBAL              3 (NULL + sys)
    194 LOAD_ATTR               14 (getprofile)
    ...
>>  228 LOAD_CONST               5 ('bdb')
    230 LOAD_GLOBAL              2 (sys)
    240 LOAD_ATTR               16 (modules)
    260 CONTAINS_OP              0
    ...
>>  304 LOAD_GLOBAL             19 (NULL + range)
    314 LOAD_CONST               7 (6)
    316 CALL                     1
    324 GET_ITER
>>  326 FOR_ITER                36 (to 402)
    330 STORE_FAST               4 (l1)
    332 LOAD_GLOBAL              2 (sys)     # sys.monitoring.get_tool(l1)
```

`sys.gettrace()`, `sys.getprofile()`, `bdb`/`pdb` in `sys.modules`, and
`sys.monitoring.get_tool(0..5)` — the last one is the 3.12 API, so a tool
registered through `sys.monitoring` is caught even though `sys.settrace` is
untouched. All four write `1` into the same local. Hold that thought.

Then the key:

```
    404 LOAD_GLOBAL              9 (NULL + _fnv)
    414 LOAD_GLOBAL             24 (_boot)
    424 LOAD_ATTR               26 (__code__)
    444 LOAD_ATTR               28 (co_code)
    464 CALL                     1
    472 LOAD_FAST                3 (lI)
    474 BINARY_OP               12 (^)
    478 STORE_FAST               5 (Il)
```

**The key is FNV-1a of `_boot`'s own bytecode**, xored with the "am I watched"
flag. Two consequences:

1. The key is stored nowhere. You have to hash the shipped `co_code` exactly
   as it is — which is why the build guarantees the constant splice does not
   perturb a single instruction byte.
2. **Patching is off the table.** NOP out one instruction to skip a check and
   the key changes:

   ```
   ValueError: bad marshal data (unknown type code)
   ```

The rest of `_boot` picks a half of `PAYLOAD` and XOR-decrypts it with a
SplitMix64 keystream seeded by the key:

```python
span = len(vault) >> 1
head = (seed & 1) * span            # which half depends on the key itself
out  = bytearray(vault[head:head + span])
state = seed
# state = (state + 0x9E3779B97F4A7C15) & M64 ; z = state
# z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & M64
# z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & M64
# z ^= z >> 31        -> 8 keystream bytes, little-endian
types.FunctionType(marshal.loads(bytes(out)), globals())(candidate)
```

## Step 3 — why the debugger lied

The watch flag flips **bit 0** of the key. Bit 0 is also the half selector.
So `PAYLOAD` is two ciphertexts: the real stage 2 at index `key & 1` under
key `key`, and a **decoy stage 2** at index `(key ^ 1) & 1` under key
`key ^ 1`. Under instrumentation everything still decrypts to a perfectly
valid code object with the same shape — it just checks against a different
target table:

```
$ echo "$FLAG" | python ouroboros.pyc                      # clean
flag: Correct!
$ echo "$FLAG" | python trace_it.py                        # sys.settrace
flag: Nope.
$ echo "HIBCHB26{n0t_th3_r34l_0n3_k33p_g01ng__________}" | python trace_it.py
flag: Correct!
```

Anyone who "just debugs it" walks away with
`HIBCHB26{n0t_th3_r34l_0n3_k33p_g01ng__________}` and no error message to
suggest otherwise. (Incidentally `python -m pdb ouroboros.pyc` does not even
start — pdb `compile()`s the file as text and chokes on the null bytes. Any
harness that gets pdb far enough to run the module has imported `bdb`, which
is check #3.)

The correct move is offline: reimplement FNV-1a + SplitMix64, hash the code
object you unmarshalled, and decrypt. No instrumentation, no bit flip.

## Step 4 — stage 2 is a stack VM

`dis` the decrypted code object. It is a `while True:` over a `bytes` constant
with a long `elif` chain on `op` — a hand-rolled VM. Reading it off gives the
opcode table (deliberately shuffled):

| byte | mnemonic | operand | behaviour |
|---|---|---|---|
| `0x1D` | `HALT` | — | stop |
| `0x4A` | `PUSHI` | u8 | push immediate byte |
| `0x9F` | `PUSHW` | u32 LE | push immediate dword |
| `0x22` | `LOADIN` | u8 | push `input[B + n]` |
| `0x93` | `LOADT` | u8 | push `target[B + n]` |
| `0x6E` / `0xB1` / `0x07` / `0x55` | `XOR` / `ADD` / `SUB` / `MUL` | — | mod 2³² |
| `0xC4` / `0x39` | `ROTL` / `ROTR` | u8 | 32-bit rotate |
| `0x64` | `SHR` | u8 | logical shift right |
| `0x8C` | `RNG` | — | push low 32 bits of the next SplitMix64 output |
| `0xE0` / `0x71` / `0xAB` | `DUP` / `SWAP` / `POP` | — | stack juggling |
| `0x16` | `CMP` | — | `ok &= (a == b)` |
| `0xD2` | `JNZ` | i8 | branch if TOS ≠ 0 |
| `0x3E` / `0xF7` | `PUSHB` / `SETB` | — | read/write the index register `B` |

73 bytes of program disassemble to a single loop:

```
0000  LOADIN  0
0002  RNG            0016  RNG            0030  RNG            0044  RNG
0003  XOR            0017  XOR            0031  XOR            0045  XOR
0004  ROTL    7      0018  ROTL    11     0032  ROTL    17     0046  ROTL    5
0006  PUSHW   0x9e3779b1  (same)               (same)               (same)
0011  MUL            0025  MUL            0039  MUL            0053  MUL
0012  DUP            0026  DUP            0040  DUP            0054  DUP
0013  SHR     13     0027  SHR     13     0041  SHR     13     0055  SHR     13
0015  XOR            0029  XOR            0043  XOR            0057  XOR
0058  LOADT   0
0060  CMP
0061  PUSHB / 0062 PUSHI 1 / 0064 ADD / 0065 SETB      ; B += 1
0066  PUSHB / 0067 PUSHI 12 / 0069 SUB
0070  JNZ     -72   -> 0
0072  HALT
```

So the candidate is cut into 4-byte little-endian blocks (the flag is 47 bytes
→ 12 blocks, the last one zero-padded) and each block goes through 4 rounds of

```
b ^= rng_next()
b  = rotl(b, r)                 # r = 7, 11, 17, 5
b  = (b * 0x9E3779B1) & 0xFFFFFFFF
b ^= b >> 13
```

with the result compared to `TARGET[n]`. Crucially the SplitMix64 state is
**chained across blocks**: block *n*'s four draws depend on the 4·*n* draws
before it, so you cannot attack a block in isolation — you have to replay the
generator from `SEED` (another constant in stage 2) in order.

## Step 5 — invert

Every round step is invertible, no solver needed:

- `b ^= b >> 13` → fixed-point iterate `x = y ^ (x >> 13)` (converges in
  ⌈32/13⌉ = 3 rounds);
- `b * 0x9E3779B1` → multiply by `pow(0x9E3779B1, -1, 2**32)`; the constant is
  odd, so it is a unit mod 2³²;
- `rotl(b, r)` → `rotr(b, r)`;
- `b ^= rng` → xor the same value back.

Walk the blocks in order, drawing 4 RNG values per block *forwards* and
consuming them *backwards* inside the block:

```python
state = SEED
for word in TARGET:
    draws = [next_rng() for _ in range(4)]
    b = word
    for r, k in zip(reversed(ROUNDS), reversed(draws)):
        b = unxorshr(b, 13)
        b = (b * INV) & 0xFFFFFFFF
        b = rotr(b, r)
        b ^= k
    out += b.to_bytes(4, "little")
```

Strip the trailing `\x00` padding and decode:

```
HIBCHB26{1t_e4ts_1ts_0wn_byt3c0d3_t0_st4y_w4rm}
```

```
$ echo 'HIBCHB26{1t_e4ts_1ts_0wn_byt3c0d3_t0_st4y_w4rm}' | python3.12 ouroboros.pyc
flag: Correct!
```

---

## Running the solver

```
$ python3.12 solver/solve.py
[+] loader code object : _boot (942 bytes of co_code)
[+] FNV-1a key         : 0xa7b2b31a8ed6d099
[+] stage 2            : _run, half index 1
[+] VM program         : 73 bytes
[+] block pipeline     : xorrng -> rotl(7) -> mul(0x9e3779b1) -> xorshr(13) -> ...
[+] SplitMix64 seed    : 0x1d872b41a17f2e6d
[+] FLAG               : HIBCHB26{1t_e4ts_1ts_0wn_byt3c0d3_t0_st4y_w4rm}
[+] decoy (traced run) : HIBCHB26{n0t_th3_r34l_0n3_k33p_g01ng__________}
[+] matches src/flag.txt
```

Runs in well under a second. Standard library only, **CPython 3.12 required**
(`marshal` is version locked). Nothing is hardcoded:

- it does not trust `co_name`: it hashes *every* code object in the file and
  keeps the one whose FNV-1a decrypts a constant into something `marshal` will
  accept — that identifies `_boot` and the key at once;
- it then decrypts the other half under `key ^ 1` and reports the decoy too;
- the round structure is recovered by **symbolically executing** the VM
  program (`pipeline()`), not by pattern matching: the rotate amounts, the odd
  multiplier and the xorshift distance all fall out of the disassembly, so the
  same solver survives a rebuild with different parameters;
- the SplitMix64 seed is picked from stage 2's integer constants by trying
  each one and keeping whichever produces a well-formed `HIBCHB26{...}`.

Pass `-v` for the full VM program listing.

## Rabbit holes

- **`PAYLOAD_ALT`** is 8112 bytes of SplitMix64 output and is never read. It is
  larger than the real `PAYLOAD` (8016 bytes) specifically so that "decrypt the
  biggest blob" fails.
- **Patching** the trace checks out of `_boot` cannot work by construction —
  the bytecode *is* the key. Emulate or reimplement instead.
- **Instrumenting** stage 1 to dump the decrypted stage 2 hands you the decoy
  code object, whose target table decodes to a fake flag of exactly the same
  length. Nothing in the output distinguishes it; you find it by noticing the
  `^ watched` on the key and the `(seed & 1) * span` half selector.
- **Line numbers** in any traceback are nonsense (`co_firstlineno` = 1337, and
  the line table is empty, which is enough to make `traceback` itself raise).
  Don't chase them.
