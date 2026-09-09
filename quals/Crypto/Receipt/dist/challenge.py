import os
import random

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Util.number import getPrime


SIZES = [48, 48, 48, 48, 48]
CONFETTI = 5 << 185
PLAYLIST = list(range(0, 192, 2))
STAMP = b"dual-shadow-ring-v1"


def feed(source):
    def take(amount):
        return bytes(source.randrange(0, 256) for _ in range(amount))

    return take


def ring(source):
    stage = 1
    stream = feed(source)
    for width in SIZES:
        stage *= getPrime(width, randfunc=stream)
    return stage


def drama(source):
    return source.randrange(-CONFETTI + 1, CONFETTI)


def pose(item, lamp, curtain, stage, source):
    result = item * lamp + item * item * curtain
    return (result + drama(source)) % stage


def pack(value, stage):
    width = (stage.bit_length() + 7) // 8
    return value.to_bytes(width, "big")


def seal(prize, lamp, curtain, stage, source):
    material = pack(lamp, stage) + pack(curtain, stage) + STAMP
    key = SHA256.new(material).digest()
    ticket = feed(source)(12)
    box = AES.new(key, AES.MODE_GCM, nonce=ticket)
    parcel, sticker = box.encrypt_and_digest(prize)
    return ticket, sticker, parcel


def transcript(prize):
    source = random.Random(int.from_bytes(os.urandom(24), "big"))
    stage = ring(source)
    lamp = source.randrange(1, stage)
    curtain = source.randrange(1, stage)
    lobby = stage // 2

    receipt = pose(lobby, lamp, curtain, stage, source)
    sunny = []
    rainy = []
    for power in PLAYLIST:
        stride = 1 << power
        sunny.append(
            pose(lobby + stride, lamp, curtain, stage, source)
        )
        rainy.append(
            pose(lobby - stride, lamp, curtain, stage, source)
        )

    ticket, sticker, parcel = seal(prize, lamp, curtain, stage, source)

    return {
        "karaoke": stage,
        "confetti": CONFETTI,
        "lobby": lobby,
        "playlist": PLAYLIST,
        "receipt": receipt,
        "sunny": sunny,
        "rainy": rainy,
        "ticket": ticket.hex(),
        "sticker": sticker.hex(),
        "parcel": parcel.hex(),
    }


def emit(label, value):
    if isinstance(value, int):
        print(f"{label} = {hex(value)}")
    else:
        print(f"{label} = {value!r}")


def main():
    prize = os.environ.get("FLAG", "HOLOGY9{redacted}").encode()
    for label, value in transcript(prize).items():
        emit(label, value)


if __name__ == "__main__":
    main()
