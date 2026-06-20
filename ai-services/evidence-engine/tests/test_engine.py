"""Tests for evidence gathering with stub retriever + stub LLM."""

import json

import pytest

from eip_evidence import (
    Candidate,
    EvidenceRelation,
    StubLLMClient,
    StubRetriever,
    classify_candidate,
    gather,
)


def candidate(cid: str, tier: int = 1, quality: float = 0.9, freshness: float = 0.8) -> Candidate:
    return Candidate(
        id=cid,
        source_id=f"src-{cid}",
        source_tier=tier,
        content=f"content for {cid}",
        quality=quality,
        freshness=freshness,
    )


def rel(value: str) -> str:
    return json.dumps({"relation": value})


def test_classify_single_candidate():
    llm = StubLLMClient(rel("supports"))
    evidence, call = classify_candidate("claim", candidate("c1", tier=2), llm=llm)
    assert evidence.relation is EvidenceRelation.SUPPORTS
    assert evidence.source_tier == 2
    assert evidence.source_id == "src-c1"
    assert call.inputs == {"candidate_id": "c1", "source_id": "src-c1"}


def test_gather_classifies_each_candidate_in_order():
    retriever = StubRetriever([candidate("c1"), candidate("c2")])
    llm = StubLLMClient([rel("supports"), rel("contradicts")])
    result = gather("Some claim", retriever=retriever, llm=llm)

    assert [e.relation for e in result.evidence] == [
        EvidenceRelation.SUPPORTS,
        EvidenceRelation.CONTRADICTS,
    ]
    assert len(result.calls) == 2  # one recorded call per candidate (INV-REPRO)


def test_gather_carries_retrieval_metadata_not_from_llm():
    retriever = StubRetriever([candidate("c1", tier=3, quality=0.4, freshness=0.2)])
    result = gather("claim", retriever=retriever, llm=StubLLMClient(rel("neutral")))
    ev = result.evidence[0]
    assert (ev.source_tier, ev.quality, ev.freshness) == (3, 0.4, 0.2)


def test_empty_retrieval_yields_no_evidence():
    result = gather("claim", retriever=StubRetriever([]), llm=StubLLMClient(rel("supports")))
    assert result.evidence == []
    assert result.calls == []


def test_invalid_relation_raises():
    with pytest.raises(ValueError):
        classify_candidate("claim", candidate("c1"), llm=StubLLMClient(rel("bogus")))
