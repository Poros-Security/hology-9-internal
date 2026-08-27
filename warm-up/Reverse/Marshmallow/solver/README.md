# Marshmallow — writeup

**Category:** Reverse · **Difficulty:** Easy · **Flag:** `HIBCHB26{h34d3rl3ss_pyc_st1ll_t04sts_th3_fl4g}`

Players get `marshmallow.zip` containing `marshmallow.pyc` and a one-line `README.txt`.

---

## Step 0 — it does not run

```
$ python marshmallow.pyc HIBCHB26{test}
RuntimeError: Bad magic number in .pyc file
```

A `.pyc` starts with a 16-byte header: 4 bytes of magic, 4 bytes of bit flags,
and 8 bytes of source mtime + size. Hexdump the file:

```
00000000  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |................|
00000010  e3 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |................|
```

The whole header is zeroed — the "top burned off". Everything from offset 16
onward is an intact `marshal` payload (`0xe3` is the marshal type code for a
code object with the ref flag set).

## Step 1 — get it back

Two equivalent options.

**Repair the header.** CPython 3.11's magic is `3495` → `a7 0d 0d 0a`. The
remaining 12 bytes are not validated when the source file is absent, so zeros
are fine:

```python
import importlib.util, pathlib
d = pathlib.Path("marshmallow.pyc").read_bytes()
pathlib.Path("fixed.pyc").write_bytes(importlib.util.MAGIC_NUMBER + b"\x00" * 12 + d[16:])
```

```
$ python3.11 fixed.pyc HIBCHB26{test}
Nope.
```

**Or skip the container entirely** and unmarshal the payload directly:

```python
import marshal
code = marshal.loads(open("marshmallow.pyc", "rb").read()[16:])
```

Either way you need a **CPython 3.11** interpreter — `marshal` is version
locked, and 3.10 or 3.12 will raise `ValueError: bad marshal data`.

## Step 2 — read the code

`pycdc` gives near-source output; plain `dis` is enough. The two interesting
constants are sitting in `co_consts` in the clear:

```python
>>> [c for c in code.co_consts if isinstance(c, bytes)]
[b't04st3d',
 b'\xe1\xd2\xc1\x96\xfd\xae\xdcC\x92!HO\x0e\x15\x92K\xa8w\xb6\xe8,\xfb4\xfc'
 b'\xa8\xaf\xc6\xfd\x84F\xd4\xf3\xe2\xe9n-w\x05\xe2K{/\xe6M\xce\xab']
```

`b't04st3d'` is obviously the key; the 46-byte blob is the target. And
`dis.dis(toast)`:

```
 11          76 LOAD_FAST                4 (x)
             78 LOAD_GLOBAL              4 (KEY)
             90 LOAD_FAST                2 (i)
             92 LOAD_GLOBAL              7 (NULL + len)
            104 LOAD_GLOBAL              4 (KEY)
            120 CALL                     1
            130 BINARY_OP                6 (%)
            134 BINARY_SUBSCR
            144 BINARY_OP               25 (^=)
            148 STORE_FAST               4 (x)

 12         150 LOAD_FAST                4 (x)
            152 LOAD_CONST               1 (3)
            154 BINARY_OP                3 (<<)
            158 LOAD_FAST                4 (x)
            160 LOAD_CONST               2 (5)
            162 BINARY_OP                9 (>>)
            166 BINARY_OP                7 (|)
            170 LOAD_CONST               3 (255)
            172 BINARY_OP                1 (&)
            176 STORE_FAST               4 (x)
```

So, per character index `i`:

```
x  = ord(c)
x ^= KEY[i % 7]
x  = ((x << 3) | (x >> 5)) & 0xFF     # rotate left 3
x  = (x + i * 7) & 0xFF
```

and the result is compared against `TARGET`. The length check
`len(candidate) != len(TARGET)` also hands you the flag length for free: 46.

## Step 3 — invert

Every step is invertible, so just run them backwards:

```python
def invert(target, key):
    out = []
    for i, t in enumerate(target):
        x = (t - i * 7) & 0xFF              # undo the index add
        x = ((x >> 3) | (x << 5)) & 0xFF    # rotate right 3
        x ^= key[i % len(key)]              # undo the xor
        out.append(x)
    return bytes(out)
```

```
HIBCHB26{h34d3rl3ss_pyc_st1ll_t04sts_th3_fl4g}
```

## Step 4 — verify

```
$ python3.11 fixed.pyc 'HIBCHB26{h34d3rl3ss_pyc_st1ll_t04sts_th3_fl4g}'
Correct!
```

---

## Running the solver

```
$ python3.11 solver/solve.py
[+] KEY    = b't04st3d'
[+] TARGET = b'\xe1\xd2\xc1\x96...'
[+] FLAG   = HIBCHB26{h34d3rl3ss_pyc_st1ll_t04sts_th3_fl4g}
[+] matches src/flag.txt
```

`solve.py` is standard library only. It reads the artifact out of
`dist/marshmallow.zip` (or a loose `dist/marshmallow.pyc`), unmarshals it, and
recovers `KEY`/`TARGET` by walking `co_consts` — nothing is hardcoded. It does
not even assume which literal is which: it tries each ordered pair and keeps
the one whose inverse is a well-formed `HIBCHB26{...}` string, then re-runs the
forward transform to confirm.

**It must be run with CPython 3.11**, because `marshal.loads` only understands
its own version's code objects.

## Rabbit holes / notes

- Rewriting the header with a *wrong* magic (3.10, 3.12) gets you past the
  "bad magic" error only to fail at `marshal.loads` — the version really does
  have to be 3.11.
- `co_filename` is `marshmallow.py`, not the build-time filename; there is no
  `__pycache__` path to leak the original module name.
- Nothing in the artifact prints or contains the flag: `grep HIBCHB26 dist/ -r`
  is empty by construction (`build.sh` fails the build otherwise).
