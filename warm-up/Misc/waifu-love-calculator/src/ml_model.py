from __future__ import annotations

import hashlib
import json
import math
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np

ALPHABET = string.ascii_uppercase
ALPHABET_SIZE = len(ALPHABET)
FEATURES_PER_POSITION = 2
NUM_POSITIONS = 4
NUM_FEATURES = NUM_POSITIONS * FEATURES_PER_POSITION
POSITION_WEIGHTS = np.array([1.10, 1.25, 1.45, 1.70], dtype=np.float64)
MODEL_VERSION = "waifu-logreg-circular-v2"


class ModelError(RuntimeError):
    pass


def _letter_to_index(ch: str) -> int:
    return ALPHABET.index(ch.upper())


def _target_hash(target: str) -> str:
    return hashlib.sha256((MODEL_VERSION + ":" + target).encode()).hexdigest()


def _angles(indices: np.ndarray) -> np.ndarray:
    return 2.0 * math.pi * indices.astype(np.float64) / ALPHABET_SIZE


def encode_indices(codes: np.ndarray) -> np.ndarray:
    angles = _angles(codes)
    features = np.empty((codes.shape[0], NUM_FEATURES), dtype=np.float64)
    features[:, 0::2] = np.sin(angles)
    features[:, 1::2] = np.cos(angles)
    return features


def encode_pair(person_a: str, person_b: str) -> np.ndarray:
    pair = (person_a + person_b).upper()
    if len(pair) != NUM_POSITIONS or any(ch not in ALPHABET for ch in pair):
        raise ModelError("pair must contain exactly four A-Z letters")
    codes = np.array([[_letter_to_index(ch) for ch in pair]], dtype=np.int16)
    return encode_indices(codes)


def all_candidate_codes() -> np.ndarray:
    grids = np.meshgrid(
        np.arange(ALPHABET_SIZE, dtype=np.int16),
        np.arange(ALPHABET_SIZE, dtype=np.int16),
        np.arange(ALPHABET_SIZE, dtype=np.int16),
        np.arange(ALPHABET_SIZE, dtype=np.int16),
        indexing="ij",
    )
    return np.stack(grids, axis=-1).reshape(-1, NUM_POSITIONS)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -60.0, 60.0)))


def _private_teacher_logits(codes: np.ndarray, target: str) -> np.ndarray:
    target_codes = np.array([_letter_to_index(ch) for ch in target], dtype=np.int16)
    delta = _angles(codes - target_codes)
    centered_similarity = (np.cos(delta) * POSITION_WEIGHTS).sum(axis=1)
    return -1.35 + 1.65 * centered_similarity


def train(target: str, *, epochs: int = 850, learning_rate: float = 0.95, l2: float = 1e-5) -> Tuple[np.ndarray, float, dict]:
    target = target.upper()
    if len(target) != NUM_POSITIONS or any(ch not in ALPHABET for ch in target):
        raise ModelError("target must be exactly four A-Z letters")

    codes = all_candidate_codes()
    x = encode_indices(codes)
    teacher_logits = _private_teacher_logits(codes, target)
    y = _sigmoid(teacher_logits)

    w = np.zeros(NUM_FEATURES, dtype=np.float64)
    b = float(np.log(y.mean() / (1.0 - y.mean())))
    n = x.shape[0]

    last_loss = None
    for _ in range(epochs):
        logits = x @ w + b
        p = _sigmoid(logits)
        error = p - y
        grad_w = (x.T @ error) / n + l2 * w
        grad_b = float(error.mean())
        w -= learning_rate * grad_w
        b -= learning_rate * grad_b
        learning_rate *= 0.998
        last_loss = float((-(y * np.log(p + 1e-12) + (1.0 - y) * np.log(1.0 - p + 1e-12))).mean())

    metadata = {
        "model_version": MODEL_VERSION,
        "target_hash": _target_hash(target),
        "epochs": epochs,
        "training_examples": int(n),
        "features": "sin/cos circular embedding of four initials",
        "loss": last_loss,
    }
    params = np.concatenate([w, np.array([b], dtype=np.float64)])
    return params, last_loss or 0.0, metadata


@dataclass(frozen=True)
class WaifuLoveModel:
    weights: np.ndarray
    bias: float
    metadata: dict

    def logit(self, person_a: str, person_b: str) -> float:
        x = encode_pair(person_a, person_b)
        return float(x @ self.weights + self.bias)

    def probability(self, person_a: str, person_b: str) -> float:
        return float(_sigmoid(np.array([self.logit(person_a, person_b)], dtype=np.float64))[0])


def save_model(path: Path, params: np.ndarray, metadata: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, params=params, metadata=json.dumps(metadata, sort_keys=True))


def load_model(path: Path) -> WaifuLoveModel:
    data = np.load(path, allow_pickle=False)
    params = data["params"].astype(np.float64)
    metadata = json.loads(str(data["metadata"]))
    if params.shape != (NUM_FEATURES + 1,):
        raise ModelError(f"bad model shape: {params.shape}")
    return WaifuLoveModel(weights=params[:-1], bias=float(params[-1]), metadata=metadata)


def ensure_model(path: Path, target: str) -> WaifuLoveModel:
    expected_hash = _target_hash(target.upper())
    try:
        model = load_model(path)
        if model.metadata.get("model_version") == MODEL_VERSION and model.metadata.get("target_hash") == expected_hash:
            return model
    except Exception:
        pass

    params, _loss, metadata = train(target.upper())
    save_model(path, params, metadata)
    return load_model(path)


def candidate_from_indices(indices: Iterable[int]) -> str:
    return "".join(ALPHABET[int(i)] for i in indices)
