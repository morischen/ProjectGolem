"""Trust Engine review queue & appeals: escalation, override, audit (A3)."""

from eip_persistence import (
    InMemoryAuditStore,
    InMemoryConfigStore,
    InMemoryReviewStore,
    InMemoryVerdictStore,
)
from fastapi.testclient import TestClient

from eip_trust.api import create_app


def _app() -> tuple[TestClient, InMemoryAuditStore]:
    audit = InMemoryAuditStore()
    client = TestClient(
        create_app(
            InMemoryVerdictStore(),
            config_store=InMemoryConfigStore(),
            audit_store=audit,
            review_store=InMemoryReviewStore(),
        )
    )
    return client, audit


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


def _mixed() -> list[dict]:
    # Equal support/contradiction -> Mixed Evidence -> evidence_conflict review.
    supports = _supports(2)
    contradicts = [
        {**e, "id": f"c{i}", "source_id": f"c{i}", "relation": "contradicts"}
        for i, e in enumerate(_supports(2))
    ]
    return supports + contradicts


def test_high_confidence_verdict_does_not_enqueue():
    client, _ = _app()
    client.post("/v1/score", json={"claim_id": "c1", "evidence": _supports(4)})
    assert client.get("/v1/review").json() == []


def test_mixed_evidence_enqueues_a_conflict_item():
    client, _ = _app()
    client.post("/v1/score", json={"claim_id": "c1", "evidence": _mixed()})
    queue = client.get("/v1/review").json()
    assert len(queue) == 1
    assert queue[0]["kind"] == "evidence_conflict"
    assert queue[0]["status"] == "open"
    assert queue[0]["claim_id"] == "c1"


def test_low_confidence_enqueues_and_dedupes_per_claim():
    client, _ = _app()
    # No directional evidence -> Insufficient (score 0) -> low_confidence.
    body = {"claim_id": "c1", "evidence": []}
    client.post("/v1/score", json=body)
    client.post("/v1/score", json=body)  # re-score: must not add a second open item
    queue = client.get("/v1/review", params={"status": "open"}).json()
    assert len(queue) == 1
    assert queue[0]["kind"] == "low_confidence"


def test_get_review_item_404_when_missing():
    client, _ = _app()
    assert client.get("/v1/review/999").status_code == 404


def test_resolve_override_appends_attributed_verdict_and_audits():
    client, audit = _app()
    client.post("/v1/score", json={"claim_id": "c1", "evidence": _mixed()})
    item_id = client.get("/v1/review").json()[0]["id"]

    res = client.post(
        f"/v1/review/{item_id}/resolve",
        json={
            "reviewer": "alice",
            "decision": "override",
            "override_verdict": "False",
            "note": "sources fail independence",
        },
    )
    assert res.status_code == 200
    resolved = res.json()
    assert resolved["status"] == "resolved"
    assert resolved["resolution"]["decision"] == "override"

    # A NEW verdict version was appended, attributed to the human (INV-OVERRIDE).
    latest = client.get("/v1/claims/c1/verdict").json()
    assert latest["verdict"] == "False"
    assert latest["weights_version"] == "human-override"
    assert latest["payload"]["reviewer"] == "alice"
    history = client.get("/v1/claims/c1/verdicts").json()
    assert [h["version"] for h in history] == [1, 2]  # original + override

    # The resolution is audited.
    entries = [e for e in audit.list() if e.action == "review.resolve"]
    assert len(entries) == 1 and entries[0].actor == "alice"


def test_resolve_upheld_does_not_append_a_verdict():
    client, _ = _app()
    client.post("/v1/score", json={"claim_id": "c1", "evidence": _mixed()})
    item_id = client.get("/v1/review").json()[0]["id"]
    client.post(
        f"/v1/review/{item_id}/resolve",
        json={"reviewer": "bob", "decision": "upheld"},
    )
    history = client.get("/v1/claims/c1/verdicts").json()
    assert len(history) == 1  # unchanged


def test_resolve_twice_conflicts():
    client, _ = _app()
    client.post("/v1/score", json={"claim_id": "c1", "evidence": _mixed()})
    item_id = client.get("/v1/review").json()[0]["id"]
    body = {"reviewer": "alice", "decision": "dismissed"}
    assert client.post(f"/v1/review/{item_id}/resolve", json=body).status_code == 200
    assert client.post(f"/v1/review/{item_id}/resolve", json=body).status_code == 409


def test_override_without_valid_verdict_is_422():
    client, _ = _app()
    client.post("/v1/score", json={"claim_id": "c1", "evidence": _mixed()})
    item_id = client.get("/v1/review").json()[0]["id"]
    res = client.post(
        f"/v1/review/{item_id}/resolve",
        json={"reviewer": "alice", "decision": "override", "override_verdict": "Bogus"},
    )
    assert res.status_code == 422


def test_appeal_submit_creates_queue_item_and_is_logged():
    client, audit = _app()
    res = client.post(
        "/v1/appeals",
        json={
            "claim_id": "c1",
            "appeal_type": "new_evidence",
            "body": "new declassified document",
            "submitter": "jane",
        },
    )
    assert res.status_code == 200
    item = res.json()
    assert item["kind"] == "appeal"
    assert item["detail"]["appeal_type"] == "new_evidence"

    assert [a["id"] for a in client.get("/v1/appeals").json()] == [item["id"]]
    assert any(e.action == "appeal.submit" for e in audit.list())


def test_claim_intake_queues_a_triage_item_and_logs():
    client, audit = _app()
    res = client.post(
        "/v1/claim-intake",
        json={"text": "Country Z shelled a hospital on 2024-03-01.", "submitter": "jo"},
    )
    assert res.status_code == 200
    item = res.json()
    assert item["kind"] == "claim_intake"
    assert item["detail"]["text"].startswith("Country Z")
    # Shows up in the open review queue and is audited.
    queue = client.get("/v1/review", params={"status": "open"}).json()
    assert any(i["kind"] == "claim_intake" for i in queue)
    assert any(e.action == "claim.intake" for e in audit.list())


def test_claim_intake_requires_text():
    client, _ = _app()
    assert client.post("/v1/claim-intake", json={"submitter": "jo"}).status_code == 422


def test_appeal_invalid_type_is_422():
    client, _ = _app()
    res = client.post(
        "/v1/appeals",
        json={"claim_id": "c1", "appeal_type": "nonsense", "body": "x"},
    )
    assert res.status_code == 422
