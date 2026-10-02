import os
from secrets import randbits, randbelow
from Crypto.Util.number import getPrime, isPrime

FLAG = os.getenv("FLAG", "HOLOGY9{REDACTED}")
e = 65537

def mul(a, b, m, D):
    x, y = a
    u, v = b
    return ((x*u + y*v*D) % m, (x*v + y*u) % m)

def pw(a, n, m, D):
    r = (1, 0)
    while n:
        if n & 1: r = mul(r, a, m, D)
        a = mul(a, a, m, D)
        n >>= 1
    return r

while True:
    p, coeffs = getPrime(512), getPrime(32)
    r = randbits(384) 
    q = coeffs*p + r
    if isPrime(q):
        break

n = p*q
secret = randbits(256)
c = pow(secret, e, n)

while True:
    mod = getPrime(521)
    if mod % 4 == 3:
        break

while True:
    D = randbelow(mod - 2) + 2
    if pow(D, (mod - 1)//2, mod) == mod - 1:
        break

A, B = pw((r, 1), 5, mod, D)

while True:
    print("[1] Challenge")
    print("[2] Submit")
    print("[3] Exit")
    x = input(">>> ")

    if x == "1":
        print(f"n = {n}")
        print(f"e = {e}")
        print(f"c = {c}")
        print(f"coeffs = {coeffs}")
        print(f"mod = {mod}")
        print(f"D = {D}")
        print(f"quotient = ({A}, {B})")
        print("R = GF(mod)[x]/(x^2-D)")
        print("quotient = (r+x)^5")

    elif x == "2":
        try:
            if int(input("secret?> ")) == secret:
                print(FLAG)
                break
        except:
            pass
        print("Wrong.")

    elif x == "3":
        break