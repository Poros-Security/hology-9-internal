import os
import random
from math import isqrt

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.number import isPrime, long_to_bytes


SMALL_FACTOR_CEILING = 4096
FACTOR_BITS = 384
PUBLIC_POWER = 65537


def norm(node):
    left_arm, right_arm = node
    return left_arm * left_arm - left_arm * right_arm + right_arm * right_arm


def product(first_node, second_node):
    first_left, first_right = first_node
    second_left, second_right = second_node
    return (
        first_left * second_left - first_right * second_right,
        first_left * second_right
        + first_right * second_left
        - first_right * second_right,
    )


def pool(limit):
    reach = isqrt(limit * 4) + 12
    atoms = []
    for left_arm in range(-reach, reach + 1):
        for right_arm in range(-reach, reach + 1):
            size = norm((left_arm, right_arm))
            if 1 < size <= limit and isPrime(size):
                atoms.append((left_arm, right_arm, size))
    return atoms


def forge(rng, bit_goal, limit):
    atoms = pool(limit)
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
    while norm(crystal).bit_length() < bit_goal:
        live_atoms = [atom for atom in atoms if budgets[atom[2]] > 0]
        if not live_atoms:
            raise RuntimeError("smoothness budget exhausted")
        left_arm, right_arm, size = rng.choice(live_atoms)
        crystal = product(crystal, (left_arm, right_arm))
        smooth_size *= size
        budgets[size] -= 1
    return crystal, smooth_size


def genprime(rng, bit_goal):
    while True:
        sample = rng.getrandbits(bit_goal)
        sample |= (1 << (bit_goal - 1)) | 1
        if sample % PUBLIC_POWER != 1 and isPrime(sample):
            return sample


def genbytes(rng):
    def take(amount):
        return bytes(rng.randrange(0, 256) for _ in range(amount))

    return take


def vault(secret_text):
    rng = random.Random(int.from_bytes(os.urandom(16), "big"))

    while True:
        crystal, _ = forge(rng, FACTOR_BITS, SMALL_FACTOR_CEILING)
        crafted_factor = norm((crystal[0] - 1, crystal[1]))
        if (
            crafted_factor.bit_length() >= FACTOR_BITS - 5
            and crafted_factor % PUBLIC_POWER != 1
            and isPrime(crafted_factor)
        ):
            break

    plain_factor = genprime(rng, FACTOR_BITS)
    public_modulus = crafted_factor * plain_factor
    private_totient = (crafted_factor - 1) * (plain_factor - 1)
    private_power = pow(PUBLIC_POWER, -1, private_totient)

    key = RSA.construct(
        (public_modulus, PUBLIC_POWER, private_power, crafted_factor, plain_factor)
    )
    cipher = PKCS1_OAEP.new(key.publickey(), randfunc=genbytes(rng))
    sealed_text = cipher.encrypt(secret_text)

    return {
        "small_factor_ceiling": SMALL_FACTOR_CEILING,
        "factor_bits": FACTOR_BITS,
        "public_modulus": public_modulus,
        "public_power": PUBLIC_POWER,
        "sealed_text": int.from_bytes(sealed_text, "big"),
    }


def main():
    secret_text = os.environ.get("FLAG", "HOLOGY9{redacted}").encode()
    values = vault(secret_text)
    for label, value in values.items():
        if isinstance(value, int):
            print(f"{label} = {hex(value)}")
        else:
            print(f"{label} = {value!r}")


if __name__ == "__main__":
    main()
