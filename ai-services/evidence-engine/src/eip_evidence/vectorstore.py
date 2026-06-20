"""Vector-store seam (ADR-0006).

`VectorStore.search` returns candidate hits for a query vector. `QdrantVectorStore`
adapts the `qdrant-client`; tests use a fake store. The SDK is only touched in the
adapter and the `make_qdrant_store` factory, keeping the rest hermetic.

Each Qdrant point payload is expected to carry: source_id, source_tier, content,
and (optionally) freshness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class VectorHit:
    id: str
    source_id: str
    source_tier: int
    content: str
    score: float
    freshness: float = 0.5


@runtime_checkable
class VectorStore(Protocol):
    def search(self, vector: list[float], *, limit: int) -> list[VectorHit]: ...


class QdrantVectorStore:
    """Adapter over a Qdrant client. `client` is duck-typed to Qdrant's API
    (`query_points`) so this module stays import-light and hermetic."""

    def __init__(self, client: Any, collection: str) -> None:
        self._client = client
        self._collection = collection

    def search(self, vector: list[float], *, limit: int) -> list[VectorHit]:
        response = self._client.query_points(
            collection_name=self._collection, query=vector, limit=limit
        )
        hits: list[VectorHit] = []
        for point in response.points:
            payload = point.payload or {}
            hits.append(
                VectorHit(
                    id=str(point.id),
                    source_id=str(payload["source_id"]),
                    source_tier=int(payload["source_tier"]),
                    content=str(payload.get("content", "")),
                    score=float(point.score),
                    freshness=float(payload.get("freshness", 0.5)),
                )
            )
        return hits


def make_qdrant_store(url: str, collection: str) -> QdrantVectorStore:
    """Build a QdrantVectorStore against a running Qdrant (e.g. infra/docker-compose).
    Imports the SDK lazily so importing this module needs no live dependency."""
    from qdrant_client import QdrantClient

    return QdrantVectorStore(QdrantClient(url=url), collection)
