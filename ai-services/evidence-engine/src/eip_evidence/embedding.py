"""Embedding seam (ADR-0006).

`Embedder` turns claim text into a vector for semantic search. `StubEmbedder` is
deterministic and dependency-free for tests/offline use — it is NOT semantically
meaningful, it just produces stable vectors so retrieval wiring is testable. A real
embedding model implements the same protocol later.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


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
