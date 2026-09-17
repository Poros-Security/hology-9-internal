import base64
import hashlib
import os

from nltk.parse.transitionparser import TransitionParser
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


FLAG = os.environ.get(
    "FLAG",
    "HOLOGY9{REDACTED}"
).encode()


VAULT_SEED = bytes([
    100, 105, 118, 101, 114, 103, 101, 110, 99, 101,
    45, 115, 116, 97, 116, 105, 99, 45, 118, 97,
    117, 108, 116, 118, 49
])


PICKLE_ARMED = False


def arm():
    global PICKLE_ARMED
    PICKLE_ARMED = True


def reveal_material():
    if not PICKLE_ARMED:
        raise RuntimeError("material is unavailable")

    print(
        "DIVERGENCE_MATERIAL="
        + base64.b64encode(VAULT_SEED).decode()
    )


def _stage_one():
    return hashlib.sha256(
        VAULT_SEED + bytes.fromhex("91274413")
    ).digest()


def _stage_two():
    first = _stage_one()

    return hashlib.sha256(
        first + bytes.fromhex("6319A702")
    ).digest()


def _stage_three():
    first = _stage_one()
    second = _stage_two()

    return hashlib.sha256(
        second[5:27]
        + first[11:29]
        + bytes.fromhex("D1A7")
    ).digest()


def _derive_key():
    first = _stage_one()
    second = _stage_two()
    third = _stage_three()

    material = (
        third[3:29]
        + second[7:23]
        + first[13:19]
    )

    return hashlib.sha256(material).digest()


def _derive_iv():
    first = _stage_one()
    second = _stage_two()
    third = _stage_three()

    material = (
        first[4:16]
        + third[18:26]
        + second[0:4]
    )

    return hashlib.sha256(material).digest()[:16]


def _encrypt():
    key = _derive_key()
    iv = _derive_iv()

    cipher = AES.new(
        key,
        AES.MODE_CBC,
        iv
    )

    return cipher.encrypt(
        pad(
            FLAG,
            AES.block_size
        )
    )


def make_output():
    ciphertext = _encrypt()

    print("=== DIVERGENCE ===")
    print("nltk = 3.9.4")
    print(
        "ciphertext = "
        + base64.b64encode(ciphertext).decode()
    )
    print("material = REDACTED")
    print("model = model.pkl")


def main():
    make_output()

    TransitionParser(
        "arc-standard"
    ).parse(
        [],
        "model.pkl"
    )


if __name__ == "__main__":
    main()