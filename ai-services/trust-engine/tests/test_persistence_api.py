"""Trust Engine API persists verdicts (append-only, versioned) and exposes history."""

from eip_persistence import InMemoryVerdictStore
from fastapi.testclient import TestClient

from eip_trust.api import create_app


def _supports(n: int) -> list[dict]:
    return [
        {
            "id": f"s{i}",
            "source_id": f"s{i}",
            "source_tier": 1,
            "relation": "supports",
            "quality": 1.0,
            "freshness": 1.0,
        }
        for i in range(n)
    ]


def _contradicts(n: int) -> list[dict]:
    return [{**e, "relation": "contradicts"} for e in _supports(n)]


def test_score_persists_when_claim_id_given():
    client = TestClient(create_app(InMemoryVerdictStore()))
    res = client.post("/v1/score", json={"claim_id": "c1", "evidence": _supports(3)})
    assert res.status_code == 200
    assert res.json()["verdict"] == "Verified"

    history = client.get("/v1/claims/c1/verdicts").json()
    assert len(history) == 1
    assert history[0]["version"] == 1
    assert history[0]["verdict"] == "Verified"
    assert history[0]["payload"]["score"] == res.json()["score"]


def test_repeated_scores_accrue_versions():
    client = TestClient(create_app(InMemoryVerdictStore()))
    client.post("/v1/score", json={"claim_id": "c1", "evidence": _supports(3)})
    client.post("/v1/score", json={"claim_id": "c1", "evidence": _contradicts(3)})

    history = client.get("/v1/claims/c1/verdicts").json()
    assert [h["version"] for h in history] == [1, 2]
    assert [h["verdict"] for h in history] == ["Verified", "False"]

    latest = client.get("/v1/claims/c1/verdict").json()
    assert latest["version"] == 2 and latest["verdict"] == "False"


def test_score_without_claim_id_does_not_persist():
    client = TestClient(create_app(InMemoryVerdictStore()))
    client.post("/v1/score", json={"evidence": _supports(3)})  # no claim_id
    assert client.get("/v1/claims/c1/verdicts").json() == []


def test_latest_404_when_absent():
    client = TestClient(create_app(InMemoryVerdictStore()))
    assert client.get("/v1/claims/none/verdict").status_code == 404


def test_no_store_returns_empty_history(monkeypatch):
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    client = TestClient(create_app())  # no store configured
    assert client.get("/v1/claims/x/verdicts").json() == []
