"""Tests for the versioned config store (in-memory + SQL parity)."""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from eip_persistence import (
    ConfigStore,
    InMemoryConfigStore,
    SqlConfigStore,
)

T1 = datetime(2024, 1, 1)
T2 = datetime(2024, 6, 1)
T3 = datetime(2024, 12, 1)


def _sql() -> SqlConfigStore:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    return SqlConfigStore(engine)


# Run every test against both implementations to guarantee parity.
@pytest.fixture(params=["memory", "sql"])
def store(request) -> ConfigStore:
    return InMemoryConfigStore() if request.param == "memory" else _sql()


def test_satisfies_protocol(store: ConfigStore):
    assert isinstance(store, ConfigStore)


def test_put_assigns_monotonic_versions_per_profile(store: ConfigStore):
    store.put("default", payload={"freshness": 0.10}, knowledge_time=T1)
    store.put("default", payload={"freshness": 0.05}, knowledge_time=T2)
    store.put("historical", payload={"freshness": 0.05}, knowledge_time=T2)
    assert [r.version for r in store.history("default")] == [1, 2]
    assert [r.version for r in store.history("historical")] == [1]


def test_active_is_latest_version(store: ConfigStore):
    store.put("default", payload={"a": 1}, knowledge_time=T1)
    store.put("default", payload={"a": 2}, knowledge_time=T2, actor="alice", note="tune")
    active = store.active("default")
    assert active is not None
    assert active.version == 2
    assert active.payload == {"a": 2}
    assert active.actor == "alice" and active.note == "tune"


def test_version_fetches_a_specific_version(store: ConfigStore):
    store.put("default", payload={"a": 1}, knowledge_time=T1)
    store.put("default", payload={"a": 2}, knowledge_time=T2)
    v1 = store.version("default", 1)
    assert v1 is not None and v1.payload == {"a": 1}
    assert store.version("default", 99) is None


def test_profiles_lists_known_namespaces(store: ConfigStore):
    store.put("historical", payload={"a": 1}, knowledge_time=T1)
    store.put("default", payload={"a": 1}, knowledge_time=T1)
    assert store.profiles() == ["default", "historical"]


def test_unknown_profile_is_empty(store: ConfigStore):
    assert store.active("nope") is None
    assert store.history("nope") == []
    assert store.profiles() == []
