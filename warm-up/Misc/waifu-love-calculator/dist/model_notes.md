# Model notes

The backend uses a trained binary classifier, not a random formula.

The model takes four letters as input, encodes each letter using circular `sin/cos`
features, and produces a compatibility confidence. The challenge is to recover the
hidden perfect initials from model outputs.
