from Crypto.Util.number import getRandomNBitInteger, isPrime, inverse
from cysignals.alarm import AlarmInterrupt
from math import gcd
import signal,os

FLAG = os.getenv("GZCTF_FLAG", "HOLOGY9{fake_flag}")

z = 200
n = 4

def prime(low):
    while True:
        p = (getRandomNBitInteger(1024 - z) << z) | low
        if p.bit_length() == 1024 and isPrime(p):
            return p

def challenge():
    low = getRandomNBitInteger(z) | 1
    p, q = prime(low), prime(low)

    while p == q:
        q = prime(low)

    N = p * q
    psi = ((p**n - 1) // (p - 1)) * ((q**n - 1) // (q - 1))

    while True:
        d = getRandomNBitInteger(int(.94 * N.bit_length())) | 1
        if gcd(d, psi) == 1:
            e = inverse(d, psi)
            break

    print(f"N = {N}")
    print(f"e = {e}")
    print(f"z = {z}")

    x = int(input(">> "))

    if not 1 < x < N or N % x:
        print("!")
        return

    signal.alarm(0)
    print(FLAG)

try:
    signal.alarm(600)
    challenge()
except AlarmInterrupt:print("Sry, More faster")
except Exception as e:print(f"Exception: {e}")