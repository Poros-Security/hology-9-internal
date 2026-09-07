from Crypto.Util.number import getPrime
from random import randint; import random; from libnum import s2n;import signal
import os

FLAG = os.getenv("GZCTF_FLAG", "HOLOGY9{TEST_FLAG}")

def main():
    p = getPrime(1024)
    q = getPrime(1024)
    n = p * q
    e = s2n('kaw0ru') % 59033177831737

    r = random.Random() # Not mersenne, trust
    k = r.getrandbits(3)
    while k == 0:
        k = r.getrandbits(3)

    hints = []
    for _ in range(k):
        a, b = randint(0, 2**312), randint(0, 2**312)
        hints.append(a * p + b * q)

    m = r.getrandbits(2048)
    c = pow(m, e, n)
    print(f"n = {n}")
    print(f"c = {c}")
    print(f'hints = {hints}')

    scram = int(input('Scramble>> '))
    ct = sum([pow(h + scram, e, n) for h in hints]) % n
    print(f"ct = {ct}")
    print("Gimme your guess!")
    for _ in hints:
        guess = int(input("Guess?> "))
        if guess != m:
            print("!!!!!")
            exit(1)

    gift = FLAG
    print(s2n(gift))
    exit(0)

if __name__ == "__main__" :
    signal.alarm(30 * 2)
    try :
        main()
    except Exception as e :
        print(e.__class__)
