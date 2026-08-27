import sys

KEY = b"t04st3d"
TARGET = b"__TARGET__"


def toast(candidate):
    out = []
    for i, ch in enumerate(candidate):
        x = ord(ch)
        x ^= KEY[i % len(KEY)]
        x = ((x << 3) | (x >> 5)) & 0xFF
        x = (x + i * 7) & 0xFF
        out.append(x)
    return bytes(out)


def main(argv):
    if len(argv) != 2:
        print("usage: python marshmallow.pyc <flag>")
        return 1
    candidate = argv[1]
    if len(candidate) != len(TARGET):
        print("Nope.")
        return 1
    if toast(candidate) == TARGET:
        print("Correct!")
        return 0
    print("Nope.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
