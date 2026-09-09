from pathlib import Path
import math
import random

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.number import long_to_bytes
from sympy import primerange


class FactorFound(Exception):
    def __init__(self, divisor):
        self.divisor = divisor


def parse():
    output_path = Path(__file__).resolve().parents[1] / "dist" / "output.txt"
    values = {}
    for raw_line in output_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        label, value = line.split("=", 1)
        values[label.strip()] = int(value.strip(), 0)
    return values


def scalar(limit):
    scalar = 1
    for prime_base in primerange(2, limit + 1):
        prime_power = prime_base
        while prime_power * prime_base <= limit:
            prime_power *= prime_base
        scalar *= prime_power
    return scalar


def invert(item, composite):
    item %= composite
    shared = math.gcd(item, composite)
    if 1 < shared < composite:
        raise FactorFound(shared)
    if shared == composite:
        raise ZeroDivisionError
    return pow(item, -1, composite)


def add(first_point, second_point, composite):
    if first_point is None:
        return second_point
    if second_point is None:
        return first_point

    first_u, first_v = first_point
    second_u, second_v = second_point

    if (first_u - second_u) % composite == 0:
        if (first_v + second_v) % composite == 0:
            return None
        numerator = (3 * first_u * first_u) % composite
        denominator = (2 * first_v) % composite
    else:
        numerator = (second_v - first_v) % composite
        denominator = (second_u - first_u) % composite

    try:
        slope = (numerator * invert(denominator, composite)) % composite
    except ZeroDivisionError:
        return None

    next_u = (slope * slope - first_u - second_u) % composite
    next_v = (slope * (first_u - next_u) - first_v) % composite
    return next_u, next_v


def multiply(point, scalar, composite):
    total = None
    doubled = point

    while scalar:
        if scalar & 1:
            total = add(total, doubled, composite)
        scalar >>= 1
        if scalar:
            doubled = add(doubled, doubled, composite)

    return total


def recover(composite, smooth_limit):
    multiple = scalar(smooth_limit)

    for attempt in range(1, 80):
        rng = random.Random(0xC0FFEE + attempt)
        base_point = (
            rng.randrange(2, composite - 2),
            rng.randrange(2, composite - 2),
        )

        _curve_shift = (
            base_point[1] * base_point[1]
            - base_point[0] * base_point[0] * base_point[0]
        ) % composite

        try:
            multiply(base_point, multiple, composite)
        except FactorFound as hit:
            return hit.divisor

    raise RuntimeError("stage-1 ECM did not hit; increase attempts")


def main():
    values = parse()
    composite = values["teapot"]
    button = values["button"]
    fortune = values["fortune"]
    smooth_limit = values["noodles"]

    hidden_factor = recover(composite, smooth_limit)
    sibling_factor = composite // hidden_factor
    totient = (hidden_factor - 1) * (sibling_factor - 1)
    handle = pow(button, -1, totient)

    key = RSA.construct(
        (composite, button, handle, hidden_factor, sibling_factor)
    )
    wrapped = long_to_bytes(fortune, key.size_in_bytes())
    flag = PKCS1_OAEP.new(key).decrypt(wrapped)

    print(f"factor = {hidden_factor}")
    print(f"flag = {flag.decode()}")


if __name__ == "__main__":
    main()
