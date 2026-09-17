import os
import random
from math import isqrt

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.number import isPrime, long_to_bytes


NOODLES = 4096
LUGGAGE = 384
BUTTON = 65537


def weigh(node):
    left_arm, right_arm = node
    return left_arm * left_arm - left_arm * right_arm + right_arm * right_arm


def stir(first_node, second_node):
    first_left, first_right = first_node
    second_left, second_right = second_node
    return (
        first_left * second_left - first_right * second_right,
        first_left * second_right
        + first_right * second_left
        - first_right * second_right,
    )


def market(limit):
    reach = isqrt(limit * 4) + 12
    atoms = []
    for left_arm in range(-reach, reach + 1):
        for right_arm in range(-reach, reach + 1):
            size = weigh((left_arm, right_arm))
            if 1 < size <= limit and isPrime(size):
                atoms.append((left_arm, right_arm, size))
    return atoms


def cook(rng, bit_goal, limit):
    atoms = market(limit)
    budgets = {}
    for _, _, size in atoms:
        if size in budgets:
            continue
        power = size
        budgets[size] = 0
        while power <= limit:
            budgets[size] += 1
            power *= size

    crystal = (1, 0)
    smooth_size = 1
    while weigh(crystal).bit_length() < bit_goal:
        live_atoms = [atom for atom in atoms if budgets[atom[2]] > 0]
        if not live_atoms:
            raise RuntimeError("smoothness budget exhausted")
        left_arm, right_arm, size = rng.choice(live_atoms)
        crystal = stir(crystal, (left_arm, right_arm))
        smooth_size *= size
        budgets[size] -= 1
    return crystal, smooth_size


def pick(rng, bit_goal):
    while True:
        sample = rng.getrandbits(bit_goal)
        sample |= (1 << (bit_goal - 1)) | 1
        if sample % BUTTON != 1 and isPrime(sample):
            return sample


def sprinkle(rng):
    def take(amount):
        return bytes(rng.randrange(0, 256) for _ in range(amount))

    return take


def box(secret_text):
    rng = random.Random(int.from_bytes(os.urandom(16), "big"))

    while True:
        crystal, _ = cook(rng, LUGGAGE, NOODLES)
        jade = weigh((crystal[0] - 1, crystal[1]))
        if (
            jade.bit_length() >= LUGGAGE - 5
            and jade % BUTTON != 1
            and isPrime(jade)
        ):
            break

    paper = pick(rng, LUGGAGE)
    teapot = jade * paper
    receipt = (jade - 1) * (paper - 1)
    handle = pow(BUTTON, -1, receipt)

    key = RSA.construct(
        (teapot, BUTTON, handle, jade, paper)
    )
    cipher = PKCS1_OAEP.new(key.publickey(), randfunc=sprinkle(rng))
    fortune = cipher.encrypt(secret_text)

    return {
        "noodles": NOODLES,
        "luggage": LUGGAGE,
        "teapot": teapot,
        "button": BUTTON,
        "fortune": int.from_bytes(fortune, "big"),
    }


def main():
    secret_text = (
        os.environ.get("GZCTF_FLAG")
        or os.environ.get("FLAG")
        or "HOLOGY9{redacted}"
    ).encode()
    values = box(secret_text)
    for label, value in values.items():
        if isinstance(value, int):
            print(f"{label} = {hex(value)}")
        else:
            print(f"{label} = {value!r}")


if __name__ == "__main__":
    main()
