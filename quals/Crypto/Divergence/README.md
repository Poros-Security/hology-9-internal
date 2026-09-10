# Divergence

**CVE:** CVE-2026-78683

NLTK versions before 3.10.0 contain an unsafe pickle deserialization path
in `TransitionParser.parse()`. The challenge intentionally uses the affected
3.9.x behavior.

## Intended solve

1. Inspect `Divergence.py`.
2. Notice that `TransitionParser.parse()` loads the supplied model.
3. Recognize that the model is a pickle artifact.
4. Build a pickle payload that invokes `__main__.reveal_key`.
5. Run the target with the crafted model.
6. Recover the per-run AES-GCM key.
7. Decrypt the ciphertext printed by the target.

The provided `model.pkl` is benign; the participant must create the malicious
model themselves.

The challenge is static: no remote service is required.
