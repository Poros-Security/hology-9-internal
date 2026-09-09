from pathlib import Path
import ast

from Crypto.Cipher import AES
from Crypto.Hash import SHA256


STAMP = b"dual-shadow-ring-v1"


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


def centered(value, stage):
    value %= stage
    if value > stage // 2:
        value -= stage
    return value


def windows(center_value, radius, stage):
    center_value %= stage
    low = center_value - radius
    high = center_value + radius
    if low < 0:
        return [(0, high), (stage + low, stage - 1)]
    if high >= stage:
        return [(low, stage - 1), (0, high - stage)]
    return [(low, high)]


def refine(ranges, multiplier, target_value, radius, stage):
    next_ranges = []

    for low_secret, high_secret in ranges:
        low_product = multiplier * low_secret
        high_product = multiplier * high_secret

        for low_residue, high_residue in windows(
            target_value, radius, stage
        ):
            wrap_low = (low_product - high_residue + stage - 1) // stage
            wrap_high = (high_product - low_residue) // stage

            for wrap_count in range(wrap_low, wrap_high + 1):
                low_number = wrap_count * stage + low_residue
                high_number = wrap_count * stage + high_residue
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


def solve(equations, radius, stage):
    ranges = [(0, stage - 1)]
    for multiplier, target_value in equations:
        ranges = refine(
            ranges, multiplier, target_value, radius, stage
        )
        if not ranges:
            raise RuntimeError("all candidates were eliminated")

    total = sum(high_secret - low_secret + 1 for low_secret, high_secret in ranges)
    if total != 1:
        raise RuntimeError(f"expected one candidate, got {total}")
    return ranges[0][0]


def recover(values):
    stage = values["karaoke"]
    confetti = values["confetti"]
    lobby = values["lobby"]
    receipt = values["receipt"]

    curtain_rows = []
    for power, sunny_item, rainy_item in zip(
        values["playlist"], values["sunny"], values["rainy"]
    ):
        stride = 1 << power
        target_value = (sunny_item + rainy_item - 2 * receipt) % stage
        curtain_rows.append((2 * stride * stride, target_value))

    curtain = solve(curtain_rows, 4 * confetti, stage)

    lamp_rows = []
    for power, sunny_item, rainy_item in zip(
        values["playlist"], values["sunny"], values["rainy"]
    ):
        stride = 1 << power
        target_value = (
            sunny_item
            - rainy_item
            - 4 * lobby * stride * curtain
        ) % stage
        lamp_rows.append((2 * stride, target_value))

    lamp = solve(lamp_rows, 2 * confetti, stage)
    return lamp, curtain


def pack(value, stage):
    width = (stage.bit_length() + 7) // 8
    return value.to_bytes(width, "big")


def unseal(values, lamp, curtain):
    stage = values["karaoke"]
    material = pack(lamp, stage) + pack(curtain, stage) + STAMP
    key = SHA256.new(material).digest()
    box = AES.new(key, AES.MODE_GCM, nonce=bytes.fromhex(values["ticket"]))
    return box.decrypt_and_verify(
        bytes.fromhex(values["parcel"]),
        bytes.fromhex(values["sticker"]),
    )


def main():
    values = parse()
    lamp, curtain = recover(values)
    flag = unseal(values, lamp, curtain)

    print(f"lamp = {lamp}")
    print(f"curtain = {curtain}")
    print(f"flag = {flag.decode()}")


if __name__ == "__main__":
    main()
