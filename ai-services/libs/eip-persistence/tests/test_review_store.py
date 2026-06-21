"""Tests for the human-review queue store (in-memory + SQL parity)."""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from eip_persistence import InMemoryReviewStore, ReviewStore, SqlReviewStore

T1 = datetime(2024, 1, 1)
T2 = datetime(2024, 6, 1)
T3 = datetime(2024, 12, 1)


def _sql() -> SqlReviewStore:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    return SqlReviewStore(engine)


@pytest.fixture(params=["memory", "sql"])
def store(request) -> ReviewStore:
    return InMemoryReviewStore() if request.param == "memory" else _sql()


def test_satisfies_protocol(store: ReviewStore):
    assert isinstance(store, ReviewStore)


def test_open_assigns_monotonic_ids_and_open_status(store: ReviewStore):
    a = store.open_item("c1", kind="low_confidence", created_time=T1, detail={"score": 0.4})
    b = store.open_item("c2", kind="appeal", created_time=T2)
    assert (a.id, b.id) == (1, 2)
    assert a.status == "open" and a.resolution is None
    assert a.detail == {"score": 0.4}


def test_get_returns_the_item(store: ReviewStore):
    item = store.open_item("c1", kind="appeal", created_time=T1)
    assert store.get(item.id) is not None
    assert store.get(999) is None


def test_list_is_newest_first_and_filters_by_status(store: ReviewStore):
    a = store.open_item("c1", kind="low_confidence", created_time=T1)
    store.open_item("c2", kind="appeal", created_time=T2)
    store.resolve(a.id, resolution={"reviewer": "alice", "decision": "upheld"}, resolved_time=T3)

    assert [r.id for r in store.list()] == [2, 1]
    assert [r.id for r in store.list(status="open")] == [2]
    assert [r.id for r in store.list(status="resolved")] == [1]


def test_resolve_sets_status_resolution_and_time(store: ReviewStore):
    item = store.open_item("c1", kind="evidence_conflict", created_time=T1)
    resolved = store.resolve(
        item.id,
        resolution={"reviewer": "alice", "decision": "override", "override_verdict": "False"},
        resolved_time=T2,
    )
    assert resolved is not None
    assert resolved.status == "resolved"
    assert resolved.resolved_time == T2
    assert resolved.resolution["decision"] == "override"
    # The change persists on subsequent reads.
    assert store.get(item.id).status == "resolved"


def test_resolve_unknown_item_returns_none(store: ReviewStore):
    assert store.resolve(999, resolution={"x": 1}, resolved_time=T1) is None


def test_empty_queue_lists_nothing(store: ReviewStore):
    assert store.list() == []
