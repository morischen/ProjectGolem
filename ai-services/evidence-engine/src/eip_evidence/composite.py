"""Composite retrieval: merge several retrievers, plus env-driven construction.

`CompositeRetriever` runs each backend and de-duplicates by candidate id (keeping the
highest-quality hit), so vector + graph results combine without double-counting.
`build_retriever_from_env` assembles the configured backends (Qdrant / Neo4j) from
environment variables — returning None when nothing is configured (the default in
tests/CI, where candidates are supplied in the request instead).
"""

from __future__ import annotations

import os

from eip_evidence.models import Candidate
from eip_evidence.retriever import Retriever


class CompositeRetriever:
    def __init__(self, retrievers: list[Retriever]) -> None:
        self._retrievers = list(retrievers)

    def retrieve(self, claim_text: str) -> list[Candidate]:
        best: dict[str, Candidate] = {}
        for retriever in self._retrievers:
            for candidate in retriever.retrieve(claim_text):
                existing = best.get(candidate.id)
                if existing is None or candidate.quality > existing.quality:
                    best[candidate.id] = candidate
        return sorted(best.values(), key=lambda c: c.quality, reverse=True)


def build_retriever_from_env() -> Retriever | None:
    """Compose retrievers from env. `QDRANT_URL` enables semantic search;
    `NEO4J_URI` enables graph retrieval. Returns None if neither is set."""
    retrievers: list[Retriever] = []

    qdrant_url = os.getenv("QDRANT_URL")
    if qdrant_url:
        from eip_evidence.embedding import HashingEmbedder
        from eip_evidence.semantic_retriever import SemanticRetriever
        from eip_evidence.vectorstore import make_qdrant_store

        # Real offline embedder (lexical, deterministic) until a hosted multilingual
        # model lands (ADR-0011). EMBED_DIM tunes the feature-hashing dimension.
        embedder = HashingEmbedder(dim=int(os.getenv("EMBED_DIM", "256")))
        vector_store = make_qdrant_store(qdrant_url, os.getenv("QDRANT_COLLECTION", "evidence"))
        retrievers.append(SemanticRetriever(embedder, vector_store))

    neo4j_uri = os.getenv("NEO4J_URI")
    if neo4j_uri:
        from eip_evidence.graph_retriever import GraphRetriever
        from eip_evidence.graphstore import make_neo4j_store

        graph_store = make_neo4j_store(
            neo4j_uri,
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", ""),
        )
        retrievers.append(GraphRetriever(graph_store))

    if not retrievers:
        return None
    if len(retrievers) == 1:
        return retrievers[0]
    return CompositeRetriever(retrievers)
