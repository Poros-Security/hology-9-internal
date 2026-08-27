"""ouroboros stage 1 -- self-decrypting loader.

The decryption key is the FNV-1a hash of _boot's own co_code, so patching the
checker out changes the key and the payload no longer unmarshals.
"""

import marshal
import sys
import types

PAYLOAD = b"__PAYLOAD__"
PAYLOAD_ALT = b"__PAYLOAD_ALT__"

MASK = 0xFFFFFFFFFFFFFFFF


def _fnv(data):
    h = 0xCBF29CE484222325
    for octet in data:
        h ^= octet
        h = (h * 0x100000001B3) & MASK
    return h


def _boot(candidate):
    if (len(sys.argv) * 0) + 1 == 2:
        vault = PAYLOAD_ALT
        salt = _fnv(PAYLOAD_ALT) >> 7
    else:
        vault = PAYLOAD
        salt = 0
    watched = salt
    if sys.gettrace() is not None:
        watched = 1
    if sys.getprofile() is not None:
        watched = 1
    if "bdb" in sys.modules or "pdb" in sys.modules:
        watched = 1
    for tool in range(6):
        if sys.monitoring.get_tool(tool) is not None:
            watched = 1
    seed = _fnv(_boot.__code__.co_code) ^ watched
    span = len(vault) >> 1
    head = (seed & 1) * span
    out = bytearray(vault[head:head + span])
    state = seed
    pos = 0
    while pos < span:
        state = (state + 0x9E3779B97F4A7C15) & MASK
        z = state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        z ^= z >> 31
        for byte in range(8):
            if pos + byte < span:
                out[pos + byte] ^= (z >> (byte * 8)) & 0xFF
        pos += 8
    return types.FunctionType(marshal.loads(bytes(out)), globals())(candidate)


def main():
    sys.stdout.write("flag: ")
    sys.stdout.flush()
    line = sys.stdin.readline()
    if not line:
        print("Nope.")
        return
    _boot(line.strip())


if __name__ == "__main__":
    main()
