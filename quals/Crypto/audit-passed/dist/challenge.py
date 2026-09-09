import os
import random

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Util.number import getPrime


LIMB_WIDTHS = [48, 48, 48, 48, 48]
FOG_LIMIT = 5 << 185
STEP_POWERS = list(range(0, 192, 2))
DOMAIN_TAG = b"dual-shadow-ring-v1"


def feed(source):
    def take(amount):
        return bytes(source.randrange(0, 256) for _ in range(amount))

    return take


def ring(source):
    modulus_value = 1
    byte_source = feed(source)
    for width in LIMB_WIDTHS:
        modulus_value *= getPrime(width, randfunc=byte_source)
    return modulus_value


def blur(source):
    return source.randrange(-FOG_LIMIT + 1, FOG_LIMIT)


def project(symbol, bright_key, shade_key, modulus_value, source):
    clean_value = symbol * bright_key + symbol * symbol * shade_key
    return (clean_value + blur(source)) % modulus_value


def pack(value, modulus_value):
    width = (modulus_value.bit_length() + 7) // 8
    return value.to_bytes(width, "big")


def seal(secret_text, bright_key, shade_key, modulus_value, source):
    material = (
        pack(bright_key, modulus_value)
        + pack(shade_key, modulus_value)
        + DOMAIN_TAG
    )
    stream_key = SHA256.new(material).digest()
    nonce = feed(source)(12)
    box = AES.new(stream_key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = box.encrypt_and_digest(secret_text)
    return nonce, tag, ciphertext


def transcript(secret_text):
    source = random.Random(int.from_bytes(os.urandom(24), "big"))
    modulus_value = ring(source)
    bright_key = source.randrange(1, modulus_value)
    shade_key = source.randrange(1, modulus_value)
    pivot_symbol = modulus_value // 2

    center_sample = project(
        pivot_symbol, bright_key, shade_key, modulus_value, source
    )
    forward_samples = []
    backward_samples = []
    for power in STEP_POWERS:
        stride = 1 << power
        forward_samples.append(
            project(
                pivot_symbol + stride,
                bright_key,
                shade_key,
                modulus_value,
                source,
            )
        )
        backward_samples.append(
            project(
                pivot_symbol - stride,
                bright_key,
                shade_key,
                modulus_value,
                source,
            )
        )

    nonce, tag, ciphertext = seal(
        secret_text, bright_key, shade_key, modulus_value, source
    )

    return {
        "modulus_value": modulus_value,
        "fog_limit": FOG_LIMIT,
        "pivot_symbol": pivot_symbol,
        "step_powers": STEP_POWERS,
        "center_sample": center_sample,
        "forward_samples": forward_samples,
        "backward_samples": backward_samples,
        "nonce": nonce.hex(),
        "tag": tag.hex(),
        "ciphertext": ciphertext.hex(),
    }


def emit(label, value):
    if isinstance(value, int):
        print(f"{label} = {hex(value)}")
    else:
        print(f"{label} = {value!r}")


def main():
    secret_text = os.environ.get("FLAG", "HOLOGY9{redacted}").encode()
    for label, value in transcript(secret_text).items():
        emit(label, value)


if __name__ == "__main__":
    main()
