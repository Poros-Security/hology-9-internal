import os
import random

from Crypto.Cipher import AES
from Crypto.Hash import SHA256

FIELD = 23
TOTAL = 9
QUIET = 5
LOUD = TOTAL - QUIET
COUNT = 10
DOMAIN = b"committee-polynomial-v1"


def pairs():
    return [(left, right) for left in range(TOTAL) for right in range(left, TOTAL)]


def bytesrc(rng):
    def take(amount):
        return bytes(rng.randrange(0, 256) for _ in range(amount))

    return take


def value(poly, point):
    total = poly["bias"]
    for index, coeff in enumerate(poly["linear"]):
        total += coeff * point[index]
    for coeff, (left, right) in zip(poly["quad"], pairs()):
        total += coeff * point[left] * point[right]
    return total % FIELD


def make(rng):
    quiet = set(rng.sample(range(TOTAL), QUIET))
    secret = [rng.randrange(FIELD) for _ in range(TOTAL)]
    polys = []

    for _ in range(COUNT):
        poly = {
            "bias": rng.randrange(FIELD),
            "linear": [rng.randrange(FIELD) for _ in range(TOTAL)],
            "quad": [],
        }

        for left, right in pairs():
            if left in quiet and right in quiet:
                coeff = 0
            else:
                coeff = rng.randrange(1, FIELD)
            poly["quad"].append(coeff)

        polys.append(poly)

    target = [value(poly, secret) for poly in polys]
    return polys, target, secret


def seal(secret, flag, rng):
    material = bytes(secret) + DOMAIN
    key = SHA256.new(material).digest()
    nonce = bytesrc(rng)(12)
    box = AES.new(key, AES.MODE_GCM, nonce=nonce)
    body, tag = box.encrypt_and_digest(flag)
    return nonce.hex(), tag.hex(), body.hex()


def build(flag):
    rng = random.Random(int.from_bytes(os.urandom(24), "big"))
    polys, target, secret = make(rng)
    nonce, tag, body = seal(secret, flag, rng)
    return {
        "field": FIELD,
        "variables": TOTAL,
        "quiet": QUIET,
        "equations": polys,
        "target": target,
        "nonce": nonce,
        "tag": tag,
        "ciphertext": body,
    }

def emit(label, item):
    print(f"{label} = {item!r}")

def main():
    flag = os.environ.get("FLAG", "HOLOGY9{redacted}").encode()
    for label, item in build(flag).items():
        emit(label, item)

if __name__ == "__main__":
    main()
