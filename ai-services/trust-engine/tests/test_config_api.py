"""Trust Engine config endpoints: versioned, audited, sum-to-1 enforced (A2)."""

from eip_persistence import InMemoryAuditStore, InMemoryConfigStore
from fastapi.testclient import TestClient

from eip_trust.api import create_app


def _client() -> TestClient:
    return TestClient(
        create_app(config_store=InMemoryConfigStore(), audit_store=InMemoryAuditStore())
    )


def _valid_weights(**overrides: float) -> dict:
    body = {
        "profile": "default",
        "actor": "alice",
        "note": "tune freshness",
        "source_reliability": 0.30,
        "corroboration": 0.25,
        "evidence_quality": 0.20,
        "independence": 0.15,
        "freshness": 0.10,
        "tier_reliability": {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.35},
        "strength_floor": 0.30,
        "mixed_conflict_threshold": 0.35,
        "verified_threshold": 0.80,
    }
    body.update(overrides)
    return body


def test_get_config_returns_seeded_profiles():
    res = _client().get("/v1/config")
    assert res.status_code == 200
    profiles = {p["profile"]: p for p in res.json()["profiles"]}
    assert set(profiles) == {"default", "historical"}
    assert profiles["default"]["active"]["version"] == 1
    assert profiles["default"]["versions"] == [1]


def test_post_config_creates_new_version_and_audits():
    client = _client()
    # New version: shift weight from freshness to source_reliability (still sums to 1).
    res = client.post("/v1/config", json=_valid_weights(source_reliability=0.35, freshness=0.05))
    assert res.status_code == 200
    record = res.json()
    assert record["version"] == 2  # seed was v1
    assert record["actor"] == "alice"
    assert record["payload"]["version"] == "default.v2"  # traceable label

    # Active is now v2.
    active = {p["profile"]: p for p in client.get("/v1/config").json()["profiles"]}
    assert active["default"]["active"]["version"] == 2

    # Audit entry recorded with before/after.
    audit = client.get("/v1/audit").json()
    assert len(audit) == 1
    assert audit[0]["action"] == "config.update"
    assert audit[0]["target"] == "config:default"
    assert audit[0]["before"]["freshness"] == 0.10
    assert audit[0]["after"]["freshness"] == 0.05


def test_post_config_rejects_weights_not_summing_to_one():
    client = _client()
    res = client.post("/v1/config", json=_valid_weights(freshness=0.50))  # sum > 1
    assert res.status_code == 422
    # No new version, no audit on rejection.
    assert client.get("/v1/config").json()["profiles"][0]["active"]["version"] == 1
    assert client.get("/v1/audit").json() == []


def test_post_config_requires_an_actor():
    client = _client()
    body = _valid_weights()
    del body["actor"]
    assert client.post("/v1/config", json=body).status_code == 422


def test_post_audit_records_a_gateway_action():
    client = _client()
    res = client.post(
        "/v1/audit",
        json={
            "actor": "admin",
            "action": "key.create",
            "target": "key:abc",
            "after": {"label": "ci"},
        },
    )
    assert res.status_code == 200
    assert res.json()["action"] == "key.create"
    entries = client.get("/v1/audit", params={"target": "key:abc"}).json()
    assert len(entries) == 1 and entries[0]["actor"] == "admin"


def test_config_history_lists_versions_oldest_first():
    client = _client()
    client.post("/v1/config", json=_valid_weights(source_reliability=0.35, freshness=0.05))
    history = client.get("/v1/config/default/history").json()
    assert [h["version"] for h in history] == [1, 2]


def test_score_uses_the_active_config_version():
    client = _client()
    evidence = [
        {
            "id": "e1",
            "source_id": "s1",
            "source_tier": 1,
            "relation": "supports",
            "quality": 1.0,
            "freshness": 1.0,
        }
    ]
    first = client.post("/v1/score", json={"evidence": evidence}).json()
    assert first["weights_version"] == "2026-06-19.v0"  # seeded default profile

    client.post("/v1/config", json=_valid_weights(source_reliability=0.35, freshness=0.05))
    second = client.post("/v1/score", json={"evidence": evidence}).json()
    assert second["weights_version"] == "default.v2"  # picks up the new active version
