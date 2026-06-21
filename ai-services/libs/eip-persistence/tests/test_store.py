"""Tests for the bitemporal in-memory verdict store."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from eip_persistence import InMemoryVerdictStore, VerdictRecord, VerdictStore

T1 = datetime(2024, 1, 1)
T2 = datetime(2024, 6, 1)
T3 = datetime(2024, 12, 1)


def _store() -> InMemoryVerdictStore:
    store = InMemoryVerdictStore()
    store.append("c1", verdict="Verified", score=0.9, weights_version="v0", knowledge_time=T1)
    store.append("c1", verdict="Mixed Evidence", score=0.5, weights_version="v0", knowledge_time=T2)
    store.append("c1", verdict="Likely False", score=0.3, weights_version="v0", knowledge_time=T3)
    return store


def test_satisfies_protocol():
    assert isinstance(InMemoryVerdictStore(), VerdictStore)


def test_append_assigns_monotonic_versions():
    store = _store()
    versions = [r.version for r in store.history("c1")]
    assert versions == [1, 2, 3]


def test_latest_is_most_recent_version():
    latest = _store().latest("c1")
    assert latest is not None
    assert latest.version == 3
    assert latest.verdict == "Likely False"


def test_history_is_full_and_ordered():
    history = _store().history("c1")
    assert [r.verdict for r in history] == ["Verified", "Mixed Evidence", "Likely False"]


def test_as_of_returns_version_current_at_that_time():
    store = _store()
    # New evidence overturns prior conclusions (Principle 5 / INV-TEMPORAL).
    assert store.as_of("c1", datetime(2024, 3, 1)).verdict == "Verified"  # between T1 and T2
    assert store.as_of("c1", datetime(2024, 8, 1)).verdict == "Mixed Evidence"  # between T2 and T3
    assert store.as_of("c1", T3).verdict == "Likely False"
    assert store.as_of("c1", datetime(2023, 1, 1)) is None  # before any assessment


def test_list_claims_returns_latest_per_claim_newest_first():
    store = _store()  # claim c1 with 3 versions @ T1<T2<T3
    store.append("c2", verdict="Verified", score=0.9, weights_version="v0", knowledge_time=T2)
    claims = store.list_claims()
    # one row per claim, latest version, newest knowledge_time first
    assert [(c.claim_id, c.version) for c in claims] == [("c1", 3), ("c2", 1)]


def test_list_claims_paginates():
    store = InMemoryVerdictStore()
    for i, t in enumerate((T1, T2, T3)):
        store.append(f"c{i}", verdict="Verified", score=0.9, weights_version="v0", knowledge_time=t)
    page = store.list_claims(limit=1, offset=1)
    assert len(page) == 1
    assert page[0].claim_id == "c1"  # second-newest (T2)


def test_unknown_claim_is_empty():
    store = InMemoryVerdictStore()
    assert store.latest("nope") is None
    assert store.history("nope") == []
    assert store.as_of("nope", T1) is None


def test_records_are_immutable():
    record = _store().latest("c1")
    assert isinstance(record, VerdictRecord)
    with pytest.raises(ValidationError):
        record.verdict = "Verified"  # frozen model


def test_event_time_and_payload_round_trip():
    store = InMemoryVerdictStore()
    rec = store.append(
        "c2",
        verdict="Verified",
        score=0.92,
        weights_version="v0",
        knowledge_time=T1,
        event_time=datetime(1948, 5, 14),
        payload={"net_support": 1.0},
    )
    assert rec.event_time == datetime(1948, 5, 14)
    assert rec.payload == {"net_support": 1.0}
