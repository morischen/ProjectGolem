"""Hermetic tests for the semantic retriever (fake vector store, stub embedder)."""

import json

from eip_evidence import (
    Retriever,
    SemanticRetriever,
    StubEmbedder,
    StubLLMClient,
    VectorHit,
    gather,
)


class FakeVectorStore:
    """In-memory VectorStore for tests — returns preset hits, records the limit."""

    def __init__(self, hits: list[VectorHit]) -> None:
        self._hits = hits
        self.last_limit: int | None = None
        self.last_vector: list[float] | None = None

    def search(self, vector: list[float], *, limit: int) -> list[VectorHit]:
        self.last_limit = limit
        self.last_vector = vector
        return list(self._hits)[:limit]


def test_maps_hits_to_candidates_and_passes_limit():
    store = FakeVectorStore(
        [VectorHit(id="h1", source_id="s1", source_tier=1, content="c1", score=0.9, freshness=0.8)]
    )
    retriever = SemanticRetriever(StubEmbedder(), store, limit=5)
    candidates = retriever.retrieve("some claim")

    assert len(candidates) == 1
    c = candidates[0]
    assert (c.id, c.source_id, c.source_tier, c.quality, c.freshness) == ("h1", "s1", 1, 0.9, 0.8)
    assert store.last_limit == 5
    assert store.last_vector is not None  # the claim was embedded and passed through


def test_scores_clamped_to_unit_interval():
    store = FakeVectorStore(
        [VectorHit(id="h1", source_id="s1", source_tier=1, content="c", score=1.4, freshness=-0.2)]
    )
    candidate = SemanticRetriever(StubEmbedder(), store).retrieve("x")[0]
    assert candidate.quality == 1.0
    assert candidate.freshness == 0.0


def test_embedder_is_deterministic():
    embedder = StubEmbedder()
    assert embedder.embed("hello") == embedder.embed("hello")


def test_semantic_retriever_satisfies_retriever_protocol():
    retriever = SemanticRetriever(StubEmbedder(), FakeVectorStore([]))
    assert isinstance(retriever, Retriever)  # drop-in for gather()


def test_gather_works_with_semantic_retriever():
    store = FakeVectorStore(
        [VectorHit(id="h1", source_id="s1", source_tier=1, content="c", score=0.9, freshness=0.8)]
    )
    result = gather(
        "a claim",
        retriever=SemanticRetriever(StubEmbedder(), store),
        llm=StubLLMClient(json.dumps({"relation": "supports"})),
    )
    assert len(result.evidence) == 1
    assert result.evidence[0].relation.value == "supports"
