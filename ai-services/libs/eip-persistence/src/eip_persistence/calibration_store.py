"""Calibration ledger store (ADR-0008; blueprint §28.12).

Append-only history of calibration/benchmark runs, so verdict accuracy and
calibration error can be tracked over time and regressions caught. Timestamps are
caller-supplied (INV-REPRO). In-memory + SQL adapters, like the other stores.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Engine,
    Float,
    Integer,
    MetaData,
    Table,
    func,
    insert,
    select,
)

from eip_persistence.models import CalibrationRunRecord


@runtime_checkable
class CalibrationStore(Protocol):
    def record(
        self,
        *,
        recorded_time: datetime,
        total: int,
        verdict_accuracy: float,
        calibration_error: float,
        payload: dict[str, Any] | None = None,
    ) -> CalibrationRunRecord: ...

    def list(self, *, limit: int = 100, offset: int = 0) -> list[CalibrationRunRecord]: ...

    def latest(self) -> CalibrationRunRecord | None: ...


class InMemoryCalibrationStore:
    def __init__(self) -> None:
        self._runs: list[CalibrationRunRecord] = []

    def record(
        self,
        *,
        recorded_time: datetime,
        total: int,
        verdict_accuracy: float,
        calibration_error: float,
        payload: dict[str, Any] | None = None,
    ) -> CalibrationRunRecord:
        run = CalibrationRunRecord(
            id=len(self._runs) + 1,
            recorded_time=recorded_time,
            total=total,
            verdict_accuracy=verdict_accuracy,
            calibration_error=calibration_error,
            payload=dict(payload or {}),
        )
        self._runs.append(run)
        return run

    def list(self, *, limit: int = 100, offset: int = 0) -> list[CalibrationRunRecord]:
        ordered = sorted(self._runs, key=lambda r: r.id, reverse=True)  # newest first
        return ordered[offset : offset + limit]

    def latest(self) -> CalibrationRunRecord | None:
        return max(self._runs, key=lambda r: r.id) if self._runs else None


_metadata = MetaData()

calibration_runs = Table(
    "calibration_runs",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("recorded_time", DateTime, nullable=False),
    Column("total", Integer, nullable=False),
    Column("verdict_accuracy", Float, nullable=False),
    Column("calibration_error", Float, nullable=False),
    Column("payload", JSON, nullable=False, default=dict),
)


def _to_record(row: Any) -> CalibrationRunRecord:
    return CalibrationRunRecord(
        id=int(row["id"]),
        recorded_time=row["recorded_time"],
        total=int(row["total"]),
        verdict_accuracy=float(row["verdict_accuracy"]),
        calibration_error=float(row["calibration_error"]),
        payload=dict(row["payload"] or {}),
    )


class SqlCalibrationStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        _metadata.create_all(engine)

    def record(
        self,
        *,
        recorded_time: datetime,
        total: int,
        verdict_accuracy: float,
        calibration_error: float,
        payload: dict[str, Any] | None = None,
    ) -> CalibrationRunRecord:
        data = dict(payload or {})
        with self._engine.begin() as conn:
            current_max = conn.execute(select(func.max(calibration_runs.c.id))).scalar()
            new_id = int(current_max or 0) + 1
            conn.execute(
                insert(calibration_runs).values(
                    id=new_id,
                    recorded_time=recorded_time,
                    total=total,
                    verdict_accuracy=verdict_accuracy,
                    calibration_error=calibration_error,
                    payload=data,
                )
            )
        return CalibrationRunRecord(
            id=new_id,
            recorded_time=recorded_time,
            total=total,
            verdict_accuracy=verdict_accuracy,
            calibration_error=calibration_error,
            payload=data,
        )

    def list(self, *, limit: int = 100, offset: int = 0) -> list[CalibrationRunRecord]:
        stmt = (
            select(calibration_runs)
            .order_by(calibration_runs.c.id.desc())
            .limit(limit)
            .offset(offset)
        )
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [_to_record(row) for row in rows]

    def latest(self) -> CalibrationRunRecord | None:
        stmt = select(calibration_runs).order_by(calibration_runs.c.id.desc()).limit(1)
        with self._engine.connect() as conn:
            row = conn.execute(stmt).mappings().first()
        return _to_record(row) if row is not None else None
