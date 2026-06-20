"""Semantic (vector) retriever — implements the `Retriever` protocol.

Embeds the claim, searches the vector store, and maps hits to `Candidate`s. The
similarity score becomes the candidate's `quality` signal (clamped to [0, 1]).
Drop-in for `gather()` anywhere a `Retriever` is accepted.
"""

from __future__ import annotations

from eip_evidence.embedding import Embedder
from eip_evidence.models import Candidate
from eip_evidence.vectorstore import VectorStore


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


class SemanticRetriever:
    def __init__(self, embedder: Embedder, store: VectorStore, *, limit: int = 10) -> None:
        self._embedder = embedder
        self._store = store
        self._limit = limit

    def retrieve(self, claim_text: str) -> list[Candidate]:
        vector = self._embedder.embed(claim_text)
        hits = self._store.search(vector, limit=self._limit)
        return [
            Candidate(
                id=hit.id,
                source_id=hit.source_id,
                source_tier=hit.source_tier,
                content=hit.content,
                quality=_clamp01(hit.score),
                freshness=_clamp01(hit.freshness),
            )
            for hit in hits
        ]
