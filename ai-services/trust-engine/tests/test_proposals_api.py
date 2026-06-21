"""Multi-approver change control for scoring config (governance, §20)."""

from eip_persistence import InMemoryAuditStore, InMemoryConfigStore
from fastapi.testclient import TestClient

from eip_trust.api import create_app


def _client(monkeypatch, required: int = 2) -> TestClient:
    monkeypatch.setenv("CONFIG_REQUIRED_APPROVALS", str(required))
    return TestClient(
        create_app(config_store=InMemoryConfigStore(), audit_store=InMemoryAuditStore())
    )


def _proposal_body(**overrides):
    body = {
        "profile": "default",
        "actor": "proposer",
        "note": "shift weight to source reliability",
        "source_reliability": 0.35,
        "corroboration": 0.25,
        "evidence_quality": 0.20,
        "independence": 0.15,
        "freshness": 0.05,
        "tier_reliability": {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.35},
        "strength_floor": 0.30,
        "mixed_conflict_threshold": 0.35,
        "verified_threshold": 0.80,
    }
    body.update(overrides)
    return body


def test_proposal_requires_two_distinct_approvers_then_applies(monkeypatch):
    client = _client(monkeypatch, required=2)
    pid = client.post("/v1/config/proposals", json=_proposal_body()).json()["id"]

    # One approval is not enough.
    r1 = client.post(f"/v1/config/proposals/{pid}/approve", json={"approver": "alice"})
    assert r1.status_code == 200 and r1.json()["status"] == "pending"
    # Active config unchanged (still seed v1).
    assert client.get("/v1/config").json()["profiles"][0]["active"]["version"] == 1

    # Second distinct approval applies it.
    r2 = client.post(f"/v1/config/proposals/{pid}/approve", json={"approver": "bob"})
    assert r2.json()["status"] == "approved"
    active = client.get("/v1/config").json()["profiles"][0]["active"]
    assert active["version"] == 2
    assert active["payload"]["source_reliability"] == 0.35


def test_proposer_cannot_approve_own_change(monkeypatch):
    client = _client(monkeypatch, required=2)
    pid = client.post("/v1/config/proposals", json=_proposal_body()).json()["id"]
    res = client.post(f"/v1/config/proposals/{pid}/approve", json={"approver": "proposer"})
    assert res.status_code == 409


def test_duplicate_approver_rejected(monkeypatch):
    client = _client(monkeypatch, required=2)
    pid = client.post("/v1/config/proposals", json=_proposal_body()).json()["id"]
    client.post(f"/v1/config/proposals/{pid}/approve", json={"approver": "alice"})
    dup = client.post(f"/v1/config/proposals/{pid}/approve", json={"approver": "alice"})
    assert dup.status_code == 409


def test_invalid_weights_rejected_at_proposal_time(monkeypatch):
    client = _client(monkeypatch, required=2)
    res = client.post("/v1/config/proposals", json=_proposal_body(freshness=0.5))
    assert res.status_code == 422


def test_approving_unknown_proposal_404(monkeypatch):
    client = _client(monkeypatch, required=2)
    res = client.post("/v1/config/proposals/999/approve", json={"approver": "alice"})
    assert res.status_code == 404


def test_single_approval_threshold_applies_immediately(monkeypatch):
    client = _client(monkeypatch, required=1)
    pid = client.post("/v1/config/proposals", json=_proposal_body()).json()["id"]
    res = client.post(f"/v1/config/proposals/{pid}/approve", json={"approver": "alice"})
    assert res.json()["status"] == "approved"
