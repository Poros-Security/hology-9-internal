# Organizer Writeup: lakaela

## Overview

`lakaela` is a menu-driven heap challenge for 64-bit Linux.  The intended solution uses the small-bin House of Water variant to obtain a chunk overlapping `tcache_perthread_struct`, then uses that metadata overlap to force `malloc(0x318)` to return a pointer to a PIE global named `sample_path`.  Changing `sample_path` to `/flag.txt` and selecting the smithing-ticket menu prints the flag.

The challenge is intended for players who understand allocations/frees, tcache, safe-linking, unsorted/smallbin sorting, and pwntools automation, but it avoids stack ROP, FSOP, libc hooks, or obscure post-exploitation tricks.

The title and player-facing strings use a fictional Kaela Kovalskia-inspired forge theme; the exploitation mechanics are unchanged and self-contained.

## Target versions

- Ubuntu 24.04 LTS Noble, amd64
- glibc package: `2.39-0ubuntu8.7`
- Architecture: x86-64

The Dockerfile pins `libc6`, `libc-bin`, and `libc6-dev` to the same Noble package version and compiles the service from `chall.c`.

## GZCTF dynamic-container notes

This package is arranged for the gzcli/GZCTF challenge contract:

- `challenge.yml` uses `type: DynamicContainer`.
- `container.flagTemplate` is `HIBCHB26{P3m4loe_f0rg3d_th3_w4t3r_h0us3_[TEAM_HASH]}`.
- `container.exposePort` is `31337`.
- `scripts.start` builds the image with `cd src && docker build -t {{.slug}} .`.
- GZCTF injects the per-team dynamic flag through `GZCTF_FLAG`.

The binary deliberately opens `/flag.txt` for the final objective.  To preserve that objective while supporting GZCTF dynamic flags, `src/run.sh` writes `${GZCTF_FLAG:-HIBCHB26{P3m4loe_f0rg3d_th3_w4t3r_h0us3_placeholder}}` to `/flag.txt` before starting `socat`.  If the variable is absent during local testing, the placeholder flag is used.

## Build protections

The Makefile uses:

```text
CFLAGS  = -Wall -Wextra -Wpedantic -O0 -g -fPIE -fno-stack-protector -D_FORTIFY_SOURCE=0
LDFLAGS = -pie -Wl,-z,relro,-z,now
```

Effective protections:

- PIE enabled: players need the slot-0 information leak to locate `sample_path`.
- NX enabled by default: no injected shellcode path is intended.
- Full RELRO: GOT overwrite is not available.
- Stack canary disabled: there is no intended stack overflow, so canaries would not teach anything for this challenge.
- Debug symbols retained: appropriate for an easy/intermediate educational heap challenge.

## Program model

The program keeps an array of global `note_t` records:

```c
typedef struct note {
    void *ptr;
    size_t size;
    unsigned int state;
} note_t;
```

Each menu-created entry stores a heap pointer, its requested size, and a state (`EMPTY`, `LIVE`, or `FREED`).  Slot 0 is a non-heap leak object containing two pointers as raw bytes:

1. `sample_path`, the global path used by `submit smithing ticket`.
2. `notes`, the global note table.

The second pointer is not needed by the reference exploit but helps players sanity-check the PIE base.

## Vulnerabilities

### 1. Stale view / UAF read

`delete_entry()` calls `free(notes[idx].ptr)` but does not clear the pointer or size.  `view_entry()` allows viewing both live and freed entries.

Impact: players can inspect stale allocator metadata.  In the reference path, the required address leak is slot 0 rather than a freed-bin leak, but the stale view is intentionally present for educational debugging and to expose tcache/smallbin contents.

### 2. Small negative metadata write

`calibrate_entry()` accepts a signed offset and allows offsets as low as `-0x20` for live entries, with at most 8 bytes written.

Impact: players can write values such as `0x331` at `ptr - 0x18` and restore `0x91` at `ptr - 0x8`.  This is enough to craft fake chunk size fields for the small-bin House of Water setup.

### 3. Fake free at `ptr - 0x10`

`peel_label()` calls:

```c
free((unsigned char *)notes[idx].ptr - 0x10);
```

It is restricted to live entries of requested size `0x88` so the challenge nudges players toward the intended layout.

Impact: after writing fake sizes with `calibrate_entry()`, players can free fake chunks into the `0x320` and `0x330` tcache bins.  These fake tcache entries overlap the tcache metadata positions later used as the fake smallbin chunk's `fd` and `bk` fields.

