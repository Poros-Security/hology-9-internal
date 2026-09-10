import base64
import hashlib
import os
from nltk.parse.transitionparser import TransitionParser

# Author version: this is the real flag used to generate the transcript.
FLAG = b"REDACTED"  # original flag removed

# The original generator keeps this material outside the transcript.
VAULT_SEED = bytes([100,105,118,101,114,103,101,110,99,101,45,115,116,97,116,105,99,45,118,97,117,108,116,45,118,49])  # challenge material; not the flag

PICKLE_ARMED = False

def arm():
    global PICKLE_ARMED
    PICKLE_ARMED = True

def reveal_material():
    if not PICKLE_ARMED:
        raise RuntimeError("material is unavailable")
    print("DIVERGENCE_MATERIAL=" + base64.b64encode(VAULT_SEED).decode())

def derive_key():
    return hashlib.sha256(VAULT_SEED).digest()

def make_output():
    nonce = b"DIVERGENCE"
    stream = hashlib.sha256(derive_key() + nonce).digest()
    ciphertext = bytes(a ^ b for a, b in zip(FLAG, (stream * 4)[:len(FLAG)]))
    print("=== DIVERGENCE ===")
    print("nltk = 3.9.4")
    print("nonce = " + base64.b64encode(nonce).decode())
    print("ciphertext = " + base64.b64encode(ciphertext).decode())
    print("material = REDACTED")
    print("model = model.pkl")

def main():
    make_output()
    TransitionParser("arc-standard").parse([], "model.pkl")

if __name__ == "__main__":
    main()
