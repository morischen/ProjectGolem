"""Tests for the composite retriever and env-driven construction."""

from eip_evidence import (
    Candidate,
    CompositeRetriever,
    Retriever,
    StubRetriever,
    build_retriever_from_env,
)


def cand(cid: str, quality: float) -> Candidate:
    return Candidate(id=cid, source_id=f"s-{cid}", source_tier=1, content="c", quality=quality)


def test_merges_and_dedupes_keeping_highest_quality():
    a = StubRetriever([cand("x", 0.4), cand("y", 0.9)])
    b = StubRetriever([cand("x", 0.7), cand("z", 0.5)])  # "x" appears in both
    result = CompositeRetriever([a, b]).retrieve("claim")

    by_id = {c.id: c for c in result}
    assert set(by_id) == {"x", "y", "z"}
    assert by_id["x"].quality == 0.7  # higher of the two "x" hits
    # sorted by quality descending
    assert [c.id for c in result] == ["y", "x", "z"]


def test_composite_satisfies_retriever_protocol():
    assert isinstance(CompositeRetriever([]), Retriever)


def test_build_from_env_returns_none_when_unconfigured(monkeypatch):
    for var in ("QDRANT_URL", "NEO4J_URI"):
        monkeypatch.delenv(var, raising=False)
    assert build_retriever_from_env() is None
