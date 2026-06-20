"""Tests for the Claim Engine HTTP surface (in-process TestClient, stub LLM)."""

import json

from fastapi.testclient import TestClient

from eip_claim import StubLLMClient
from eip_claim.api import create_app

CLAIM_OUTPUT = json.dumps(
    {
        "text": "Country X attacked City Y.",
        "claim_type": "empirical",
        "actors": ["Country X"],
        "targets": ["City Y"],
    }
)


def _client(output: str = CLAIM_OUTPUT, *, raise_server_exceptions: bool = True) -> TestClient:
    return TestClient(
        create_app(StubLLMClient(output)),
        raise_server_exceptions=raise_server_exceptions,
    )


def test_health():
    res = _client().get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_extract_returns_normalized_claim():
    res = _client().post("/v1/extract", json={"text": "X attacked Y", "claim_id": "c1"})
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == "c1"
    assert body["claim_type"] == "empirical"
    assert body["actors"] == ["Country X"]


def test_extract_requires_text_and_claim_id():
    res = _client().post("/v1/extract", json={"text": "missing claim_id"})
    assert res.status_code == 422  # pydantic validation


def test_extract_bad_llm_output_is_server_error():
    client = _client("not json", raise_server_exceptions=False)
    res = client.post("/v1/extract", json={"text": "x", "claim_id": "c2"})
    assert res.status_code == 500
