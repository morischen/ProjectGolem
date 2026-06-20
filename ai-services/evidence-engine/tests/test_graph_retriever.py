"""Hermetic tests for the graph retriever (fake graph store)."""

import json

from eip_evidence import GraphHit, GraphRetriever, Retriever, StubLLMClient, gather


class FakeGraphStore:
    def __init__(self, hits: list[GraphHit]) -> None:
        self._hits = hits
        self.last_limit: int | None = None

    def query_candidates(self, claim_text: str, *, limit: int) -> list[GraphHit]:
        self.last_limit = limit
        return list(self._hits)[:limit]


def test_maps_graph_hits_to_candidates():
    store = FakeGraphStore(
        [
            GraphHit(
                id="g1", source_id="s1", source_tier=1, content="c", freshness=0.7, relevance=0.9
            )
        ]
    )
    candidates = GraphRetriever(store, limit=5).retrieve("claim")
    assert len(candidates) == 1
    c = candidates[0]
    assert (c.id, c.source_id, c.source_tier, c.quality, c.freshness) == ("g1", "s1", 1, 0.9, 0.7)
    assert store.last_limit == 5


def test_graph_retriever_satisfies_retriever_protocol():
    assert isinstance(GraphRetriever(FakeGraphStore([])), Retriever)


def test_gather_works_with_graph_retriever():
    store = FakeGraphStore(
        [
            GraphHit(
                id="g1", source_id="s1", source_tier=1, content="c", freshness=0.7, relevance=0.9
            )
        ]
    )
    result = gather(
        "claim",
        retriever=GraphRetriever(store),
        llm=StubLLMClient(json.dumps({"relation": "contradicts"})),
    )
    assert result.evidence[0].relation.value == "contradicts"
