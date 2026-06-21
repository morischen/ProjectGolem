"""Tests for the calibration ledger store (in-memory + SQL parity)."""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from eip_persistence import (
    CalibrationStore,
    InMemoryCalibrationStore,
    SqlCalibrationStore,
)

T1 = datetime(2024, 1, 1)
T2 = datetime(2024, 6, 1)
T3 = datetime(2024, 12, 1)


def _sql() -> SqlCalibrationStore:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    return SqlCalibrationStore(engine)


@pytest.fixture(params=["memory", "sql"])
def store(request) -> CalibrationStore:
    return InMemoryCalibrationStore() if request.param == "memory" else _sql()


def test_satisfies_protocol(store: CalibrationStore):
    assert isinstance(store, CalibrationStore)


def test_record_assigns_ids_and_round_trips(store: CalibrationStore):
    run = store.record(
        recorded_time=T1,
        total=9,
        verdict_accuracy=1.0,
        calibration_error=0.2,
        payload={"by_difficulty": {"hard": 1.0}},
    )
    assert run.id == 1
    assert run.verdict_accuracy == 1.0
    assert run.payload["by_difficulty"] == {"hard": 1.0}


def test_list_is_newest_first_and_latest(store: CalibrationStore):
    store.record(recorded_time=T1, total=9, verdict_accuracy=0.8, calibration_error=0.3)
    store.record(recorded_time=T2, total=9, verdict_accuracy=0.9, calibration_error=0.2)
    store.record(recorded_time=T3, total=9, verdict_accuracy=1.0, calibration_error=0.1)
    assert [r.id for r in store.list()] == [3, 2, 1]
    latest = store.latest()
    assert latest is not None and latest.verdict_accuracy == 1.0


def test_list_paginates(store: CalibrationStore):
    for t in (T1, T2, T3):
        store.record(recorded_time=t, total=1, verdict_accuracy=1.0, calibration_error=0.0)
    page = store.list(limit=1, offset=1)
    assert [r.id for r in page] == [2]


def test_empty_ledger(store: CalibrationStore):
    assert store.list() == []
    assert store.latest() is None
