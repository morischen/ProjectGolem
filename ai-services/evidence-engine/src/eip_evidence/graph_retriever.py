"""Graph retriever — implements the `Retriever` protocol via a `GraphStore`.

Traverses the knowledge graph from the claim to connected evidence/sources and maps
hits to `Candidate`s (graph relevance → quality). Drop-in for `gather()`.
"""

from __future__ import annotations

from eip_evidence.graphstore import GraphStore
from eip_evidence.models import Candidate


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


class GraphRetriever:
    def __init__(self, store: GraphStore, *, limit: int = 10) -> None:
        self._store = store
        self._limit = limit

    def retrieve(self, claim_text: str) -> list[Candidate]:
        hits = self._store.query_candidates(claim_text, limit=self._limit)
        return [
            Candidate(
                id=hit.id,
                source_id=hit.source_id,
                source_tier=hit.source_tier,
                content=hit.content,
                quality=_clamp01(hit.relevance),
                freshness=_clamp01(hit.freshness),
            )
            for hit in hits
        ]
