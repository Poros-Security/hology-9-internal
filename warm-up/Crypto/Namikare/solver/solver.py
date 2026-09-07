import ast
from itertools import combinations
from Crypto.Util.number import long_to_bytes
from math import gcd, isqrt
from fpylll import IntegerMatrix, LLL
from pwn import *

def lll_rows(rows):
    basis = IntegerMatrix(len(rows), len(rows[0]))
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            basis[i, j] = int(value)
    LLL.reduction(basis)
    return [[int(basis[i, j]) for j in range(basis.ncols)] for i in range(basis.nrows)]

def factor_from_two_hints(h1, h2, n):
    scale = 1 << 624
    rows = [[1, 0, 0, h1 * h1 * scale],[0, 1, 0, h2 * h2 * scale],[0, 0, 1, h1 * h2 * scale],[0, 0, 0, n * scale],]
    reduced = lll_rows(rows)
    candidates = [row[:3] for row in reduced if row[3] == 0 and any(row[:3])]
    if not candidates:
        candidates = [min(reduced, key=lambda row: abs(row[3]))[:3]]

    for x1, x2, x3 in candidates:
        for sign in (1, -1):
            X1, X2, X3 = sign * x1, sign * x2, sign * x3
            disc = X3 * X3 - 4 * X1 * X2
            if disc < 0:
                continue
            root = isqrt(disc)
            if root * root != disc:
                continue

            roots = (((-X3 + root) // 2, (-X3 - root) // 2),((-X3 - root) // 2, (-X3 + root) // 2),)
            for X4, X5 in roots:
                if X4 + X5 != -X3:
                    continue

                A1 = gcd(abs(X2), abs(X5))
                A2 = gcd(abs(X1), abs(X4))
                factor = gcd(abs(A1 * h2 - A2 * h1), n)
                if 1 < factor < n:
                    return factor, n // factor

                B1 = gcd(abs(X2), abs(X4))
                B2 = gcd(abs(X1), abs(X5))
                factor = gcd(abs(B1 * h2 - B2 * h1), n)
                if 1 < factor < n:
                    return factor, n // factor

    log.failure("Lattice dua-hint ga nemu faktor")
    return None, None

def recover_factors(hints, n):
    if len(hints) == 1:
        factor = gcd(hints[0], n)
        if 1 < factor < n:
            return factor, n // factor
        log.warning("Kurang hint..")
        return None, None

    for h1, h2 in combinations(hints, 2):
        p, q = factor_from_two_hints(h1, h2, n)
        if p is not None and q is not None:
            return p, q
            
    log.failure("Gagal faktorin dari hints yang ada :(")
    return None, None

def decrypt_message(c, p, q):
    n = p * q
    phi = (p - 1) * (q - 1)
    if gcd(3, phi) != 1:
        log.failure("Eksponen ndak bisa diinvers.")
        return None
    d = pow(3, -1, phi)
    return pow(c, d, n)

def parse_instance(text):
    n = int(re.search(r"n = (\d+)", text).group(1))
    c = int(re.search(r"c = (\d+)", text).group(1))
    hints = ast.literal_eval(re.search(r"hints = (\[.*\])", text).group(1))
    return n, c, hints

def solve(io):
    preamble = io.recvuntil(b"Scramble>> ").decode()
    n, c, hints = parse_instance(preamble)
    print(f"Gotted {len(hints)} hints from server")

    p, q = recover_factors(hints, n)
    if p is None or q is None:
        print("Faktor ga nemu. jalanin ulang.")
        return
    
    m = decrypt_message(c, p, q)
    if m is None:
        return
        
    if pow(m, 3, n) != c:
        print("Plaintext tidak cocok")
        return
        
    print(f"Plaintext (m) berhasil didapatkan: {m}")

    io.sendline(b"0")
    io.recvuntil(b"Guess?>")

    for index, _hint in enumerate(hints):
        io.sendline(str(m).encode())
        if index + 1 != len(hints):
            io.recvuntil(b"Guess?>")

    tail = io.recvall(timeout=2).decode(errors='ignore')
    numbers = re.findall(r"\d+", tail)
    
    if not numbers:
        print("Tidak menemukan integer akhir pada output.")
        print(f"Output server:{tail}")
        return

    flag_int = int(numbers[-1])
    flag_bytes = long_to_bytes(flag_int).decode()
    print(f"Gotted the flag!: {flag_bytes}")

if __name__ == "__main__":
    io = process(["python3", "chall.py"]) 
    solve(io) #Workss solper