### 4. One-byte stale NUL write

`rinse_entry()` writes one `\0` byte into a freed entry at a chosen offset.

Impact: after the 0x90 chunks are sorted into the smallbin, this allows the exploit to overwrite only the low byte of:

- `small_start->fd` at offset `0`
- `small_end->bk` at offset `8`

The write changes pointers that originally reference the `relative_chunk` header in the `heap_base + 0x2??` range to `heap_base + 0x200`, the fake House of Water chunk header inside `tcache_perthread_struct` metadata.

## Intended heap layout

The first real heap allocation in the intended path is the `relative_chunk`; no heap object is allocated by slot 0.  This preserves the classic House of Water layout near the start of the heap.

The solver allocates:

```text
idx 1: relative_chunk, 0x88 request -> 0x90 chunk
idx 2: guard,          0x18 request -> 0x20 chunk
idx 3: small_start,    0x88 request -> 0x90 chunk
idx 4: guard,          0x18 request -> 0x20 chunk
idx 5: small_end,      0x88 request -> 0x90 chunk
idx 6: guard,          0x18 request -> 0x20 chunk
```

The guard chunks prevent consolidation when the three 0x90 chunks are later freed.

## Why House of Water applies

House of Water targets the `tcache_perthread_struct` metadata placed at the beginning of the heap.  The small-bin variant links a fake chunk inside this metadata into a smallbin list.  Once the fake metadata chunk is returned by `malloc`, the attacker can edit tcache metadata directly.

This challenge provides exactly the constrained primitives needed for the variant:

1. controlled heap layout with 0x90 chunks and guards,
2. fake frees into the 0x320 and 0x330 tcache bins,
3. real frees into the unsorted bin and sorting into the smallbin,
4. one-byte UAF NUL writes to redirect smallbin `fd`/`bk`, and
5. allocation of the fake chunk at `heap_base + 0x210`, overlapping useful tcache entries.

No brute force is required because the one-byte overwrite is deterministic: the target relative pointer naturally resides in the `heap_base + 0x2??` range, and zeroing the low byte redirects it to `heap_base + 0x200`.

## Exploitation stages

### Stage 1: Leak PIE

View slot 0:

```text
3 -> index 0
```

The first eight bytes are the absolute address of `sample_path`.  Because the binary is PIE, this leak is required to know where to point the final tcache allocation.

The solver computes the PIE base only for logging:

```python
sample_path = u64(leak[:8])
exe.address = sample_path - exe.sym["sample_path"]
```

The exploit ultimately uses the absolute leaked `sample_path` address directly.

### Stage 2: Arrange the 0x90 smallbin candidates

Allocate three `0x88` entries separated by `0x18` guards:

```text
relative_chunk, guard, small_start, guard, small_end, guard
```

The order and sizes matter.  `relative_chunk` must be close to the tcache metadata at the beginning of the heap so that its smallbin pointers can be redirected with a single low-byte NUL.

### Stage 3: Create fake 0x330 and 0x320 tcache entries

For `small_start`:

1. write `0x331` at `small_start - 0x18`,
2. call `peel_label(small_start)`, freeing `small_start - 0x10`,
3. restore the real chunk size at `small_start - 0x8` to `0x91`.

For `small_end`:

1. write `0x321` at `small_end - 0x18`,
2. call `peel_label(small_end)`, freeing `small_end - 0x10`,
3. restore the real chunk size at `small_end - 0x8` to `0x91`.

These fake tcache frees seed the tcache metadata so the future fake smallbin chunk has plausible `fd` and `bk` values.

### Stage 4: Fill the 0x90 tcache

Allocate and free seven additional `0x88` entries.  The 0x90 tcache bin is now full.

This matters because the next frees of `small_end`, `relative_chunk`, and `small_start` must bypass tcache and enter the unsorted bin.

### Stage 5: Build and sort the unsorted list

Free in this order:

```text
small_end
relative_chunk
small_start
```

Then allocate a large chunk, e.g. `0x700`, to force glibc to sort the unsorted chunks into the 0x90 smallbin.

The useful order becomes:

```text
small_start <-> relative_chunk <-> small_end
```

### Stage 6: Redirect smallbin links with one-byte UAF writes

Use `rinse_entry()` on freed chunks:

```text
rinse small_start offset 0
rinse small_end   offset 8
```

This zeroes the least significant byte of `small_start->fd` and `small_end->bk`, redirecting both from the `relative_chunk` header to the fake chunk header at `heap_base + 0x200`.

