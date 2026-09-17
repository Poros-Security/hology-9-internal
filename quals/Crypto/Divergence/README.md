# Divergence

**CVE:** CVE-2026-78683

NLTK versions before 3.10.0 contain an unsafe pickle deserialization path in `TransitionParser.parse()`. The challenge intentionally uses the affected 3.9.x behavior.

## Intended solve

1. Inspect `Divergence.py`.
2. Notice that `TransitionParser.parse()` loads the supplied model.
3. Recognize that the model is a pickle artifact.
4. Build a pickle payload that invokes `__main__.arm()` and `__main__.reveal_material()`.
5. Run the target with the crafted model.
6. Recover the hidden material printed by the target.
7. Reverse the staged derivation used to obtain the encryption key and IV.
8. Decrypt the ciphertext printed by the target.
9. Recover the flag.

The provided `model.pkl` is benign; the participant must create the malicious model themselves.

The challenge is static: no remote service is required.

## Files

```text
Divergence/
├── README.md
├── challenge.yml
├── dist/
│   ├── Divergence.py
│   ├── model.pkl
│   └── output.txt
├── solver/
│   ├── requirements.txt
│   └── solve.py
└── src/
    └── Divergence.py
```

## Notes

The ciphertext is generated using a key and IV derived through multiple SHA-256 stages from the recovered material.

The derivation is intentionally split across several stages, so recovering the material alone is not sufficient to immediately obtain the flag.

No remote interaction is required.
