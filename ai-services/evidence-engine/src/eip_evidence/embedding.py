"""Embedding seam (ADR-0006, ADR-0011).

`Embedder` turns text into a vector for semantic search. Two dependency-free,
deterministic implementations ship here so retrieval works fully offline:

- `StubEmbedder` — stable but NOT semantically meaningful; for wiring tests only.
- `HashingEmbedder` — a real (if simple) lexical embedder: a hashed bag-of-words
  with term-frequency weighting, L2-normalized. Texts that share words land closer
  in cosine space, so retrieval ranks by genuine lexical overlap without any external
  model or network. A hosted multilingual model (ADR-0011) implements the same
  protocol later; pin + record its id when it lands (INV-REPRO).

Language-agnostic tokenization (Unicode word characters) keeps it usable for the
Arabic/Hebrew/English domain (ADR-0012).
"""

from __future__ import annotations

import hashlib
import re
from typing import Protocol, runtime_checkable

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


@runtime_checkable
class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class StubEmbedder:
    def __init__(self, dim: int = 8) -> None:
        self._dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for i, ch in enumerate(text):
            vec[i % self._dim] += (ord(ch) % 17) / 17.0
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class HashingEmbedder:
    """Deterministic hashed bag-of-words embedder (the feature-hashing trick).

    Each token is hashed to a bucket in `[0, dim)` and contributes its term frequency
    (with a sign hash to reduce collisions cancelling signal). The vector is
    L2-normalized so dot product == cosine similarity. No training, no network, no
    randomness — same text always yields the same vector (INV-REPRO).
    """

    def __init__(self, dim: int = 256) -> None:
        if dim <= 0:
            raise ValueError("dim must be positive")
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def _bucket(self, token: str) -> tuple[int, float]:
        digest = hashlib.sha1(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % self._dim
        sign = 1.0 if digest[4] & 1 else -1.0
        return index, sign

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for token in _tokenize(text):
            index, sign = self._bucket(token)
            vec[index] += sign
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]
