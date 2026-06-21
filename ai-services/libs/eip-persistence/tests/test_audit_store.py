"""Tests for the append-only audit log (in-memory + SQL parity)."""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from eip_persistence import AuditStore, InMemoryAuditStore, SqlAuditStore

T1 = datetime(2024, 1, 1)
T2 = datetime(2024, 6, 1)
T3 = datetime(2024, 12, 1)


def _sql() -> SqlAuditStore:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    return SqlAuditStore(engine)


@pytest.fixture(params=["memory", "sql"])
def store(request) -> AuditStore:
    return InMemoryAuditStore() if request.param == "memory" else _sql()


def test_satisfies_protocol(store: AuditStore):
    assert isinstance(store, AuditStore)


def test_record_assigns_monotonic_ids(store: AuditStore):
    a = store.record(
        actor="alice", action="config.update", target="config:default", knowledge_time=T1
    )
    b = store.record(
        actor="bob", action="config.update", target="config:default", knowledge_time=T2
    )
    assert (a.id, b.id) == (1, 2)


def test_before_after_round_trip(store: AuditStore):
    rec = store.record(
        actor="alice",
        action="config.update",
        target="config:default",
        knowledge_time=T1,
        before={"freshness": 0.10},
        after={"freshness": 0.05},
    )
    assert rec.before == {"freshness": 0.10}
    assert rec.after == {"freshness": 0.05}
    fetched = store.list()[0]
    assert fetched.before == {"freshness": 0.10}
    assert fetched.after == {"freshness": 0.05}


def test_list_is_newest_first_and_paginates(store: AuditStore):
    for t in (T1, T2, T3):
        store.record(actor="a", action="x", target="t", knowledge_time=t)
    ids = [e.id for e in store.list()]
    assert ids == [3, 2, 1]
    page = store.list(limit=1, offset=1)
    assert [e.id for e in page] == [2]


def test_list_filters_by_target(store: AuditStore):
    store.record(actor="a", action="x", target="config:default", knowledge_time=T1)
    store.record(actor="a", action="x", target="config:historical", knowledge_time=T2)
    rows = store.list(target="config:historical")
    assert len(rows) == 1 and rows[0].target == "config:historical"


def test_empty_log_lists_nothing(store: AuditStore):
    assert store.list() == []
