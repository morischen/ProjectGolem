"""Trust Engine metrics endpoint: benchmark + queue health + claims count (A4)."""

from eip_persistence import (
    InMemoryAuditStore,
    InMemoryConfigStore,
    InMemoryReviewStore,
    InMemoryVerdictStore,
)
from fastapi.testclient import TestClient

from eip_trust.api import create_app


def _client() -> TestClient:
    return TestClient(
        create_app(
            InMemoryVerdictStore(),
            config_store=InMemoryConfigStore(),
            audit_store=InMemoryAuditStore(),
            review_store=InMemoryReviewStore(),
        )
    )


def _mixed() -> list[dict]:
    base = {"source_tier": 1, "quality": 1.0, "freshness": 1.0}
    return [
        {"id": "s0", "source_id": "s0", "relation": "supports", **base},
        {"id": "s1", "source_id": "s1", "relation": "supports", **base},
        {"id": "c0", "source_id": "c0", "relation": "contradicts", **base},
        {"id": "c1", "source_id": "c1", "relation": "contradicts", **base},
    ]


def test_metrics_reports_benchmark_accuracy():
    res = _client().get("/v1/metrics")
    assert res.status_code == 200
    bench = res.json()["benchmark"]
    # The seed set is golden: the engine reproduces every labeled verdict.
    assert bench is not None
    assert bench["verdict_accuracy"] == 1.0
    assert bench["total"] >= 1
    assert "calibration_error" in bench


def test_metrics_reflects_queue_and_claims():
    client = _client()
    # Score a conflicted claim -> 1 verdict + 1 open review item.
    client.post("/v1/score", json={"claim_id": "c1", "evidence": _mixed()})

    body = client.get("/v1/metrics").json()
    assert body["claims_count"] == 1
    assert body["queue"]["open"] == 1
    assert body["queue"]["by_kind"]["evidence_conflict"] == 1
    assert body["queue"]["resolved"] == 0


def test_metrics_queue_counts_resolved():
    client = _client()
    client.post("/v1/score", json={"claim_id": "c1", "evidence": _mixed()})
    item_id = client.get("/v1/review").json()[0]["id"]
    client.post(
        f"/v1/review/{item_id}/resolve",
        json={"reviewer": "alice", "decision": "dismissed"},
    )
    queue = client.get("/v1/metrics").json()["queue"]
    assert queue["open"] == 0 and queue["resolved"] == 1
