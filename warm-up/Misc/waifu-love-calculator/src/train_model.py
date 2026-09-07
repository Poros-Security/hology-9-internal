#!/usr/bin/env python3
"""Train the Waifu Love Calculator model.

Examples:
    SECRET_A=WA SECRET_B=FU python train_model.py
    SECRET_A=AB SECRET_B=CD python train_model.py --output model/waifu_model.npz
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from ml_model import save_model, train


def clean_initials(value: str, fallback: str) -> str:
    value = (value or "").strip().upper()
    return value if re.fullmatch(r"[A-Z]{2}", value) else fallback


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the Waifu Love Calculator ML model")
    parser.add_argument("--output", default="model/waifu_model.npz", help="path to write .npz model artifact")
    parser.add_argument("--epochs", type=int, default=850, help="full-batch gradient descent epochs")
    args = parser.parse_args()

    secret_a = clean_initials(os.environ.get("SECRET_A", "WA"), "WA")
    secret_b = clean_initials(os.environ.get("SECRET_B", "FU"), "FU")
    target = secret_a + secret_b
    params, loss, metadata = train(target, epochs=args.epochs)
    save_model(Path(args.output), params, metadata)
    print(f"trained {metadata['model_version']} on {metadata['training_examples']} examples")
    print(f"final loss: {loss:.8f}")
    print(f"wrote: {args.output}")


if __name__ == "__main__":
    main()
