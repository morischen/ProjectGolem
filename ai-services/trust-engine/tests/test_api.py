"""Tests for the FastAPI HTTP surface (in-process via TestClient — no server)."""

from fastapi.testclient import TestClient

from eip_trust.api import app

client = TestClient(app)


def _support(eid: str, source: str, tier: int = 1) -> dict:
    return {
        "id": eid,
        "source_id": source,
        "source_tier": tier,
        "relation": "supports",
        "quality": 1.0,
        "freshness": 1.0,
    }


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_score_returns_verdict_and_breakdown():
    payload = {"evidence": [_support("e1", "s1"), _support("e2", "s2"), _support("e3", "s3")]}
    res = client.post("/v1/score", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["verdict"] == "Verified"
    assert 0.0 <= body["score"] <= 1.0
    assert set(body["breakdown"]) >= {"source_reliability", "weighted_total"}
    assert body["weights_version"]


def test_score_empty_is_insufficient():
    res = client.post("/v1/score", json={"evidence": []})
    assert res.status_code == 200
    assert res.json()["verdict"] == "Insufficient Evidence"


def test_score_historical_profile_used():
    payload = {
        "evidence": [_support("e1", "s1"), _support("e2", "s2"), _support("e3", "s3")],
        "historical": True,
    }
    res = client.post("/v1/score", json=payload)
    assert res.status_code == 200
    assert res.json()["weights_version"].endswith("historical")


def test_score_rejects_invalid_tier():
    bad = {"evidence": [{**_support("e1", "s1"), "source_tier": 9}]}
    res = client.post("/v1/score", json=bad)
    assert res.status_code == 422  # pydantic validation -> Unprocessable Entity
