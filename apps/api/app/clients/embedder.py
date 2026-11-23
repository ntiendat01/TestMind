"""Embedding backends. Tests inject their own Embedder."""

from __future__ import annotations

import hashlib
import math
from typing import Any


class HashEmbedder:
    """Deterministic unit vectors. Not a semantic model."""

    model_name = "hash-1024"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_hash_vector(text) for text in texts]


class BgeM3Embedder:
    model_name = "BAAI/bge-m3"

    def __init__(self, model_name: str = "BAAI/bge-m3") -> None:
        self.model_name = model_name
        self._model: Any = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._load()
        vectors = model.encode(texts, normalize_embeddings=True)
        return [[float(value) for value in row] for row in vectors]

    def _load(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model


def _hash_vector(text: str) -> list[float]:
    values: list[float] = []
    seed = hashlib.sha256(text.encode()).digest()
    counter = 0
    while len(values) < 1024:
        block = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        for offset in range(0, len(block), 4):
            number = int.from_bytes(block[offset : offset + 4], "big")
            values.append(number / 2**32 * 2 - 1)
        counter += 1
    norm = math.sqrt(sum(value * value for value in values[:1024])) or 1.0
    return [value / norm for value in values[:1024]]
