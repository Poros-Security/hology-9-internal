from sage.all import *
from pwn import *

conn = process(["python3","chall.py"])
conn.sendlineafter(b"> ", b"1")

n = int(conn.recvline_contains(b"n = ").split(b" = ")[1])
e = int(conn.recvline_contains(b"e = ").split(b" = ")[1])
c = int(conn.recvline_contains(b"c = ").split(b" = ")[1])
coeffs = int(conn.recvline_contains(b"coeffs = ").split(b" = ")[1])
mod = int(conn.recvline_contains(b"mod = ").split(b" = ")[1])
D = int(conn.recvline_contains(b"D = ").split(b" = ")[1])
line = conn.recvline_contains(b"quotient = ")
A, B = map(int, line.split(b"(")[1].rstrip(b")\n").split(b","))

F = GF(mod)
R.<x> = PolynomialRing(F)
Q.<X> = R.quotient(x^2 - F(D))
leak = Q(F(A) + F(B)*X)
P.<y> = PolynomialRing(F)
f = 5*y^2 + 10*F(D)*y + F(D)^2 - F(B)

r_candidates = []
for y0 in f.roots(multiplicities=False):
    for r in y0.sqrt(all=True, extend=False):
        if Q(r + X)^5 == leak:
            r_candidates.append(ZZ(r))

p = q = None

for r in r_candidates:
    delta = r^2 + 4*coeffs*n
    if delta.is_square():
        p = (-r + delta.sqrt()) // (2*coeffs)
        q = n // p
        break

assert p*q == n

phi = (p - 1) * (q - 1)
d = pow(int(e), -1, int(phi))
secret = pow(int(c), d, int(n))
print(f"[+] r      = {r}")
print(f"[+] p      = {p}")
print(f"[+] q      = {q}")
print(f"[+] secret = {secret}")

conn.sendlineafter(b"> ", b"2")
conn.sendlineafter(b"secret?> ", str(secret).encode())
conn.interactive()