This handles safe-linking because the modified pointers are smallbin `fd`/`bk` pointers, not safe-linked tcache/fastbin `next` pointers.

### Stage 7: Allocate the fake tcache metadata chunk

Drain the seven real 0x90 tcache chunks, then allocate three more `0x88` entries:

1. first returns `small_start`,
2. second returns `small_end`,
3. third returns the fake chunk at `heap_base + 0x210`.

The third chunk overlaps tcache metadata entries.  In the tested glibc family, the start of the returned fake user chunk overlaps the tcache entries for the `0x320` / `0x330` size classes that were seeded earlier.

### Stage 8: Turn metadata control into an allocation over `sample_path`

The fake 0x321 free left the `0x320` tcache count nonzero.  Edit the metadata-overlap chunk so the 0x320 tcache entry head is `sample_path`:

```python
edit(meta_idx, p64(sample_path))
create(target_idx, 0x318)   # malloc returns sample_path
```

Tcache entry heads are stored raw; safe-linking protects the `next` pointer inside freed chunks, not the `tcache->entries[idx]` head pointer itself.  The target is 16-byte aligned, so it passes glibc's alignment check.

The returned chunk overlaps the global `sample_path` buffer.  Write:

```text
/flag.txt\0
```

Then choose `submit smithing ticket`; the program opens `sample_path`, reads the file, and prints it.

## Address leaks

The required leak is the PIE leak from slot 0.  It is deterministic and script-friendly.  The challenge also allows stale views of freed heap chunks, so players can inspect safe-linked tcache pointers or libc main-arena pointers during development, but the reference chain only needs the PIE leak because the House of Water pointer redirection is a deterministic low-byte operation.

## Modern glibc mitigations handled

- **Safe-linking:** avoided in the smallbin-link redirection stage; later tcache metadata control writes the raw tcache head pointer, which is not safe-linked.
- **Tcache double-free key:** ordinary double free is not used.  Fake frees use distinct fake pointers at `small_start - 0x10` and `small_end - 0x10`.
- **Full RELRO:** no GOT overwrite.
- **PIE:** defeated by the slot-0 information leak.
- **NX:** irrelevant because the exploit uses a data-only file-read primitive, not shellcode.

## Allocation ordering and size constraints

Important constants:

- `0x88` request -> `0x90` chunk, used by House of Water smallbin list.
- `0x18` request -> `0x20` guard chunk.
- fake size `0x331` -> 0x330 tcache bin.
- fake size `0x321` -> 0x320 tcache bin.
- final request `0x318` -> 0x320 tcache bin.

Important ordering:

1. allocate `relative`, `small_start`, `small_end` with guards,
2. fake-free `small_start - 0x10` and `small_end - 0x10`,
3. fill the 0x90 tcache,
4. free `small_end`, `relative`, `small_start`,
5. allocate a large chunk to sort unsorted into smallbin,
6. apply two NUL-byte UAF writes,
7. drain tcache and allocate the fake metadata chunk,
8. poison the 0x320 tcache entry to `sample_path`,
9. overwrite `sample_path` and submit.

## Reliability

The intended chain is deterministic inside the pinned container.  It does not depend on brute force, sleeps, races, thread scheduling, or stack layout.  The key assumptions are:

- ASLR is enabled, but the PIE target address is leaked.
- The first intended heap allocation occurs before other heap allocations by the program.
- The glibc allocator layout matches Ubuntu 24.04 glibc 2.39.
- `sample_path` remains 16-byte aligned.

## Possible unintended solutions and mitigations

- **Direct stack overflow:** none of the line-based input paths writes to stack buffers without bounds.
- **Command injection:** `submit smithing ticket` uses `open()` directly, not `system()`.
- **Immediate win function:** no `win()` function exists.
- **GOT overwrite:** full RELRO prevents it.
- **Writable function pointer overwrite:** no function pointer dispatch table is exposed.  The final target is data-only path control.
- **Classic tcache poisoning from UAF edit:** the program does not provide arbitrary writes to freed tcache chunks.  `rinse_entry()` only writes a single NUL byte into stale chunks, which is enough for House of Water but not enough for a trivial safe-linking-aware arbitrary tcache poison.
- **House of Force / top chunk:** allocation sizes are capped at `0x800`, and there is no top-size overwrite primitive.
- **Direct arbitrary write from calibration:** `calibrate_entry()` only works on live entries, is limited to offsets `[-0x20, size)`, and writes at most 8 bytes.  It is sufficient for fake size fields but not a general write-what-where.
