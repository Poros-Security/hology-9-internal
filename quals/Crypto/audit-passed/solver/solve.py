from pathlib import Path
import ast

from Crypto.Cipher import AES
from Crypto.Hash import SHA256


DOMAIN_TAG = b"dual-shadow-ring-v1"


def parse():
    output_path = Path(__file__).resolve().parents[1] / "dist" / "output.txt"
    values = {}
    for raw_line in output_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        label, value = line.split("=", 1)
        values[label.strip()] = ast.literal_eval(value.strip())
    return values


def centered(value, modulus_value):
    value %= modulus_value
    if value > modulus_value // 2:
        value -= modulus_value
    return value


def windows(center_value, radius, modulus_value):
    center_value %= modulus_value
    low = center_value - radius
    high = center_value + radius
    if low < 0:
        return [(0, high), (modulus_value + low, modulus_value - 1)]
    if high >= modulus_value:
        return [(low, modulus_value - 1), (0, high - modulus_value)]
    return [(low, high)]


def refine(ranges, multiplier, target_value, radius, modulus_value):
    next_ranges = []

    for low_secret, high_secret in ranges:
        low_product = multiplier * low_secret
        high_product = multiplier * high_secret

        for low_residue, high_residue in windows(
            target_value, radius, modulus_value
        ):
            wrap_low = (low_product - high_residue + modulus_value - 1) // modulus_value
            wrap_high = (high_product - low_residue) // modulus_value

            for wrap_count in range(wrap_low, wrap_high + 1):
                low_number = wrap_count * modulus_value + low_residue
                high_number = wrap_count * modulus_value + high_residue
                refined_low = max(
                    low_secret, (low_number + multiplier - 1) // multiplier
                )
                refined_high = min(high_secret, high_number // multiplier)
                if refined_low <= refined_high:
                    next_ranges.append((refined_low, refined_high))

    next_ranges.sort()
    merged = []
    for low_secret, high_secret in next_ranges:
        if merged and low_secret <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], high_secret))
        else:
            merged.append((low_secret, high_secret))
    return merged


def solve(equations, radius, modulus_value):
    ranges = [(0, modulus_value - 1)]
    for multiplier, target_value in equations:
        ranges = refine(
            ranges, multiplier, target_value, radius, modulus_value
        )
        if not ranges:
            raise RuntimeError("all candidates were eliminated")

    total = sum(high_secret - low_secret + 1 for low_secret, high_secret in ranges)
    if total != 1:
        raise RuntimeError(f"expected one candidate, got {total}")
    return ranges[0][0]


def recover(values):
    modulus_value = values["modulus_value"]
    fog_limit = values["fog_limit"]
    pivot_symbol = values["pivot_symbol"]
    center_sample = values["center_sample"]

    shade_equations = []
    for power, forward_item, backward_item in zip(
        values["step_powers"], values["forward_samples"], values["backward_samples"]
    ):
        stride = 1 << power
        target_value = (forward_item + backward_item - 2 * center_sample) % modulus_value
        shade_equations.append((2 * stride * stride, target_value))

    shade_key = solve(shade_equations, 4 * fog_limit, modulus_value)

    bright_equations = []
    for power, forward_item, backward_item in zip(
        values["step_powers"], values["forward_samples"], values["backward_samples"]
    ):
        stride = 1 << power
        target_value = (
            forward_item
            - backward_item
            - 4 * pivot_symbol * stride * shade_key
        ) % modulus_value
        bright_equations.append((2 * stride, target_value))

    bright_key = solve(bright_equations, 2 * fog_limit, modulus_value)
    return bright_key, shade_key


def pack(value, modulus_value):
    width = (modulus_value.bit_length() + 7) // 8
    return value.to_bytes(width, "big")


def unseal(values, bright_key, shade_key):
    modulus_value = values["modulus_value"]
    material = (
        pack(bright_key, modulus_value)
        + pack(shade_key, modulus_value)
        + DOMAIN_TAG
    )
    stream_key = SHA256.new(material).digest()
    box = AES.new(stream_key, AES.MODE_GCM, nonce=bytes.fromhex(values["nonce"]))
    return box.decrypt_and_verify(
        bytes.fromhex(values["ciphertext"]),
        bytes.fromhex(values["tag"]),
    )


def main():
    values = parse()
    bright_key, shade_key = recover(values)
    flag = unseal(values, bright_key, shade_key)

    print(f"bright_key = {bright_key}")
    print(f"shade_key = {shade_key}")
    print(f"flag = {flag.decode()}")


if __name__ == "__main__":
    main()
