"""SQL adapter parity tests — run real SQL against in-memory SQLite (no Docker)."""

from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from eip_persistence import SqlVerdictStore, VerdictStore

T1 = datetime(2024, 1, 1)
T2 = datetime(2024, 6, 1)
T3 = datetime(2024, 12, 1)


def _store() -> SqlVerdictStore:
    # StaticPool keeps one in-memory SQLite DB across connections.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    return SqlVerdictStore(engine)


def _seeded() -> SqlVerdictStore:
    store = _store()
    store.append("c1", verdict="Verified", score=0.9, weights_version="v0", knowledge_time=T1)
    store.append("c1", verdict="Mixed Evidence", score=0.5, weights_version="v0", knowledge_time=T2)
    store.append("c1", verdict="Likely False", score=0.3, weights_version="v0", knowledge_time=T3)
    return store


def test_satisfies_protocol():
    assert isinstance(_store(), VerdictStore)


def test_versions_history_and_latest():
    store = _seeded()
    assert [r.version for r in store.history("c1")] == [1, 2, 3]
    latest = store.latest("c1")
    assert latest is not None and latest.verdict == "Likely False"


def test_as_of_round_trips_through_sql():
    store = _seeded()
    assert store.as_of("c1", datetime(2024, 3, 1)).verdict == "Verified"
    assert store.as_of("c1", datetime(2024, 8, 1)).verdict == "Mixed Evidence"
    assert store.as_of("c1", datetime(2023, 1, 1)) is None


def test_event_time_and_payload_persist():
    store = _store()
    store.append(
        "c2",
        verdict="Verified",
        score=0.92,
        weights_version="v0",
        knowledge_time=T1,
        event_time=datetime(1948, 5, 14),
        payload={"net_support": 1.0},
    )
    rec = store.latest("c2")
    assert rec is not None
    assert rec.event_time == datetime(1948, 5, 14)
    assert rec.payload == {"net_support": 1.0}


def test_list_claims_latest_per_claim():
    store = _seeded()  # c1 @ T1<T2<T3 (3 versions)
    store.append("c2", verdict="Verified", score=0.9, weights_version="v0", knowledge_time=T2)
    claims = store.list_claims()
    assert {(c.claim_id, c.version) for c in claims} == {("c1", 3), ("c2", 1)}
    # newest knowledge_time first: c1 (T3) before c2 (T2)
    assert [c.claim_id for c in claims] == ["c1", "c2"]


def test_unknown_claim_is_empty():
    store = _store()
    assert store.latest("nope") is None
    assert store.history("nope") == []
