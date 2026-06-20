"""Tests for the Evidence Engine HTTP surface (in-process TestClient, stub LLM)."""

import json

from fastapi.testclient import TestClient

from eip_evidence import StubLLMClient
from eip_evidence.api import create_app

CANDIDATE = {
    "id": "c1",
    "source_id": "s1",
    "source_tier": 1,
    "content": "Source text about the claim.",
    "quality": 0.9,
    "freshness": 0.8,
}


def _client(outputs: list[str] | str) -> TestClient:
    return TestClient(create_app(StubLLMClient(outputs)))


def test_health():
    res = _client(json.dumps({"relation": "supports"})).get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_gather_classifies_candidates():
    client = _client([json.dumps({"relation": "supports"})])
    res = client.post("/v1/gather", json={"claim_text": "a claim", "candidates": [CANDIDATE]})
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["relation"] == "supports"
    assert body[0]["source_tier"] == 1


def test_gather_empty_candidates_returns_empty():
    client = _client(json.dumps({"relation": "supports"}))
    res = client.post("/v1/gather", json={"claim_text": "a claim", "candidates": []})
    assert res.status_code == 200
    assert res.json() == []


def test_gather_requires_claim_text():
    client = _client(json.dumps({"relation": "supports"}))
    res = client.post("/v1/gather", json={"candidates": [CANDIDATE]})
    assert res.status_code == 422


def test_gather_uses_configured_retriever_when_no_candidates():
    from eip_evidence import Candidate, StubRetriever
    from eip_evidence.api import create_app

    retriever = StubRetriever(
        [Candidate(id="r1", source_id="s9", source_tier=1, content="from retriever")]
    )
    client = TestClient(create_app(StubLLMClient(json.dumps({"relation": "supports"})), retriever))
    res = client.post("/v1/gather", json={"claim_text": "a claim"})  # no candidates
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["id"] == "r1"
    assert body[0]["relation"] == "supports"
